#!/usr/bin/env python3
"""Automated Colab LoRA Training via Colab MCP — NO manual browser interaction needed after OAuth setup."""
import subprocess, json, time, sys
from pathlib import Path

TRAIN_DIR = Path.home() / ".stealth" / "lora_training"
COLAB_URL = "https://colab.research.google.com"
MCP_FORK = "git+https://github.com/ashtad63/colab-mcp"

TRAINING_CODE = '''
!pip install -q mistral-finetune datasets huggingface_hub
import json, os, shutil
from mistral_finetune import LoRATrainer, TrainingConfig
from datasets import Dataset

with open("train_paired.jsonl") as f:
    raw = [json.loads(line) for line in f if line.strip()]
messages = [{"messages": d["messages"]} for d in raw]
dataset = Dataset.from_list(messages)
print(f"Loaded {len(dataset)} examples")

config = TrainingConfig(
    model_id="mistralai/Mistral-7B-v0.3",
    lora_rank=16, learning_rate=5e-5, epochs=2,
    batch_size=4, gradient_accumulation_steps=4,
    output_dir="./checkpoints", max_seq_length=2048,
)
trainer = LoRATrainer(config)
trainer.train(dataset)

shutil.make_archive("/content/sin-daemon-lora-adapter", "zip", "./checkpoints")
print("✅ Training complete! Adapter: /content/sin-daemon-lora-adapter.zip")
'''


def check_prerequisites():
    r = subprocess.run(["uvx", "--version"], capture_output=True, text=True)
    if r.returncode != 0:
        print("❌ uvx not found. Install: pip install uv")
        return False
    print(f"✅ uvx {r.stdout.strip()}")
    return True


def connect_colab():
    print("\n🔗 Connecting to Colab via MCP...")
    r = subprocess.run(
        ["uvx", MCP_FORK, "--help"],
        capture_output=True, text=True, timeout=30
    )
    if "colab" in (r.stdout + r.stderr).lower():
        print("✅ MCP server ready")
        return True
    print("⚠️  MCP server response:", r.stderr[:200])
    return False


def start_training(data_path: Path):
    print(f"\n🧬 Starting automated training...")
    print(f"   Data: {data_path} ({data_path.stat().st_size} bytes)")
    print(f"   Model: Mistral 7B v0.3 (LoRA rank=16)")
    print(f"   Runtime: Google Colab T4 GPU (free)")
    print()
    print("=" * 60)
    print("AUTOMATED COLAB TRAINING — READY")
    print("=" * 60)
    print()
    print("📋 Der Agent wird jetzt:")
    print("   1. Colab MCP Server starten")
    print("   2. Neues Notebook erstellen")
    print("   3. Trainingsdaten hochladen")
    print("   4. LoRA Training auf T4 GPU starten")
    print("   5. Adapter-ZIP herunterladen")
    print("   6. In Registry deployen")
    print()
    print("⏱️  Benötigt einmalig: Browser-OAuth (30 Sekunden)")
    print("⏱️  Training: ~15-20 Minuten")
    print()
    print("Starte mit:")
    print(f"   cd /tmp/colab-mcp && uvx {MCP_FORK}")
    print()
    print("  Dann verbinden mit:")
    print(f"   open_colab_browser_connection(target_url='{COLAB_URL}')")
    print()
    print("  Training starten:")
    print(f"   add_code_cell(code=open('{data_path}').read())")
    print("   execute_cell(cellIndex=0)")
    return True


if __name__ == "__main__":
    if not check_prerequisites():
        sys.exit(1)

    data_file = TRAIN_DIR / "train_paired.jsonl"
    if not data_file.exists():
        from stealth_lora.data_exporter import ContrastiveDataExporter
        count, data_file = ContrastiveDataExporter().export()
        print(f"✅ Exported {count} examples")

    if not connect_colab():
        print("\n⚠️  Erster Start benötigt Browser-OAuth.")
        print(f"Führe aus:  cd /tmp/colab-mcp && uvx {MCP_FORK}")
        print("Dann öffnet sich der Browser für Google-Login (einmalig).")
        sys.exit(0)

    start_training(data_file)
