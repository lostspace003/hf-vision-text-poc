# 🔍 Vision Caption & Text Analysis (Hugging Face POC)

Two-tab web app:

| Tab | What it does | Model |
|---|---|---|
| 🖼️ Image Caption | Upload an image → get a caption | [`Salesforce/blip-image-captioning-base`](https://huggingface.co/Salesforce/blip-image-captioning-base) |
| 📝 Text Analysis | Type text → sentiment, top emotions, stats | [`cardiffnlp/twitter-roberta-base-sentiment-latest`](https://huggingface.co/cardiffnlp/twitter-roberta-base-sentiment-latest), [`j-hartmann/emotion-english-distilroberta-base`](https://huggingface.co/j-hartmann/emotion-english-distilroberta-base) |

**Live app (GitHub Pages):** https://lostspace003.github.io/hf-vision-text-poc/

## Architecture

```
GitHub Pages (web/)  ──@gradio/client──►  Hugging Face Space (space/, Gradio, ZeroGPU)
  static HTML/JS                               transformers pipelines
  NO tokens                                    HF_TOKEN = Space secret
                                                    │ CommitScheduler
                                                    ▼
                                         HF Dataset (private): <user>/vision-text-logs
```

* **Frontend** – `web/` static HTML/CSS/JS, hosted on GitHub Pages. It calls the public Space's API with [`@gradio/client`](https://www.gradio.app/guides/getting-started-with-the-js-client). It never contains a token.
* **Backend** – `space/` Gradio app on a Hugging Face Space. It requests **ZeroGPU** (`zero-a10g`). If your account can't use ZeroGPU (hosting ZeroGPU Spaces needs a PRO account or a PRO organization), the deploy falls back to free **CPU basic**. Functions are wrapped in `@spaces.GPU`, which does nothing on CPU.
* **Storage** – results (captions and text analysis, **never images**) are appended as JSONL to a **private HF Dataset** through `huggingface_hub.CommitScheduler`, once every 5 min.
* **Data source** – live inference on the user's input. No mock data.

## Setup (one time)

1. Create a Hugging Face **write** token: https://huggingface.co/settings/tokens
2. In GitHub, go to **Settings → Secrets and variables → Actions → New repository secret**:
   `Name: HF_TOKEN`, `Value: hf_...`
3. Go to **Actions → CI & Deploy → Run workflow**, or push to `main`.
4. In **Settings → Pages**, set Source to *Deploy from a branch*, branch `gh-pages` / `(root)` (if it isn't already).

The workflow then:
1. runs the Python and JS unit tests,
2. creates/updates the Space `<hf-user>/vision-text-poc` and the private dataset `<hf-user>/vision-text-logs`, stores `HF_TOKEN` as a **Space secret**, and requests ZeroGPU,
3. writes `web/config.json` with the Space ID and publishes `web/` to the `gh-pages` branch.

> The first request after the Space sleeps can take ~1–2 min (cold start and model download).

## Local development

```bash
# frontend
cd web && python -m http.server 8000   # open http://localhost:8000, set Space ID in Settings
# backend
cd space && pip install gradio==5.35.0 -r requirements.txt && python app.py
# tests
python -m unittest discover -s tests -p "test_*.py"
node --test tests/utils.test.mjs
```

## Security

* No secrets are committed. `HF_TOKEN` exists only in GitHub Actions secrets and the HF Space secret store.
* The frontend validates input type, size (10 MB image, 5000 chars text) and escapes all output.
* Prefer a **fine-grained** token limited to this Space and dataset, and rotate it regularly.

## References

* Microsoft Learn – [What are Hugging Face Transformers?](https://learn.microsoft.com/azure/databricks/machine-learning/train-model/huggingface/)
* Microsoft Learn – [Fine-tune Hugging Face models (pipelines for text-classification)](https://learn.microsoft.com/azure/databricks/machine-learning/train-model/huggingface/fine-tune-model)
* Microsoft Learn – [NLP batch processing with Hugging Face pipelines](https://learn.microsoft.com/azure/machine-learning/how-to-nlp-processing-batch)
* Hugging Face – [Transformers pipelines](https://huggingface.co/docs/transformers/pipeline_tutorial), [ZeroGPU Spaces](https://huggingface.co/docs/hub/spaces-zerogpu), [Spaces secrets](https://huggingface.co/docs/hub/spaces-overview#managing-secrets), [Space storage via datasets](https://huggingface.co/docs/huggingface_hub/guides/upload#scheduled-uploads)

License: Apache-2.0
