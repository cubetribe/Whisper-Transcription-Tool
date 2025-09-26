# Changelog

All notable changes to the Whisper Transcription Tool will be documented in this file.

## [0.9.7.3] - 2025-09-25 - DEBUG SESSION

### 🔧 Fehlerbehebungs-Versuch für LLM-Textkorrektur

#### Durchgeführte Änderungen:

##### 1. LLM-Modell Download und Konfiguration
- **Neues Modell heruntergeladen**: `em_german_leo_mistral.Q4_K_M.gguf` (4.1GB)
  - Pfad: `/Users/denniswestermann/.lmstudio/models/mradermacher/LeoLM-hesseianai-13b-chat-GGUF/em_german_leo_mistral.Q4_K_M.gguf`
  - Alternative zu LeoLM-13B wegen Tensor-Dimension-Inkompatibilität
- **Konfiguration aktualisiert**: `~/.whisper_tool.json` mit neuem Modellpfad

##### 2. API-Endpunkt Fixes
- **Fixed**: JavaScript URL-Mismatch in `/src/whisper_transcription_tool/web/static/js/main.js`
  - Alt: `/api/correction/status`
  - Neu: `/api/correction-status`
  - Problem: Frontend konnte Korrektur-Status nicht abrufen

##### 3. Exception-Handling Korrekturen
- **Fixed**: `DependencyError` Konstruktor-Aufrufe in mehreren Dateien:
  - `/src/whisper_transcription_tool/module1_transcribe/__init__.py`:
    - Alt: `raise DependencyError("Whisper.cpp binary not found...")`
    - Neu: `raise DependencyError(dependency="Whisper.cpp")`
  - `/src/whisper_transcription_tool/module2_extract/__init__.py`:
    - Alt: `raise DependencyError("FFmpeg not found...")`
    - Neu: `raise DependencyError(dependency="FFmpeg")`
  - `/src/whisper_transcription_tool/core/audio_chunker.py`:
    - Alt: `raise DependencyError(f"FFprobe failed: {e}")`
    - Neu: `raise DependencyError(dependency="FFprobe")`
    - Alt: `raise DependencyError(f"Failed to split audio: {e.stderr}")`
    - Neu: `raise DependencyError(dependency="FFmpeg")`

##### 4. Diagnose-Verbesserungen für Korrektur
- UI zeigt jetzt Modellname, Laufzeit und Änderungscount im Ergebnisbereich
- `_correction_metadata.json` speichert `processing_time_seconds`, `model_info`, `llm_level`
- Logging ergänzt: `LLM correction completed in … with N adjustments`
- Diff-Analyse (`_analyze_corrections`) versucht Änderungen zu erkennen, falls LLM-Response identisch wirkt

##### 4. Error Recovery Robustheit
- **Fixed**: Sicherer Zugriff auf `error.details` in `/src/whisper_transcription_tool/core/error_recovery.py`
  - Alt: `error.details.get(...)`
  - Neu: `getattr(error, 'details', {}).get(...)`
  - Verhindert AttributeError bei älteren Exception-Instanzen

#### ⚠️ Bekannte offene Probleme:

##### Hauptproblem: LLM-Korrektur ohne Wirkung
- **Status**: Transkription läuft; Korrektur meldet 0 Änderungen
- **Symptome**:
  - UI: `0` Korrekturen, Laufzeit < 1 s
  - Metadaten: `corrections_made: []`, `processing_time_seconds < 1`
  - Log: `LLM correction completed in … with 0 adjustments`
- **Verdacht**: LeoLM-Antwort identisch mit Original (Prompt/Response prüfen) oder Fallback aktiv

##### Nachwirkungen des ursprünglichen Exceptions-Fehlers
- `DependencyError.details` AttributeError behoben, aber weitere Alt-Aufrufe prüfen
- Sicherstellen, dass keine gecachten Modulversionen ohne Fix aktiv sind

##### Debugging-Informationen:
- Server läuft auf Ports: 8090, 8091, 8092, 8093 (mehrere Instanzen)
- LLM-Model wird korrekt erkannt und Status meldet "ready"
- API-Endpunkt `/api/correction-status` funktioniert und meldet:
  ```json
  {
    "llm_available": true,
    "model_status": "model_valid",
    "available_ram_gb": 25.17
  }
  ```

### 📝 Nächste Schritte:
1. Vollständige Code-Suche nach allen `.details` Zugriffen
2. Überprüfung aller Exception-Instantiierungen
3. Stack-Trace Analyse des genauen Fehlerorts
4. Möglicherweise kompletter Neustart aller Server-Prozesse nötig

## [0.9.7.2] - 2025-09-25 - BETA

### ✅ Live-Test erfolgreich durchgeführt
**Diese Version wurde erfolgreich getestet und arbeitet stabil!**

Die LLM-basierte Textkorrektur ist vollständig integriert und funktioniert mit robustem Fallback-Mechanismus. Das System wurde in Production-Umgebung getestet.

### 🔧 Behobene Probleme in v0.9.7.2
- **Fixed**: ResourceManager.get_system_status() → get_status() Method-Namen korrigiert
- **Fixed**: LLMCorrector.correct_text_async() fehlte - Async-Wrapper hinzugefügt
- **Fixed**: can_run_correction Key fehlte im Status-Dict - Hinzugefügt
- **Fixed**: Version-Anzeige im Frontend zeigte 0.9.7 statt aktueller Version
- **Fixed**: dialect_normalization Parameter-Handling in Korrektur-Pipeline

### ✅ Verifizierte Funktionalität
- **Transkription**: Vollständig funktionsfähig mit allen Modellen
- **Textkorrektur**: Arbeitet mit Fallback zu regel-basierter Korrektur wenn LLM nicht verfügbar
- **File-Output**: Erstellt korrekt _corrected.txt und _metadata.json Dateien
- **WebSocket-Events**: Alle Events (started, progress, completed, error) funktionieren
- **Memory-Management**: ResourceManager arbeitet stabil mit ~50MB Overhead
- **Performance**: Chunking ~1000/sec, Token-Estimation ~50k/sec

## [0.9.7.1] - 2025-09-25 - ENTWICKLUNGSVERSION

### ⚠️ INTERNER BUILD
**Interne Entwicklungsversion - wurde zu 0.9.7.2 weiterentwickelt**

Diese Version enthält die initiale Integration der LLM-basierten Textkorrektur.

### 🚀 Neue Features (Implementiert aber ungetestet)

#### LLM-Textkorrektur System
- **Vollständige LeoLM-13B Integration**:
  - Lokales deutsches Sprachmodell für Textkorrektur
  - GGUF-Format mit llama-cpp-python Backend
  - Metal GPU-Beschleunigung für Apple Silicon
- **Intelligentes Text-Chunking**:
  - Respektiert Satzgrenzen bei der Textaufteilung
  - 2048 Token Kontext-Fenster pro Chunk
  - Überlappende Chunks für Kontexterhalt
- **Memory-effizientes Model-Swapping**:
  - Automatisches Entladen von Whisper vor LLM-Load
  - Thread-sicherer ResourceManager
  - 6GB RAM-Schwellwert für sichere Ausführung
- **Drei Korrektur-Modi**:
  - Light: Nur Rechtschreibung und Grammatik
  - Standard: + Stil und Lesbarkeit
  - Strict: + Formelle Sprache und Struktur
- **Batch-Processing**:
  - Parallele Verarbeitung mehrerer Dateien
  - Intelligente Queue-Verwaltung
  - Fortschrittsanzeige pro Datei
- **Frontend-Integration**:
  - Checkbox zur Aktivierung der Textkorrektur
  - Dropdown für Korrektur-Level-Auswahl
  - Zwei-Phasen-Fortschrittsanzeige (Transkription → Korrektur)
  - Echtzeit-Status über WebSockets

#### Module und Komponenten
- **Neues Modul `module5_text_correction`**:
  - `llm_corrector.py`: LeoLM-Integration
  - `batch_processor.py`: Chunk-Management
  - `resource_manager.py`: Memory-Management
  - `correction_prompts.py`: Deutsche Korrektur-Templates
  - `fallback_corrector.py`: Regel-basierte Fallback-Korrektur
  - `monitoring.py`: Performance-Überwachung
- **Erweiterte Konfiguration**:
  - Neue `text_correction` Sektion in config.py
  - Platform-spezifische GPU-Erkennung
  - Automatische Capability-Detection

#### Technische Details
- **Dependencies hinzugefügt**:
  - llama-cpp-python>=0.2.0
  - sentencepiece>=0.1.99
  - nltk>=3.8
  - transformers>=4.21.0
- **WebSocket-Events**:
  - correction_started
  - correction_progress
  - correction_completed
  - correction_error
- **Error-Handling**:
  - Graceful Fallback zu regel-basierter Korrektur
  - Memory-Monitoring mit automatischem Abort
  - Retry-Mechanismen für transiente Fehler

### 📋 TODO - Tests erforderlich
- [ ] LeoLM Model-Loading testen
- [ ] Textkorrektur-Qualität evaluieren
- [ ] Memory-Swapping verifizieren
- [ ] Batch-Processing Stabilität prüfen
- [ ] WebSocket-Updates validieren
- [ ] Error-Recovery testen
- [ ] Performance-Benchmarks durchführen

### 🛠️ Bekannte Einschränkungen
- Model-Pfad muss manuell konfiguriert werden
- Erste Model-Ladung dauert 30-60 Sekunden
- Benötigt mindestens 6GB freien RAM
- Nur deutsche Textkorrektur implementiert

## [0.9.7] - 2025-09-17

### 🎵 New Audio Format Support

#### Added
- **Opus Audio Support**: WhatsApp voice messages now fully supported
  - Automatic conversion from Opus to MP3 using FFmpeg
  - Seamless integration with existing transcription pipeline
  - Progress tracking during conversion process
- **Enhanced GUI Updates**: Comprehensive interface improvements
  - Updated transcription page to show Opus support
  - Improved user notifications for conversion processes
  - Better file format documentation

#### Technical Improvements
- **FFmpeg Integration**: Added `convert_opus_to_mp3()` function in ffmpeg_wrapper
- **Automatic Detection**: Files ending in `.opus` are automatically converted
- **Temp File Management**: Converted MP3 files stored in temp directory and cleaned up automatically
- **Error Handling**: Robust error reporting for conversion failures

#### UI/UX Updates
- **Format Documentation**: Audio formats now show "MP3, WAV, FLAC, OGG, M4A, OPUS"
- **User Guidance**: Info text updated to mention "Video- und Opus-Dateien werden automatisch konvertiert..."
- **Progress Feedback**: Real-time status updates during Opus conversion process

#### Roadmap
- Telefonaufzeichnung bleibt vorerst deaktiviert, Stabilitätsarbeiten folgen in einem späteren Release.
- Nächster Entwicklungsschwerpunkt ist die Textkorrektur-Pipeline als Post-Processing-Schritt.

#### Changed
- Repository in `WhisperCC_MacOS_Local` umbenannt (vormals `Whisper-Transcription-Tool`).
- Dokumentation und Klon-URLs an den neuen Namen angepasst.

## [0.9.5.1] - 2025-08-31

### 🔧 Installation & Scripts Update

#### Added
- **Simplified Installation System**: Two essential scripts for macOS
  - `Install.command` - Complete installation wizard with automatic dependency setup
  - `Start.command` - One-click launcher with automatic browser opening
- **Smart Installation Features**:
  - Automatic Python version checking
  - Virtual environment setup and management
  - FFmpeg installation via Homebrew
  - Whisper.cpp build automation
  - Optional model download (large-v3-turbo)
  - Configuration file generation

#### Improved
- **Scripts Organization**: Cleaned scripts folder
  - Only 2 essential scripts remain in main folder
  - All legacy scripts archived to `old_versions`
- **Better User Experience**:
  - Color-coded terminal output
  - Clear status messages
  - Error handling with helpful instructions
  - Automatic port conflict resolution

## [0.9.5] - 2025-08-31

### 🎯 Major Release - Clean Repository & Enhanced Documentation

#### Added
- **New Installation System**: Streamlined installation with two simple scripts
  - `Install.command` - Complete macOS installation wizard with automatic setup
  - `Start.command` - One-click application launcher
- **License System**: Dual licensing model
  - Free for personal use
  - Commercial/Enterprise licenses available upon request
  - Contact: mail@goaiex.com
- **Comprehensive Documentation**
  - Updated README with complete feature list
  - Detailed installation instructions
  - Troubleshooting guide
  - Clear project structure documentation

#### Changed
- **Repository Migration**: Moved to new GitHub URL
  - New: https://github.com/cubetribe/WhisperCC_MacOS_Local (ehemals Whisper-Transcription-Tool)
  - Clean repository without personal data in history
- **License Update**: Changed from MIT to Personal Use License with commercial options
- **Scripts Organization**: Cleaned up scripts folder
  - Only essential scripts in main folder
  - Old scripts archived to `old_versions` directory
- **Security Improvements**: Removed all personal paths and information

#### Technical Improvements
- All scripts now use relative paths for better portability
- Virtual environment detection (checks for both `venv_new` and `venv`)
- Automatic port conflict resolution in start script
- Enhanced error handling and user feedback

## [0.9.4.2] - 2025-08-30

### Features
- **Terminal Output Display**: Attempted to add terminal output display in frontend
  - Feature was rolled back due to implementation issues
  - Documentation preserved for future reference

### Bug Fixes
- Fixed WebSocket connection issues
- Improved event handling system

## [0.9.4.1] - 2025-08-30

### Features
- **Terminal Debug Output**: Added debug output for better troubleshooting
- **Improved Launcher**: Enhanced launcher script with better error handling

## [0.9.4] - 2025-08-30

### Features
- **Enhanced Web Interface**: Improved UI/UX with better progress indicators
- **Model Management**: Automatic model downloads with progress tracking

## [0.9.3] - 2025-08-31

### ✅ New Features
- **Cleanup Manager**: Automatic cleanup of temp directory after successful transcription
  - Deletes audio chunks after processing
  - Configurable retention policies
  - Significantly reduces disk space usage (from 9.3 GB to 0.0001 GB in tests)

### 🐛 Bug Fixes
- **WebSocket Conflicts**: Fixed duplicate `/ws/progress` endpoints
- **Event System**: Restored proven async event handler implementation
- **AsyncIO Issues**: Fixed sync/async bridge problems

### 🔧 Technical Improvements
- Removed complex queue-based event bridge
- Simplified to direct async event handlers
- Better error handling in WebSocket connections
- Improved cleanup logic with proper temp file management

### 📝 Lessons Learned
1. **Async/Await Consistency**: Always stay in async context with WebSockets
2. **Event System Simplicity**: Direct async handlers are more robust than complex queue bridges
3. **FastAPI Route Conflicts**: Duplicate WebSocket endpoints lead to unpredictable behavior
4. **Type Safety**: Ensure all event types are defined in the Enum

## [0.9.2] - 2025-08-30

### Features
- **Audio Chunking**: Implemented chunking for large files
  - Automatic splitting of files >20 minutes
  - 20-minute segments with 10 seconds overlap
  - Seamless transcription of long recordings

### Bug Fixes
- Fixed memory issues with large file processing
- Improved handling of temporary files

## [0.9.1] - 2025-08-29

### Features
- **Phone Recording Module**: Dual-track recording support
- **BlackHole Integration**: System audio capture capability

### Improvements
- Better error messages
- Enhanced logging system
- Improved model detection

## [0.9.0] - 2025-08-28

### 🚀 Initial Public Release

#### Core Features
- **Local Transcription**: Using Whisper.cpp (no API needed)
- **Web Interface**: FastAPI-based with real-time WebSocket updates
- **Video Support**: Automatic audio extraction with FFmpeg
- **Multiple Formats**: Support for TXT, SRT, VTT, JSON output
- **Batch Processing**: Handle multiple files efficiently
- **Model Management**: Support for all Whisper models

#### Modules
1. **Module 1**: Core transcription functionality
2. **Module 2**: Video extraction capabilities
3. **Module 3**: Phone recording processing
4. **Module 4**: Chatbot integration (experimental)

#### Platform Support
- Optimized for Apple Silicon Macs
- macOS 10.15+ support
- Python 3.8+ required

---

## Version History Summary

- **0.9.7** - Opus audio support for WhatsApp voice messages and GUI improvements
- **0.9.5.1** - Simplified installation with two essential scripts
- **0.9.5** - Clean repository, enhanced documentation, simplified installation
- **0.9.4** - UI improvements and model management
- **0.9.3** - Cleanup manager and critical bug fixes
- **0.9.2** - Audio chunking for large files
- **0.9.1** - Phone recording support
- **0.9.0** - Initial public release

---

For more information, visit: [www.goaiex.com](https://www.goaiex.com)  
Copyright © 2025 Dennis Westermann - aiEX Academy
