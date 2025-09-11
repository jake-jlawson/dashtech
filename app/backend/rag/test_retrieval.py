import os, json, argparse
from typing import List, Dict, Any, Optional
import numpy as np
from pathlib import Path
from ollama import Client

ROOT = Path(__file__).resolve().parents[3]
STORE_DIR = ROOT / "app" / "backend" / "rag" / "store"
INDEX_PATH = STORE_DIR / "index.npy"
META_PATH = STORE_DIR / "meta.jsonl"


def load_store():
  vecs = np.load(INDEX_PATH).astype(np.float32)
  meta: List[Dict[str, Any]] = []
  with open(META_PATH, "r", encoding="utf-8") as f:
    for line in f:
      line = line.strip()
      if not line:
        continue
      meta.append(json.loads(line))
  if len(meta) != vecs.shape[0]:
    raise RuntimeError(f"meta count {len(meta)} != vectors {vecs.shape[0]}")
  return vecs, meta

def cosine_search(vecs: np.ndarray, q: np.ndarray, k: int, mask: Optional[np.ndarray] = None):
  V = vecs if mask is None else vecs[mask]
  qn = q / (np.linalg.norm(q) + 1e-8)
  Vn = V / (np.linalg.norm(V, axis=1, keepdims=True) + 1e-8)
  sims = Vn @ qn
  k = min(k, len(sims))
  idx = np.argpartition(-sims, k-1)[:k]
  idx = idx[np.argsort(-sims[idx])]
  if mask is None:
    return idx, sims[idx]
  else:
    # map masked idx back to global indices
    global_idx = np.nonzero(mask)[0][idx]
    return global_idx, sims[idx]

def build_mask(meta: List[Dict[str, Any]], namespaces, systems, types):
  m = np.ones(len(meta), dtype=bool)
  if namespaces:
    ns = set([s.strip().lower() for s in namespaces])
    m &= np.array([(d.get("namespace","shared").lower() in ns) for d in meta], dtype=bool)
  if systems:
    sysset = set([s.strip().lower() for s in systems])
    def has_system(d):
      vals = [s.lower() for s in (d.get("systems") or [])]
      return any(s in sysset for s in vals)
    m &= np.array([has_system(d) for d in meta], dtype=bool)
  if types:
    tset = set([t.strip().lower() for t in types])
    m &= np.array([(d.get("type","text").lower() in tset) for d in meta], dtype=bool)
  return m

def main():
  ap = argparse.ArgumentParser()
  ap.add_argument("--q", required=True, help="query text")
  ap.add_argument("--k", type=int, default=8)
  ap.add_argument("--ns", default="", help="comma-separated namespaces (diagnostics,maintenance,shared)")
  ap.add_argument("--systems", default="", help="comma-separated systems (engine,brakes,...)")
  ap.add_argument("--types", default="", help="comma-separated types (text,image)")
  ap.add_argument("--base-url", default="http://localhost:11434")
  ap.add_argument("--embed-model", default="nomic-embed-text")
  args = ap.parse_args()

  vecs, meta = load_store()
  client = Client(host=args.base_url)
  q = np.array(client.embeddings(model=args.embed_model, prompt=args.q)["embedding"], dtype=np.float32)

  namespaces = [s for s in args.ns.split(",") if s] or None
  systems = [s for s in args.systems.split(",") if s] or None
  types = [s for s in args.types.split(",") if s] or None
  mask = build_mask(meta, namespaces, systems, types)

  idx, sims = cosine_search(vecs, q, args.k, mask=mask)

  for rank, (i, s) in enumerate(zip(idx, sims), start=1):
    m = meta[i]
    t = m.get("type","text")
    hdr = f"#{rank} [{t}] score={s:.3f} ns={m.get('namespace')} sys={m.get('systems')}"
    loc = f"{m.get('doc_title','')} > {m.get('section_title','')} | src={m.get('source','')}"
    if t == "image":
      img = m.get("image_path")
      page = m.get("page")
      print(hdr); print(loc); print(f"page={page} image={img}")
      print(m.get("text","")[:200].replace("\n"," ") + "...")
    else:
      pstart, pend = m.get("page_start"), m.get("page_end")
      print(hdr); print(loc); print(f"pages={pstart}-{pend}")
      snippet = (m.get("text","")[:400]).replace("\n"," ")
      print(snippet + "...")
    print("-"*80)

if __name__ == "__main__":
  main()