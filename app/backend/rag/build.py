import os, re, json, argparse, uuid, hashlib
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
from tqdm import tqdm
import numpy as np
import fitz  # PyMuPDF
from PIL import Image
from ollama import Client
import pytesseract  # add near other imports
# If needed on Windows, uncomment and set the path:
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

from tools import clean_text, chunk_text


vehicle = "daf-lf45-lf55"

#File paths
ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT / "data" / vehicle / "documentation"
STORAGE_DIR = ROOT / "app" / "backend" / "rag" / "store"
EMBED_MODEL = "nomic-embed-text"



NAMESPACE_RULES = {
    "diagnostics": ["diagnostic", "troubleshoot", "dtc", "fault", "wiring"],
    "maintenance": ["maintenance", "service", "repair", "torque", "procedure"],
}

SYSTEM_KEYWORDS = {
    "engine": ["engine", "coolant", "euro", "emissions"],
    "brakes": ["brake", "abs", "braking"],
    "fuel": ["fuel", "injector", "pump"],
    "electrical": ["electrical", "wiring", "relay", "fuse"],
    "cab": ["cab", "body"],
    "gearbox": ["gearbox", "transmission"],
    "clutch": ["clutch"],
    "steering": ["steering"],
    "suspension": ["suspension"],
    "rear_axle": ["rear axle", "axle", "differential"],
}


def guess_namespace(name: str, title: str) -> str:
    s = (name + " " + title).lower()
    for ns, kws in NAMESPACE_RULES.items():
        if any(k in s for k in kws):
            return ns
    return "shared"

def guess_systems(context: str) -> List[str]:
    s = context.lower()
    hits = [sys for sys, kws in SYSTEM_KEYWORDS.items() if any(k in s for k in kws)]
    return sorted(set(hits))

def sha1_bytes(b: bytes) -> str:
    return hashlib.sha1(b).hexdigest()

def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)

# ---------------- TOC and blocks ----------------

def get_toc(doc: fitz.Document) -> List[Tuple[int, str, int]]:
    """
    Returns list of (level, title, page_index) from TOC.
    """
    try:
        toc = doc.get_toc(simple=False) or []
    except Exception:
        toc = doc.get_toc() or []
    out = []
    for item in toc:
        # PyMuPDF TOC can be [level, title, page] or dicts
        if isinstance(item, list) and len(item) >= 3:
            out.append((item[0], item[1], max(0, item[2]-1)))
        elif isinstance(item, dict):
            out.append((item.get("level", 1), item.get("title", ""), max(0, item.get("page", 1)-1)))
    return out

def section_ranges_from_toc(toc: List[Tuple[int, str, int]], page_count: int) -> List[Dict[str, Any]]:
    """
    Build contiguous sections with page ranges based on level-1 and level-2 headings.
    """
    if not toc:
        return [{"title": "Document", "level": 1, "start": 0, "end": page_count-1, "path": ["Document"]}]
    # Keep up to level 2
    filtered = [t for t in toc if t[0] in (1, 2)]
    sections = []
    for i, (lvl, title, pidx) in enumerate(filtered):
        start = pidx
        end = (filtered[i+1][2] - 1) if i+1 < len(filtered) else (page_count - 1)
        path = []
        if lvl == 1:
            path = [title]
        else:
            # find nearest previous level 1
            j = i-1
            prev = ""
            while j >= 0:
                if filtered[j][0] == 1:
                    prev = filtered[j][1]
                    break
                j -= 1
            path = [prev, title] if prev else [title]
        sections.append({"title": title, "level": lvl, "start": max(0, start), "end": max(0, end), "path": path})
    return sections

def page_blocks_with_images(page: fitz.Page) -> Dict[str, Any]:
    raw = page.get_text("rawdict")
    text_blocks = []
    xref_bbox = {}

    for b in raw.get("blocks", []):
        btype = b.get("type", 0)
        bbox = b.get("bbox", [0,0,0,0])
        if btype == 0:
            text = ""
            for line in b.get("lines", []):
                for span in line.get("spans", []):
                    text += span.get("text", "")
                text += "\n"
            text_blocks.append({"bbox": bbox, "text": clean_text(text)})
        elif btype == 1:
            xref = b.get("image")
            if xref is not None:
                try:
                    xref_bbox[int(xref)] = bbox
                except Exception:
                    pass

    images = []
    try:
        for info in page.get_images(full=True):
            xref = int(info[0])
            images.append({"xref": xref, "bbox": xref_bbox.get(xref)})
    except Exception:
        pass

    return {"text_blocks": text_blocks, "images": images}

def nearest_caption_for_image(img_bbox, text_blocks):
    if not img_bbox:
        for tb in text_blocks:
            if tb.get("text", "").strip():
                return tb["text"].strip().split("\n")[0][:300]
        return ""
    x0,y0,x1,y1 = img_bbox
    img_cy = 0.5*(y0+y1)
    best, best_d = None, 1e9
    for tb in text_blocks:
        t0,t1,t2,t3 = tb["bbox"]
        cy = 0.5*(t1+t3)
        d = abs(cy - img_cy)
        if d < best_d and tb["text"].strip():
            best, best_d = tb, d
    return (best["text"].strip() if best else "").split("\n")[0][:300]

def ocr_page_text(page: fitz.Page) -> str:
    pix = page.get_pixmap(dpi=200)
    mode = "RGB" if pix.n in (3,4) else "L"
    img = Image.frombytes(mode, [pix.width, pix.height], pix.samples)
    if img.mode != "RGB":
        img = img.convert("RGB")
    try:
        return clean_text(pytesseract.image_to_string(img))
    except Exception:
        return ""

# ---------------- Builder ----------------

def build_index(data_dir: Path, store_dir: Path, use_llm_tags: bool = False) -> None:
    ensure_dir(store_dir)
    images_dir = store_dir / "images"
    ensure_dir(images_dir)

    meta_fp = open(store_dir / "meta.jsonl", "w", encoding="utf-8")
    vectors: List[List[float]] = []
    client = Client(host="http://localhost:11434")

    pdfs = sorted([p for p in data_dir.iterdir() if p.suffix.lower() == ".pdf"])
    for pdf in tqdm(pdfs, desc="Indexing PDFs"):
        try:
            doc = fitz.open(pdf)
        except Exception as e:
            print(f"Failed to open {pdf}: {e}")
            continue

        title = (doc.metadata.get("title") or pdf.stem)
        namespace = guess_namespace(pdf.name, title)
        doc_level_systems = guess_systems(pdf.name + " " + title)

        toc = get_toc(doc)
        secs = section_ranges_from_toc(toc, doc.page_count)
        if not secs:
            secs = [{"title": "Document", "level": 1, "start": 0, "end": doc.page_count-1, "path": [title]}]

        # Pass 1: extract text per section and page; collect images with captions
        images_collected = []
        page_text_cache: Dict[int, Dict[str, Any]] = {}
        for pi in range(doc.page_count):
            p = doc.load_page(pi)
            data = page_blocks_with_images(p)
            page_text_cache[pi] = data
            # save images
            for im in data["images"]:
                xref = im["xref"]
                try:
                    pix = fitz.Pixmap(doc, xref)
                    if pix.n - pix.alpha < 4:
                        img_bytes = pix.tobytes("png")
                    else:
                        pix = fitz.Pixmap(fitz.csRGB, pix)
                        img_bytes = pix.tobytes("png")
                    img_id = sha1_bytes(img_bytes)
                    img_path = images_dir / f"{img_id}.png"
                    if not img_path.exists():
                        with open(img_path, "wb") as f:
                            f.write(img_bytes)
                    caption = nearest_caption_for_image(im["bbox"], data["text_blocks"])
                    images_collected.append({
                        "id": img_id,
                        "path": str(img_path.relative_to(store_dir).as_posix()),
                        "page": pi+1,
                        "bbox": im["bbox"],
                        "caption": caption,
                    })
                except Exception:
                    continue

        # Pass 2: section-aligned text chunks
        for sec in secs:
            sec_pages = list(range(sec["start"], sec["end"]+1))
            sec_text_parts = []
            for pi in sec_pages:
                blocks = page_text_cache[pi]["text_blocks"]
                page_text = "\n".join(tb["text"].strip() for tb in blocks if tb["text"].strip())
                if not page_text or len(page_text) < 50:
                    page = doc.load_page(pi)
                    page_text = ocr_page_text(page)
                if page_text:
                    sec_text_parts.append(page_text)
            sec_text = f"{' > '.join([title] + sec['path'])}\n\n" + "\n\n".join(sec_text_parts)
            chunks = chunk_text(sec_text, chunk_size=1000, overlap=200)

            # find images within this section (page range)
            sec_images = [im for im in images_collected if (sec["start"]+1) <= im["page"] <= (sec["end"]+1)]

            # Index text chunks
            for ci, c in enumerate(chunks, start=1):
                emb = client.embeddings(model=EMBED_MODEL, prompt=c)["embedding"]
                vectors.append(emb)
                meta = {
                    "id": str(uuid.uuid4()),
                    "type": "text",
                    "namespace": namespace,
                    "systems": sorted(set(doc_level_systems + guess_systems(c))),
                    "source": str(pdf.relative_to(ROOT).as_posix()),
                    "doc_title": title,
                    "section_title": sec["title"],
                    "toc_path": [title] + sec["path"],
                    "page_start": sec["start"]+1,
                    "page_end": sec["end"]+1,
                    "chunk": ci,
                    "text": c,
                    "images": [im["id"] for im in sec_images],
                    "filename": pdf.name,
                    "embed_model": EMBED_MODEL,
                }
                meta_fp.write(json.dumps(meta, ensure_ascii=False) + "\n")

            # Index images as pseudo-chunks with captions
            for im in sec_images:
                cap = im["caption"] or f"Image on page {im['page']} in section {sec['title']}"
                ctext = f"[IMAGE] {cap}\nContext: {' > '.join([title] + sec['path'])}"
                try:
                    emb = client.embeddings(model=EMBED_MODEL, prompt=ctext)["embedding"]
                except Exception:
                    continue
                vectors.append(emb)
                meta_img = {
                    "id": im["id"],
                    "type": "image",
                    "namespace": namespace,
                    "systems": doc_level_systems,
                    "source": str(pdf.relative_to(ROOT).as_posix()),
                    "doc_title": title,
                    "section_title": sec["title"],
                    "toc_path": [title] + sec["path"],
                    "page": im["page"],
                    "chunk": 0,
                    "text": ctext,
                    "image_path": im["path"],
                    "bbox": im["bbox"],
                    "filename": pdf.name,
                    "embed_model": EMBED_MODEL,
                }
                meta_fp.write(json.dumps(meta_img, ensure_ascii=False) + "\n")

        doc.close()
        print(f"{pdf.name}: chunks={len(vectors)} images_saved={len(images_collected)}")

    meta_fp.close()
    if not vectors:
        raise RuntimeError("No vectors indexed.")
    arr = np.array(vectors, dtype=np.float32)
    np.save(store_dir / "index.npy", arr)
    manifest = {
        "embed_model": EMBED_MODEL,
        "count": int(arr.shape[0]),
        "dim": int(arr.shape[1]) if arr.ndim == 2 else None,
        "data_dir": str(data_dir),
    }
    with open(store_dir / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"Saved index to {store_dir}: {arr.shape}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default=str(DATA_DIR))
    ap.add_argument("--store-dir", default=str(STORAGE_DIR))
    args = ap.parse_args()
    build_index(Path(args.data_dir), Path(args.store_dir))







