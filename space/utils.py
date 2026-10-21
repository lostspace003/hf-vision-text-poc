"""Pure helper functions (no heavy ML imports) so they can be unit-tested in CI."""

MAX_TEXT_CHARS = 5000

SENTIMENT_LABELS = {
    "label_0": "negative",
    "label_1": "neutral",
    "label_2": "positive",
    "negative": "negative",
    "neutral": "neutral",
    "positive": "positive",
}


def validate_text(text):
    """Return cleaned text or raise ValueError with a user-friendly message."""
    if text is None:
        raise ValueError("Please enter some text to analyze.")
    cleaned = str(text).strip()
    if not cleaned:
        raise ValueError("Please enter some text to analyze.")
    if len(cleaned) > MAX_TEXT_CHARS:
        raise ValueError(f"Text is too long ({len(cleaned)} chars). Max is {MAX_TEXT_CHARS}.")
    return cleaned


def normalize_sentiment(raw):
    """Turn pipeline output [{'label':..,'score':..}] (or nested list) into a sorted dict."""
    if raw and isinstance(raw[0], list):
        raw = raw[0]
    scores = {}
    for item in raw or []:
        label = SENTIMENT_LABELS.get(str(item["label"]).lower(), str(item["label"]).lower())
        scores[label] = round(float(item["score"]), 4)
    top = max(scores, key=scores.get) if scores else None
    return {"label": top, "scores": dict(sorted(scores.items(), key=lambda kv: -kv[1]))}


def normalize_emotions(raw, top_k=3):
    if raw and isinstance(raw[0], list):
        raw = raw[0]
    items = sorted(raw or [], key=lambda x: -float(x["score"]))[:top_k]
    return [{"emotion": str(i["label"]).lower(), "score": round(float(i["score"]), 4)} for i in items]


def text_stats(text):
    words = text.split()
    sentences = [s for s in text.replace("!", ".").replace("?", ".").split(".") if s.strip()]
    return {
        "characters": len(text),
        "words": len(words),
        "sentences": max(1, len(sentences)) if words else 0,
    }


def clean_caption(raw):
    """BLIP returns [{'generated_text': '...'}]; produce a tidy sentence."""
    if not raw:
        return ""
    text = str(raw[0].get("generated_text", "")).strip()
    if not text:
        return ""
    text = text[0].upper() + text[1:]
    return text if text.endswith(".") else text + "."
