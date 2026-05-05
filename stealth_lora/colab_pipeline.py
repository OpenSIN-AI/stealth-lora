#!/usr/bin/env python3
"""SIN-daemon Colab LoRA Training — End-to-End Pipeline.

1. Export training data from learn.md → JSONL
2. Generate Colab notebook with mistral-finetune code
3. Upload training data to HuggingFace (optional)
4. Open Colab with pre-filled notebook URL
5. After training: deploy adapter to registry
"""
import json, sys, webbrowser, subprocess
from pathlib import Path
from datetime import datetime
from stealth_lora.colab_launcher import ColabLauncher
from stealth_lora.trainer_sota import ColabTrainerSOTA

STEALTH_DATA = Path.home() / ".stealth"
TRAIN_DIR = STEALTH_DATA / "lora_training"
ADAPTER_REGISTRY = STEALTH_DATA / "adapter_registry.json"

COLAB_TEMPLATE = '''# SIN-daemon LoRA Training (Mistral 7B via Colab T4 — KOSTENLOS)
!pip install -q mistral-finetune datasets huggingface_hub

import json, os
from mistral_finetune import LoRATrainer, TrainingConfig
from datasets import Dataset
from huggingface_hub import HfApi

# ============================================================
# 1. DATASET LADEN
# ============================================================
# Upload die train_paired.jsonl-Datei in Colab (links auf "Files" klicken)
# Oder ersetze den Pfad mit deinem HuggingFace-Dataset

with open("train_paired.jsonl") as f:
    raw = [json.loads(line) for line in f if line.strip()]

print(f"Geladen: {len(raw)} Beispiele")

# Konvertiere zu ChatML-Format (mistral-finetune erwartet messages-Liste)
messages = []
for d in raw:
    messages.append({"messages": d["messages"]})

dataset = Dataset.from_list(messages)
print(f"Dataset: {len(dataset)} samples, Format: ChatML")

# ============================================================
# 2. LORA TRAINING (KOSTENLOS auf T4 GPU)
# ============================================================
MODEL_ID = "{HF_MODEL}"
OUTPUT_DIR = "./checkpoints"

config = TrainingConfig(
    model_id=MODEL_ID,
    lora_rank=16,
    learning_rate=5e-5,
    epochs=2,
    batch_size=4,
    gradient_accumulation_steps=4,
    output_dir=OUTPUT_DIR,
    max_seq_length=2048,
)

print(f"Starte Training: {MODEL_ID}")
print(f"LoRA rank=16, epochs=2, batch=4, grad_accum=4")

trainer = LoRATrainer(config)
trainer.train(dataset)

print(f"\\n✅ Training abgeschlossen!")
print(f"Adapter gespeichert in: {OUTPUT_DIR}/")

# ============================================================
# 3. UPLOAD ZU HUGGINGFACE (optional)
# ============================================================
UPLOAD = False  # Auf True setzen wenn du pushen willst
HF_REPO = "delqhi/sin-daemon-lora"

if UPLOAD:
    api = HfApi()
    api.create_repo(HF_REPO, exist_ok=True)
    api.upload_folder(
        folder_path=OUTPUT_DIR,
        repo_id=HF_REPO,
        repo_type="model",
    )
    print(f"\\n📤 Uploaded to https://huggingface.co/{HF_REPO}")

# ============================================================
# 4. ADAPTER-DOWNLOAD (für lokale Nutzung)
# ============================================================
from google.colab import files
import shutil, os

shutil.make_archive("sin-daemon-lora-adapter", "zip", OUTPUT_DIR)
files.download("sin-daemon-lora-adapter.zip")
print("\\n📥 Adapter als ZIP heruntergeladen")

print(f"\\n{'='*60}")
print("DEPLOY:")
print("  1. ZIP entpacken")
print("  2. stealth-lora deploy --adapter-id sin-lora-{DATE}")
print(f"{'='*60}")
'''


def run_pipeline(hf_token: str = "", open_browser: bool = True):
    print("=" * 60)
    print("🧬 SIN-DAEMON COLAB LORA TRAINING PIPELINE")
    print("=" * 60)

    launcher = ColabLauncher(model="7b", hf_token=hf_token)
    count, data_path = launcher.export_for_colab()

    if count < 5:
        print(f"\n❌ Nur {count} Beispiele (< 5). Sammle mehr Survey-Daten!")
        return

    print(f"\n📊 Trainingsdaten: {count} Beispiele → {data_path}")

    notebook_code = COLAB_TEMPLATE.replace("{HF_MODEL}", launcher.model).replace(
        "{DATE}", datetime.now().strftime("%Y%m%d"))

    notebook_path = TRAIN_DIR / f"colab_train_{datetime.now().strftime('%Y%m%d_%H%M')}.ipynb"

    cells = [{"cell_type": "code", "metadata": {}, "execution_count": None,
               "outputs": [], "source": [notebook_code]}]
    notebook = {"cells": cells, "metadata": {"colab": {"provenance": []}},
                 "nbformat": 4, "nbformat_minor": 0}

    TRAIN_DIR.mkdir(parents=True, exist_ok=True)
    notebook_path.write_text(json.dumps(notebook))
    print(f"📓 Colab Notebook erstellt: {notebook_path}")
    print(f"📁 Dataset: {data_path}")
    print(f"\n🚀 NÄCHSTE SCHRITTE:")
    print(f"   1. Öffne https://colab.research.google.com/")
    print(f"   2. Upload → {notebook_path.name}")
    print(f"   3. Upload → {data_path.name}")
    print(f"   4. Runtime → Run all (Strg+F9)")
    print(f"   5. Adapter-ZIP herunterladen")
    print(f"   6. Deploy mit: python3 -c \"from stealth_lora.trainer_sota import ColabTrainerSOTA; ColabTrainerSOTA().deploy_adapter('sin-lora-{datetime.now().strftime('%Y%m%d')}')\"")

    if open_browser:
        webbrowser.open("https://colab.research.google.com/")

    return notebook_path


if __name__ == "__main__":
    hf = sys.argv[1] if len(sys.argv) > 1 else ""
    run_pipeline(hf_token=hf)
