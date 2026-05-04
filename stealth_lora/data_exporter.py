"""Contrastive Data Exporter für Fireworks SFT – Export nach JSONL."""
import json
from pathlib import Path
from datetime import datetime

STEALTH_DATA = Path.home() / ".stealth"
TRAIN_DIR = STEALTH_DATA / "lora_training"
MINIMAX_BASE = "accounts/fireworks/models/minimax-m2p7"


def _pair_record(intent: str, verdict: str, weight: float = 1.0) -> dict:
    return {
        "messages": [
            {"role": "system", "content": "Du bist SIN-daemon. Analysiere AX-Tree und antworte mit der optimalen Aktion."},
            {"role": "user", "content": intent},
            {"role": "assistant", "content": verdict},
        ],
        "weight": weight,
    }


def _negative_record(intent: str, bad_response: str, weight: float = 0.5) -> dict:
    return {
        "messages": [
            {"role": "system", "content": "Du bist SIN-daemon. Analysiere AX-Tree und antworte mit der optimalen Aktion."},
            {"role": "user", "content": intent},
            {"role": "assistant", "content": bad_response},
        ],
        "weight": weight,
    }


class ContrastiveDataExporter:
    def __init__(self, min_examples: int = 10, output_path: Path = None):
        self.min_examples = min_examples
        self.output_path = output_path or (TRAIN_DIR / "train_paired.jsonl")
        TRAIN_DIR.mkdir(parents=True, exist_ok=True)

    def _load_learn_records(self) -> list:
        records = []
        for md_path in [STEALTH_DATA / "learn.md", TRAIN_DIR / "learn_snippets.jsonl"]:
            if not md_path.exists():
                continue
            content = md_path.read_text() if md_path.suffix == ".md" else ""
            if md_path.suffix == ".jsonl":
                for line in md_path.read_text().splitlines():
                    if line.strip():
                        records.append(json.loads(line))
            else:
                for block in content.split("\n## "):
                    if not block.strip():
                        continue
                    lines = block.split("\n")
                    intent = lines[0].strip("# ").strip()
                    verdict = "\n".join(lines[1:]).strip()
                    if intent and verdict:
                        records.append({"intent": intent, "verdict": verdict})
        return records

    def export(self) -> tuple[int, Path]:
        records = self._load_learn_records()
        if len(records) < self.min_examples:
            return 0, self.output_path
        pairs = []
        for r in records:
            intent = r.get("intent", r.get("query", ""))
            verdict = r.get("verdict", r.get("answer", ""))
            outcome = r.get("outcome", "success")
            weight = {"success": 1.0, "workaround": 0.8, "failure": 0.5}.get(outcome, 0.7)
            pairs.append(_pair_record(intent, verdict, weight))
        with self.output_path.open("w") as f:
            for p in pairs:
                f.write(json.dumps(p, ensure_ascii=False) + "\n")
        return len(pairs), self.output_path