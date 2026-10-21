"""Hugging Face Space: image captioning + text analysis.

Runs on free ZeroGPU when available (the @spaces.GPU decorator is a no-op on CPU hardware).
Optionally logs results (no images, no raw tokens) to a private HF Dataset for storage.
"""
import os
import json
import uuid
import datetime
from pathlib import Path

import spaces  # must be imported before torch for ZeroGPU
import torch
import gradio as gr
from transformers import pipeline

from utils import (
    validate_text, normalize_sentiment, normalize_emotions, text_stats, clean_caption,
)

CAPTION_MODEL = os.getenv("CAPTION_MODEL", "Salesforce/blip-image-captioning-base")
SENTIMENT_MODEL = os.getenv("SENTIMENT_MODEL", "cardiffnlp/twitter-roberta-base-sentiment-latest")
EMOTION_MODEL = os.getenv("EMOTION_MODEL", "j-hartmann/emotion-english-distilroberta-base")

ON_ZERO_GPU = bool(os.getenv("SPACES_ZERO_GPU"))
DEVICE = "cuda" if (ON_ZERO_GPU or torch.cuda.is_available()) else "cpu"
print(f"Loading models on {DEVICE} (ZeroGPU={ON_ZERO_GPU})")

captioner = pipeline("image-to-text", model=CAPTION_MODEL, device=DEVICE)
sentiment = pipeline("text-classification", model=SENTIMENT_MODEL, top_k=None, device=DEVICE)
emotion = pipeline("text-classification", model=EMOTION_MODEL, top_k=None, device=DEVICE)

# ---------- Optional HF storage (private dataset) ----------
scheduler = None
LOG_REPO = os.getenv("LOG_DATASET_REPO")
LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / f"results-{uuid.uuid4()}.jsonl"
if LOG_REPO and os.getenv("HF_TOKEN"):
    try:
        from huggingface_hub import CommitScheduler
        LOG_DIR.mkdir(exist_ok=True)
        scheduler = CommitScheduler(
            repo_id=LOG_REPO, repo_type="dataset", folder_path=LOG_DIR,
            path_in_repo="data", every=5, private=True, token=os.getenv("HF_TOKEN"),
        )
        print(f"Logging results to dataset {LOG_REPO}")
    except Exception as exc:  # storage must never break the app
        print(f"Storage disabled: {exc}")


def log_result(kind, payload):
    if scheduler is None:
        return
    record = {"ts": datetime.datetime.utcnow().isoformat() + "Z", "kind": kind, **payload}
    try:
        with scheduler.lock:
            with LOG_FILE.open("a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
    except Exception as exc:
        print(f"Log write failed: {exc}")


# ---------- Inference ----------
@spaces.GPU(duration=30)
def _caption(image):
    return captioner(image, max_new_tokens=40)


@spaces.GPU(duration=30)
def _analyze(text):
    return sentiment(text, truncation=True), emotion(text, truncation=True)


def caption_image(image):
    if image is None:
        raise gr.Error("Please upload an image.")
    try:
        caption = clean_caption(_caption(image.convert("RGB")))
    except Exception as exc:
        raise gr.Error(f"Captioning failed: {exc}")
    log_result("caption", {"caption": caption, "model": CAPTION_MODEL})
    return caption


def analyze_text(text):
    try:
        cleaned = validate_text(text)
    except ValueError as exc:
        raise gr.Error(str(exc))
    try:
        sent_raw, emo_raw = _analyze(cleaned)
    except Exception as exc:
        raise gr.Error(f"Text analysis failed: {exc}")
    result = {
        "sentiment": normalize_sentiment(sent_raw),
        "emotions": normalize_emotions(emo_raw),
        "stats": text_stats(cleaned),
    }
    log_result("text", {"text": cleaned[:500], "result": result})
    return result


with gr.Blocks(title="Vision Caption & Text Analysis") as demo:
    gr.Markdown("# Vision Caption & Text Analysis\nBackend API for the GitHub Pages app.")
    with gr.Tab("Image caption"):
        img = gr.Image(type="pil", label="Upload image")
        cap_btn = gr.Button("Generate caption", variant="primary")
        cap_out = gr.Textbox(label="Caption")
        cap_btn.click(caption_image, inputs=img, outputs=cap_out, api_name="caption")
    with gr.Tab("Text analysis"):
        txt = gr.Textbox(lines=6, label="Text")
        txt_btn = gr.Button("Analyze", variant="primary")
        txt_out = gr.JSON(label="Result")
        txt_btn.click(analyze_text, inputs=txt, outputs=txt_out, api_name="analyze")

demo.queue(max_size=20).launch()
