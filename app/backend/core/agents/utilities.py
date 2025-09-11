import json
import re
from typing import Any, Dict, List

# ----- UTILITIES -----
def _jd(x) -> str:
    # compact, stable JSON for prompts
    return json.dumps(x, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def parse_llm_json(output_text: str) -> Dict[str, Any]:
    """
    Parse an LLM response that is intended to be JSON into a Python dict.

    This helper is resilient to common LLM formatting quirks:
    - Surrounding prose before/after the JSON block
    - Markdown code fences (``` or ```json)
    - Minor JSON-ish issues (trailing commas, Python booleans/None)

    It will try multiple strategies in order:
    1) Direct json.loads
    2) Strip markdown code fences and retry
    3) Extract substring from first '{' to last '}' and retry
    4) Progressive truncation from the end to find the largest valid JSON
    5) Light normalization (booleans/None, trailing commas, naive quote fix) and retry

    Raises ValueError if it cannot produce a dict.
    """
    if output_text is None:
        raise ValueError("parse_llm_json: output_text is None")

    text = str(output_text).strip()

    def _try_parse(candidate: str) -> Dict[str, Any] | None:
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
            return None
        except Exception:
            return None

    # 1) Direct parse
    parsed = _try_parse(text)
    if parsed is not None:
        return parsed

    # 2) Strip code fences if present
    fence_match = re.search(r"```(?:json|JSON)?\s*([\s\S]*?)```", text, re.DOTALL)
    if fence_match:
        fenced = fence_match.group(1).strip()
        parsed = _try_parse(fenced)
        if parsed is not None:
            return parsed
        text = fenced  # continue attempts using the inside of the fence

    # 3) Extract substring from first '{' to last '}'
    first = text.find("{")
    last = text.rfind("}")
    if first != -1 and last != -1 and last > first:
        candidate = text[first:last + 1]
        parsed = _try_parse(candidate)
        if parsed is not None:
            return parsed

        # 4) Progressive truncation from the end
        for idx in range(last, first, -1):
            parsed = _try_parse(text[first:idx])
            if parsed is not None:
                return parsed

        # 5) Light normalization and retry
        def _normalize_jsonish(s: str) -> str:
            # Replace Python booleans/None with JSON equivalents
            s = re.sub(r"\bTrue\b", "true", s)
            s = re.sub(r"\bFalse\b", "false", s)
            s = re.sub(r"\bNone\b", "null", s)
            # Remove trailing commas before object/array close
            s = re.sub(r",\s*([}\]])", r"\1", s)
            # Naive single-quote to double-quote conversion when no double quotes present
            if '"' not in s and "'" in s:
                s = s.replace("'", '"')
            return s

        normalized = _normalize_jsonish(candidate)
        parsed = _try_parse(normalized)
        if parsed is not None:
            return parsed

    # If we get here, we failed all attempts
    raise ValueError("Failed to parse LLM output as a JSON object (dict)")




def lookup_error_code(error_code: str) -> str:
    pass


def normalise_probabilities(probabilities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not probabilities:
        return probabilities
    
    # Calculate the sum of all probabilities
    total = sum(prob.get("probability", 0) for prob in probabilities)
    
    # If total is 0 or very close to 0, return equal probabilities
    if total <= 1e-10:
        equal_prob = 1.0 / len(probabilities)
        return [
            {**prob, "probability": equal_prob}
            for prob in probabilities
        ]
    
    # Normalize each probability by dividing by the total
    return [
        {**prob, "probability": prob.get("probability", 0) / total}
        for prob in probabilities
    ]