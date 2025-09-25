# Schnellstart & Installation

Dieses Dokument führt durch die Einrichtung von WhisperCC MacOS Local auf einem neuen System.

## Systemvoraussetzungen
- **Hardware:** Apple Silicon (empfohlen) oder Intel-Mac mit ≥16 GB RAM
- **Betriebssystem:** macOS 13 Ventura oder neuer
- **Software:**
  - Python 3.11+
  - Homebrew (für FFmpeg und optionale Utilities)
  - Xcode Command Line Tools
  - `llama-cpp-python` (für die Textkorrektur)

## Repository vorbereiten
```bash
# Klonen
git clone https://github.com/cubetribe/WhisperCC_MacOS_Local.git
cd WhisperCC_MacOS_Local

# Virtuelle Umgebung anlegen
python3 -m venv venv_new
source venv_new/bin/activate

# Abhängigkeiten installieren
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .[full]

# Whisper.cpp & FFmpeg einrichten
bash install.sh
chmod +x deps/whisper.cpp/build/bin/whisper-cli
```

## Modelle laden
```bash
# Whisper-Model (empfohlen)
python scripts/download_model.py --model large-v3-turbo

# LeoLM (LLM für Textkorrektur)
python scripts/download_leolm.py --target ~/models/leolm-13b
```

## Startoptionen
- `python -m src.whisper_transcription_tool.main web --port 8090`
- `./start_server.sh` (Terminal)
- `scripts/Start.command` (Doppelklick)
- macOS-App (`WhisperLocal.app`)

Nach dem Start ist die Weboberfläche unter `http://localhost:8090` erreichbar.

## Testlauf
1. Beispiel-Audiodatei in `examples/` auswählen
2. Im Web-UI hochladen, ggf. Textkorrektur aktivieren
3. Fortschritt verfolgen (Transkription → Korrektur)
4. Dateien in `transcriptions/` prüfen

Weitere Details: siehe [Funktionsübersicht](Feature-Overview.md) und [Troubleshooting](Troubleshooting-and-FAQ.md).
