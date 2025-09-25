# Troubleshooting & FAQ

## Häufige Probleme
### Whisper CLI fehlt / nicht ausführbar
**Symptom:** `Permission denied` oder `whisper-cli not found`
**Lösung:**
```bash
bash install.sh
chmod +x deps/whisper.cpp/build/bin/whisper-cli
```

### LeoLM-Modell nicht gefunden
**Symptom:** UI zeigt „Textkorrektur nicht verfügbar“
**Lösung:** Pfad in `text_correction.model_path` prüfen oder `scripts/download_leolm.py` ausführen. Eventuell `TEXT_CORRECTION_MODEL_PATH` setzen.

### RAM zu niedrig für Korrektur
**Symptom:** Event `correction_error` mit `INSUFFICIENT_MEMORY`
**Lösung:** Andere Anwendungen schließen, Swap erhöhen, `memory_threshold_gb` anpassen oder Korrektur deaktivieren.

### WebSocket-Verbindung bricht ab
**Symptom:** Fortschrittsanzeige stoppt
**Lösung:** Browser-DevTools prüfen, Server-Logs (`text_correction` Logger) anschauen, ggf. Server neu starten.

### macOS-App startet nicht
**Symptom:** `WhisperLocal.app` öffnet sich nicht
**Lösung:** `macos/prepare_final_release.sh` ausführen, Code-Signing prüfen, Gatekeeper-Dialog bestätigen.

## FAQ
**Frage:** Kann ich andere LLMs nutzen?
> Ja, solange sie GGUF-kompatibel und über llama-cpp-python ladbar sind. Konfiguriere `model_path` und Kontextlänge.

**Frage:** Wie vergleiche ich Original und korrigierte Texte?
> UI bietet Download beider Versionen. Für Diffs eignen sich Tools wie `meld` oder `code --diff`.

**Frage:** Unterstützt das System Mehrsprachigkeit?
> Whisper erkennt Sprache automatisch. Korrektor ist derzeit auf Deutsch optimiert; Erweiterungen geplant.

**Frage:** Wie sichere ich meine Daten?
> Siehe `documentation/BACKUP_INFO.md`. Transkripte liegen in `transcriptions/`; Modelle können groß sein.

**Frage:** Gibt es Telemetrie?
> Standardmäßig nein. Optionale Metriken können in `text_correction.monitoring_enabled` aktiviert werden.

Weitere Fragen? Issue mit Label `question` eröffnen oder im internen Slack nachfragen.
