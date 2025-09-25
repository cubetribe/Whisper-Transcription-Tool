# Konfiguration & Betrieb

## Konfigurationsdatei
Hauptkonfiguration liegt standardmäßig in `~/.whisper_tool.json`. Relevante Sektionen:
- `output` – Standardverzeichnisse, Temp-Ordner
- `models` – Whisper-Modelle, Downloadpfade
- `text_correction` – LeoLM-Integration (siehe Tabelle unten)

Beispiel:
```json
{
  "output": {
    "default_directory": "~/transcriptions",
    "temp_directory": "~/transcriptions/temp"
  },
  "text_correction": {
    "enabled": false,
    "model_path": "~/models/leolm-13b/LeoLM-hesseianai-13b-chat.Q4_K_M.gguf",
    "context_length": 2048,
    "temperature": 0.3,
    "correction_level": "standard",
    "dialect_normalization": false,
    "memory_threshold_gb": 6.0,
    "max_parallel_jobs": 1
  }
}
```

## CLI-Parameter
```bash
# Webserver starten mit Textkorrektur
python -m src.whisper_transcription_tool.main web \
  --port 8090 \
  --enable-correction \
  --correction-level strict \
  --dialect-normalization

# CLI-Transkription inkl. Korrektur
whisper-tool transcribe audio.mp3 --enable-correction
```

## Umgebungsvariablen
- `WHISPER_TOOL_CONFIG` – Pfad zur Alternativkonfiguration
- `TEXT_CORRECTION_MODEL_PATH` – überschreibt `model_path`
- `LLAMA_CPP_NUM_THREADS` – Performance-Tuning

## Deployment-Hinweise
- **macOS-App:** Skripte in `macos/` (`prepare_final_release.sh`, `create_release.sh`).
- **CI/CD:** Workflows `build-macos-app.yml`, `phone_recording_tests.yml`.
- **Backup:** siehe `Backups/` & `documentation/BACKUP_INFO.md`.

## Monitoring & Logging
- Logging-Konfiguration über `telemetry` Sektion oder `LOG_LEVEL` Env
- `text_correction` Logger schreibt detaillierte LLM-Operationen
- Optionale Metriken: `correction_duration_seconds`, `memory_usage_mb`

Weitere Tipps siehe [CONFIG_EXAMPLES.md](https://github.com/cubetribe/WhisperCC_MacOS_Local/blob/main/documentation/CONFIG_EXAMPLES.md) & [TROUBLESHOOTING.md](https://github.com/cubetribe/WhisperCC_MacOS_Local/blob/main/documentation/TROUBLESHOOTING.md).
