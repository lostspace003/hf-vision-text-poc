"""Create/update the Hugging Face Space from ./space using the HF_TOKEN env var.

- Creates a public Gradio Space (exist_ok)
- Stores HF_TOKEN + LOG_DATASET_REPO as Space secret/variable (HF secret store)
- Uploads ./space
- Requests free ZeroGPU hardware (falls back to free CPU if the account is not eligible)
- Writes space_id to $GITHUB_OUTPUT and web/config.json
"""
import json
import os
import sys

from huggingface_hub import HfApi

SPACE_NAME = os.getenv("SPACE_NAME", "vision-text-poc")
DATASET_NAME = os.getenv("DATASET_NAME", "vision-text-logs")


def main():
    token = os.getenv("HF_TOKEN")
    if not token:
        sys.exit("HF_TOKEN secret is not set. Add it in GitHub > Settings > Secrets and variables > Actions.")

    api = HfApi(token=token)
    user = api.whoami()["name"]
    space_id = f"{user}/{SPACE_NAME}"
    dataset_id = f"{user}/{DATASET_NAME}"
    print(f"Deploying Space {space_id}")

    api.create_repo(space_id, repo_type="space", space_sdk="gradio", exist_ok=True, private=False)
    api.create_repo(dataset_id, repo_type="dataset", exist_ok=True, private=True)
    api.add_space_secret(space_id, "HF_TOKEN", token)
    api.add_space_variable(space_id, "LOG_DATASET_REPO", dataset_id)

    api.upload_folder(
        folder_path="space", repo_id=space_id, repo_type="space",
        commit_message=f"Deploy from GitHub {os.getenv('GITHUB_SHA', 'local')[:7]}",
        ignore_patterns=["__pycache__/*", "*.pyc"],
    )

    hardware = "zero-a10g"
    try:
        api.request_space_hardware(space_id, hardware)
        print("Requested ZeroGPU hardware (zero-a10g).")
    except Exception as exc:
        hardware = "cpu-basic"
        print(f"::warning::ZeroGPU not available for this account ({exc}). Using free CPU basic.")

    with open("web/config.json", "w", encoding="utf-8") as f:
        json.dump({"spaceId": space_id, "hardware": hardware}, f, indent=2)

    out = os.getenv("GITHUB_OUTPUT")
    if out:
        with open(out, "a", encoding="utf-8") as f:
            f.write(f"space_id={space_id}\nhardware={hardware}\n")
    print(f"Space URL: https://huggingface.co/spaces/{space_id}")


if __name__ == "__main__":
    main()
