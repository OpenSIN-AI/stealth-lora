# brain.md — Architektur (stealth-lora)

> **← [stealth-runner/brain.md](https://github.com/OpenSIN-AI/stealth-runner/blob/main/brain.md) für Gesamtarchitektur**

---

## Repo-Architektur

- **Layer**: 💰 LoRA
- **Beschreibung**: LoRA Training + KeyPoolManager — 10-fail Rotation
- **Technologie**: (Dokumentation folgt)

## Stealth Suite Integration

Dieses Repo ist Teil der Stealth Suite und MUSS:
1. CUA-ONLY Architektur respektieren
2. Pipeline (perceive→plan→guard→execute→critique) einhalten
3. BANNED Tools vermeiden

## Abhängigkeiten

- [stealth-runner](https://github.com/OpenSIN-AI/stealth-runner) — Orchestrator
- DOC-HEALTH: `python3 /Users/jeremy/dev/stealth-runner/scripts/check_doc_health.py --repo stealth-lora`

**Letztes Update**: 2026-05-07
