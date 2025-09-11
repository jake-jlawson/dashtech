from typing import List
import re


# ------------------ Processing Utilities ------------------ #
def clean_text(t: str) -> str:
    t = t.replace("\x00", " ").strip()
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    text = clean_text(text)
    i, out = 0, []
    while i < len(text):
        end = min(i + chunk_size, len(text))
        c = text[i:end].strip()
        if c:
            out.append(c)
        if end == len(text):
            break
        i = max(0, end - overlap)
    return out