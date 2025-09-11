from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path
import json
import numpy as np
from ollama import Client


class RagRetriever:
    """
    Lightweight local RAG retriever over numpy + Ollama embeddings.

    Store layout (created by build.py):
      - store/index.npy         float32 [num_chunks, dim]
      - store/meta.jsonl        one json per vector (metadata)
      - store/images/*.png      extracted images (referenced by meta.image_path)
    """

    def __init__(
        self,
        store_dir: Optional[Path] = None,
        base_url: str = "http://localhost:11434",
        embed_model: str = "nomic-embed-text",
    ) -> None:
        here = Path(__file__).resolve().parent  # .../rag
        self.store_dir = Path(store_dir) if store_dir is not None else (here / "store")
        self.index_path = self.store_dir / "index.npy"
        self.meta_path = self.store_dir / "meta.jsonl"
        self.client = Client(host=base_url)
        self.embed_model = embed_model

        # lazy-loaded
        self._vecs: Optional[np.ndarray] = None
        self._meta: Optional[List[Dict[str, Any]]] = None

    def ensure_loaded(self) -> None:
        if self._vecs is not None and self._meta is not None:
            return
        vecs = np.load(self.index_path).astype(np.float32)
        meta: List[Dict[str, Any]] = []
        with open(self.meta_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                meta.append(json.loads(line))
        if len(meta) != vecs.shape[0]:
            raise RuntimeError(f"RAG store corrupted: meta={len(meta)} vs vecs={vecs.shape[0]}")
        self._vecs = vecs
        self._meta = meta

    def embed(self, text: str) -> np.ndarray:
        res = self.client.embeddings(model=self.embed_model, prompt=text)
        return np.array(res["embedding"], dtype=np.float32)

    def _build_mask(
        self,
        namespaces: Optional[List[str]] = None,
        systems: Optional[List[str]] = None,
        types: Optional[List[str]] = None,
    ) -> np.ndarray:
        assert self._meta is not None
        mask = np.ones(len(self._meta), dtype=bool)
        if namespaces:
            ns = {n.lower() for n in namespaces}
            mask &= np.array([(m.get("namespace", "shared").lower() in ns) for m in self._meta], dtype=bool)
        if systems:
            sys = {s.lower() for s in systems}
            def has_system(m: Dict[str, Any]) -> bool:
                vals = [s.lower() for s in (m.get("systems") or [])]
                return any(v in sys for v in vals)
            mask &= np.array([has_system(m) for m in self._meta], dtype=bool)
        if types:
            tt = {t.lower() for t in types}
            mask &= np.array([(m.get("type", "text").lower() in tt) for m in self._meta], dtype=bool)
        return mask

    def search(
        self,
        query: str,
        k: int = 8,
        namespaces: Optional[List[str]] = None,
        systems: Optional[List[str]] = None,
        types: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Returns list of results with fields: score, type, text, image_path?, meta
        """
        self.ensure_loaded()
        assert self._vecs is not None and self._meta is not None

        q = self.embed(query)
        mask = self._build_mask(namespaces=namespaces, systems=systems, types=types)
        if not mask.any():
            return []

        V = self._vecs[mask]
        qn = q / (np.linalg.norm(q) + 1e-8)
        Vn = V / (np.linalg.norm(V, axis=1, keepdims=True) + 1e-8)
        sims = Vn @ qn
        k = min(k, len(sims))
        idx = np.argpartition(-sims, k - 1)[:k]
        idx = idx[np.argsort(-sims[idx])]
        global_idx = np.nonzero(mask)[0][idx]

        results: List[Dict[str, Any]] = []
        for gi, si in zip(global_idx, sims[idx]):
            m = self._meta[int(gi)]
            item: Dict[str, Any] = {
                "score": float(si),
                "type": m.get("type", "text"),
                "text": m.get("text", ""),
                "meta": {
                    "namespace": m.get("namespace"),
                    "systems": m.get("systems"),
                    "doc_title": m.get("doc_title"),
                    "section_title": m.get("section_title"),
                    "toc_path": m.get("toc_path"),
                    "source": m.get("source"),
                    "page": m.get("page"),
                    "page_start": m.get("page_start"),
                    "page_end": m.get("page_end"),
                    "filename": m.get("filename"),
                },
            }
            if m.get("type") == "image":
                img_rel = m.get("image_path", "")
                item["image_path"] = str((self.store_dir / img_rel).resolve())
            else:
                item["linked_images"] = m.get("images", [])
            results.append(item)

        return results


