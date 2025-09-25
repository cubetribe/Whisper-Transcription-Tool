# Textkorrektur-Workflow (Modul 5)

Diese Seite beschreibt Architektur, Ablauf und Best Practices für die LLM-basierte Textkorrektur.

## Prozessübersicht
1. **Transkription** – Whisper erstellt Rohtext (`*_original.txt`).
2. **Trigger** – UI/CLI setzt `enable_correction`, Level & Dialektoption.
3. **Model Swap** – ResourceManager entlädt Whisper, lädt LeoLM (Q4_K_M).
4. **Chunking** – BatchProcessor segmentiert Text (Token & Satzgrenzen, Overlap=1).
5. **Prompting** – `PromptTemplates` generiert System/User-Prompts je Chunk.
6. **Inference** – LeoLM korrigiert Chunks; Fortschritt via WebSocket.
7. **Reassembly** – Chunks werden zusammengeführt, Konsistenz geprüft.
8. **Output** – Korrigierter Text (`*_corrected.txt`, JSON-Metadaten) gespeichert.
9. **Cleanup** – ResourceManager entlädt LeoLM, optional Whisper reload.

## Komponenten & Verantwortlichkeiten
- **LLMCorrector** – Laden/Entladen, Token-Schätzung, Inferenz, Fehlerbehandlung.
- **BatchProcessor** – Chunking, Overlap-Handling, Reassembly.
- **ResourceManager** – Thread-safe Model-Locks, RAM-Prüfung (`memory_threshold_gb`).
- **WebSocket Events** – `correction_started`, `correction_progress`, `correction_completed`, `correction_error`.

## Konfigurationsparameter (`text_correction`)
| Feld | Beschreibung | Standard |
| --- | --- | --- |
| `enabled` | Globale Voreinstellung | `false` |
| `model_path` | Pfad zur GGUF-Datei | `~/models/leolm-13b/...` |
| `context_length` | Max Tokens pro Chunk | `2048` |
| `temperature` | Generationsparameter | `0.3` |
| `correction_level` | Default-Stufe | `standard` |
| `dialect_normalization` | Dialekt → Hochdeutsch | `false` |
| `chunk_overlap_sentences` | Satz-Overlap | `1` |
| `memory_threshold_gb` | Minimal verfügbarer RAM | `6.0` |
| `fallback_on_error` | Bei Fehler nur Original ausgeben | `true` |

## Fehlertoleranz
- Modell fehlt → UI-Hinweis, Event `correction_error` mit `fallback_action=correction_skipped`.
- RAM zu niedrig → Warnung, Korrektur übersprungen.
- Einzelner Chunk fehlerhaft → Fortsetzung mit verbleibenden Chunks, Log-Eintrag.

## Tests & Monitoring
- **Unit**: Prompt-Generierung, Token-Schätzung, ResourceManager-Locks.
- **Integration**: End-to-End (`test_module5_integration.py`).
- **Performance**: Memory-Stresstests, Korrektur-Dauer (`correction_duration_seconds`).

Für Implementation Details siehe [Design-Spezifikation](https://github.com/cubetribe/WhisperCC_MacOS_Local/blob/main/.kiro/specs/llm-text-correction/design.md) und den Quellcode in [`src/whisper_transcription_tool/module5_text_correction/`](https://github.com/cubetribe/WhisperCC_MacOS_Local/tree/main/src/whisper_transcription_tool/module5_text_correction).
