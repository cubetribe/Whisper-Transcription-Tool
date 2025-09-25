# 📝 LLM Textkorrektur mit LeoLM - Kompletter Benutzerhandbuch

**Vollständige Anleitung für die automatische Textkorrektur mit lokalem KI-Modell**

---

## 🎯 Überblick

Das Whisper Transcription Tool bietet eine fortschrittliche **lokale Textkorrektur-Pipeline** mit dem LeoLM-13B Modell von Hessian.AI. Diese Funktion ermöglicht es, transkribierte deutsche Texte automatisch zu korrigieren und zu verbessern - **vollständig offline und ohne Cloud-Abhängigkeiten**.

### ✨ Hauptmerkmale

- **🔒 100% Lokal**: Keine Internetverbindung erforderlich, alle Daten bleiben auf Ihrem Mac
- **🧠 LeoLM-13B**: Speziell für deutsche Sprache optimiertes Large Language Model
- **⚡ Metal-Acceleration**: Optimiert für Apple Silicon (M1/M2/M3) mit GPU-Beschleunigung
- **🎨 Drei Korrekturstufen**: Flexibel anpassbar je nach Anwendungsfall
- **🧩 Intelligente Textaufteilung**: Automatische Verarbeitung großer Texte in sinnvollen Blöcken
- **⏱️ Echtzeit-Feedback**: Fortschrittsanzeige während der Korrektur

---

## 📋 System-Anforderungen

### Hardware-Mindestanforderungen

| Komponente | Minimum | Empfohlen |
|------------|---------|-----------|
| **RAM** | 6GB frei | 8GB+ frei |
| **Prozessor** | Apple Silicon (M1/M2/M3) | M2 Pro oder besser |
| **Speicher** | 8GB frei | 15GB+ frei |
| **GPU** | Integrierte Metal-GPU | Alle Apple Silicon GPUs unterstützt |

### Software-Anforderungen

- **Betriebssystem**: macOS 12.0+ (Monterey oder neuer)
- **Python**: Version 3.8 oder höher
- **Xcode Command Line Tools**: Für Metal-Unterstützung
- **LM Studio**: Für einfache Modell-Verwaltung (empfohlen)

---

## 🚀 Installation und Setup

### Schritt 1: LeoLM Modell herunterladen

#### Option A: Mit LM Studio (Empfohlen)

1. **LM Studio installieren**:
   ```bash
   # Download von: https://lmstudio.ai/
   # LM Studio öffnen
   ```

2. **Modell suchen und herunterladen**:
   - Suche nach: `LeoLM-hesseianai-13b-chat`
   - Wähle Version: `mradermacher/LeoLM-hesseianai-13b-chat-GGUF`
   - Quantisierung: **Q4_K_M** (empfohlene Balance zwischen Qualität und Performance)
   - Download-Größe: ~7.5GB

3. **Standard-Pfad überprüfen**:
   ```bash
   ls ~/.lmstudio/models/mradermacher/LeoLM-hesseianai-13b-chat-GGUF/
   # Sollte die .gguf Datei anzeigen
   ```

#### Option B: Manueller Download

1. **Modell-Repository klonen**:
   ```bash
   git clone https://huggingface.co/mradermacher/LeoLM-hesseianai-13b-chat-GGUF
   ```

2. **Gewünschte Quantisierung herunterladen**:
   ```bash
   cd LeoLM-hesseianai-13b-chat-GGUF
   wget https://huggingface.co/mradermacher/LeoLM-hesseianai-13b-chat-GGUF/resolve/main/LeoLM-hesseianai-13b-chat.Q4_K_M.gguf
   ```

### Schritt 2: Python-Dependencies installieren

```bash
# Virtuelle Umgebung aktivieren
source venv_new/bin/activate

# LLM-Korrektur Dependencies installieren
pip install llama-cpp-python>=0.2.0
pip install sentencepiece>=0.1.99
pip install nltk>=3.8
pip install transformers>=4.21.0

# NLTK Daten herunterladen (für Satz-Segmentierung)
python -c "import nltk; nltk.download('punkt')"
```

### Schritt 3: Konfiguration

1. **Basis-Konfigurationsdatei erstellen**:
   ```bash
   # Konfig-Datei bearbeiten oder erstellen
   nano ~/.whisper_tool.json
   ```

2. **Text-Korrektur Konfiguration hinzufügen**:
   ```json
   {
     "text_correction": {
       "enabled": true,
       "model_path": "~/.lmstudio/models/mradermacher/LeoLM-hesseianai-13b-chat-GGUF/LeoLM-hesseianai-13b-chat.Q4_K_M.gguf",
       "context_length": 2048,
       "correction_level": "standard",
       "temperature": 0.3,
       "max_tokens": 512,
       "batch_size": 4,
       "enable_chunking": true,
       "overlap_sentences": 1
     }
   }
   ```

3. **Pfad-Validierung**:
   ```bash
   # Prüfen ob Modell-Datei existiert
   python -c "
   import json
   from pathlib import Path

   with open(Path.home() / '.whisper_tool.json') as f:
       config = json.load(f)

   model_path = Path(config['text_correction']['model_path']).expanduser()
   print(f'Modell gefunden: {model_path.exists()}')
   print(f'Pfad: {model_path}')
   print(f'Größe: {model_path.stat().st_size / 1024**3:.1f} GB' if model_path.exists() else 'Datei nicht gefunden')
   "
   ```

---

## 💻 Verwendung

### Web-Interface (Empfohlen für Einsteiger)

1. **Server starten**:
   ```bash
   cd /path/to/whisper_clean
   ./start_server.sh
   ```

2. **Browser öffnen**: http://localhost:8090

3. **Transkription mit Korrektur**:
   - Audio-/Video-Datei auswählen
   - **"Text Correction" aktivieren**
   - Korrekturstufe wählen (Basic/Advanced/Formal)
   - Transkription starten
   - Text wird automatisch korrigiert

4. **Nur Korrektur ohne Transkription**:
   - Zur "Models" Seite navigieren
   - "Text Correction" Bereich
   - Text eingeben oder Datei hochladen
   - Korrekturstufe wählen
   - "Correct Text" klicken

### Command Line Interface

#### Grundlegende Befehle

```bash
# Einfache Textkorrektur
whisper-tool correct "Das ist ein text mit viele fehler."

# Mit spezifischer Korrekturstufe
whisper-tool correct --level advanced "Dein Text hier."

# Datei korrigieren
whisper-tool correct --input input.txt --output corrected.txt

# Mit benutzerdefinierten Parametern
whisper-tool correct --level formal --temperature 0.2 --input text.txt
```

#### Erweiterte Optionen

```bash
# Alle verfügbaren Optionen anzeigen
whisper-tool correct --help

# Mit ausführlicher Ausgabe
whisper-tool correct --verbose "Text zum korrigieren."

# Korrektur mit Batch-Verarbeitung für große Dateien
whisper-tool correct --batch-size 8 --input large_text.txt

# Trocken-Lauf (ohne tatsächliche Korrektur)
whisper-tool correct --dry-run --input text.txt
```

### Python API

#### Einfache Verwendung

```python
from whisper_transcription_tool.module5_text_correction import LLMCorrector

# Context Manager für automatisches Modell-Management
with LLMCorrector() as corrector:
    original_text = "Das ist ein text mit viele fehler und schlecht grammatik."

    corrected = corrector.correct_text(
        text=original_text,
        correction_level="advanced",
        language="de"
    )

    print("Original:", original_text)
    print("Korrigiert:", corrected)
```

#### Erweiterte API-Verwendung

```python
import asyncio
from whisper_transcription_tool.module5_text_correction import (
    LLMCorrector,
    BatchProcessor
)

async def advanced_correction_example():
    # Manuelle Modell-Konfiguration
    corrector = LLMCorrector(
        model_path="~/.lmstudio/models/.../model.gguf",
        context_length=4096  # Größerer Context für längere Texte
    )

    # Modell laden
    if not corrector.load_model():
        raise RuntimeError("Modell konnte nicht geladen werden")

    try:
        # Lange Texte mit Batch-Verarbeitung
        long_text = "Sehr langer Text hier..." * 100

        # Intelligente Textaufteilung
        processor = BatchProcessor(
            max_context_length=2048,
            overlap_sentences=2
        )

        chunks = processor.chunk_text(long_text)
        print(f"Text in {len(chunks)} Chunks aufgeteilt")

        # Korrektur-Funktion definieren
        def correction_function(chunk_text: str) -> str:
            return corrector.correct_text(
                chunk_text,
                correction_level="advanced"
            )

        # Asynchrone Verarbeitung mit Fortschrittsanzeige
        def progress_callback(current, total, status):
            percentage = (current / total) * 100
            print(f"Fortschritt: {percentage:.1f}% ({current}/{total}) - {status}")

        # Chunks verarbeiten
        result = await processor.process_chunks_async(
            chunks,
            correction_function,
            progress_callback=progress_callback
        )

        print("\nKorrektur abgeschlossen!")
        print(f"Erfolgreiche Chunks: {len([r for r in result if r.success])}")
        print(f"Fehlgeschlagene Chunks: {len([r for r in result if not r.success])}")

        # Finalen Text zusammenfügen
        corrected_text = " ".join([r.corrected_text for r in result])
        return corrected_text

    finally:
        # Modell wieder freigeben
        corrector.unload_model()

# Ausführung
corrected_text = asyncio.run(advanced_correction_example())
```

---

## 🎨 Korrekturstufen im Detail

### Basic Level
**Anwendungsfall**: Grundlegende Korrektur für alltägliche Texte

**Was wird korrigiert**:
- ✅ Rechtschreibfehler
- ✅ Grundlegende Grammatikfehler
- ✅ Zeichensetzung (Kommas, Punkte)
- ✅ Groß-/Kleinschreibung

**Beispiel**:
```
Eingabe:  "das ist ein test mit viele fehler und schlechte grammar."
Ausgabe:  "Das ist ein Test mit vielen Fehlern und schlechter Grammatik."
```

### Advanced Level
**Anwendungsfall**: Professionelle Texte, Artikel, Berichte

**Was wird korrigiert**:
- ✅ Alles aus "Basic"
- ✅ Komplexe Grammatik und Satzbau
- ✅ Stil-Optimierungen
- ✅ Verbesserte Lesbarkeit
- ✅ Konsistente Terminologie
- ✅ Füllwörter reduzieren

**Beispiel**:
```
Eingabe:  "Also, das Ergebnis war halt so, dass wir eigentlich ziemlich gut abgeschnitten haben."
Ausgabe:  "Das Ergebnis zeigt, dass wir sehr gut abgeschnitten haben."
```

### Formal Level
**Anwendungsfall**: Offizielle Dokumente, Geschäftskommunikation

**Was wird korrigiert**:
- ✅ Alles aus "Advanced"
- ✅ Formelle Sprache und Stil
- ✅ Professionelle Formulierungen
- ✅ Korrekte Anrede und Höflichkeitsformen
- ✅ Präzise und eindeutige Ausdrücke
- ✅ Geschäftstaugliche Terminologie

**Beispiel**:
```
Eingabe:  "Hi, können Sie mir mal schnell sagen, ob das okay ist?"
Ausgabe:  "Sehr geehrte Damen und Herren, könnten Sie mir bitte mitteilen, ob dies Ihren Vorstellungen entspricht?"
```

---

## 🔧 Konfigurationsoptionen im Detail

### Vollständige Konfigurationsdatei

```json
{
  "text_correction": {
    "enabled": true,

    // Modell-Einstellungen
    "model_path": "~/.lmstudio/models/mradermacher/LeoLM-hesseianai-13b-chat-GGUF/LeoLM-hesseianai-13b-chat.Q4_K_M.gguf",
    "context_length": 2048,

    // Korrektur-Parameter
    "correction_level": "standard",
    "temperature": 0.3,
    "max_tokens": 512,
    "top_p": 0.9,
    "repeat_penalty": 1.1,

    // Performance-Einstellungen
    "n_gpu_layers": -1,
    "n_threads": 8,
    "batch_size": 4,
    "use_mlock": true,
    "use_mmap": true,

    // Text-Verarbeitung
    "enable_chunking": true,
    "max_chunk_size": 1600,
    "overlap_sentences": 1,
    "tokenizer_strategy": "nltk",

    // Timeout und Retry
    "timeout_seconds": 120,
    "max_retries": 2,
    "retry_delay": 5.0,

    // Logging und Debugging
    "verbose": false,
    "log_corrections": true,
    "save_intermediate_results": false
  }
}
```

### Parameter-Beschreibungen

#### Modell-Einstellungen

| Parameter | Standard | Beschreibung |
|-----------|----------|--------------|
| `model_path` | LM Studio Standard | Pfad zur .gguf Modell-Datei |
| `context_length` | 2048 | Maximale Token-Anzahl für Kontext |
| `n_gpu_layers` | -1 | GPU-Layer (-1 = alle verfügbaren) |
| `n_threads` | Auto | CPU-Threads für Verarbeitung |

#### Korrektur-Parameter

| Parameter | Standard | Beschreibung |
|-----------|----------|--------------|
| `correction_level` | "standard" | basic/advanced/formal |
| `temperature` | 0.3 | Kreativität (0.0-1.0, niedrig = konsistenter) |
| `max_tokens` | 512 | Maximale Antwort-Länge |
| `top_p` | 0.9 | Nucleus Sampling Parameter |
| `repeat_penalty` | 1.1 | Wiederholungs-Vermeidung |

#### Performance-Einstellungen

| Parameter | Standard | Beschreibung |
|-----------|----------|--------------|
| `batch_size` | 4 | Parallel verarbeitete Chunks |
| `use_mlock` | true | Modell im RAM sperren |
| `use_mmap` | true | Memory Mapping verwenden |
| `timeout_seconds` | 120 | Timeout pro Korrektur-Anfrage |

---

## ⚡ Performance-Optimierung

### Hardware-spezifische Optimierungen

#### M1 Base (8GB RAM)
```json
{
  "text_correction": {
    "context_length": 1024,
    "batch_size": 2,
    "max_chunk_size": 800,
    "n_threads": 4
  }
}
```

#### M2 Pro (16GB+ RAM)
```json
{
  "text_correction": {
    "context_length": 4096,
    "batch_size": 6,
    "max_chunk_size": 2000,
    "n_threads": 8
  }
}
```

#### M3 Max (32GB+ RAM)
```json
{
  "text_correction": {
    "context_length": 8192,
    "batch_size": 8,
    "max_chunk_size": 4000,
    "n_threads": 12
  }
}
```

### Performance-Monitoring

```python
from whisper_transcription_tool.module5_text_correction import LLMCorrector
import time
import psutil

def monitor_correction_performance(text: str):
    # System-Ressourcen vor Start messen
    start_memory = psutil.virtual_memory().used / 1024**3
    start_time = time.time()

    with LLMCorrector() as corrector:
        model_info = corrector.get_model_info()
        print(f"Modell geladen: {model_info}")

        # Korrektur durchführen
        corrected = corrector.correct_text(text, correction_level="advanced")

        # Performance-Metriken
        end_time = time.time()
        end_memory = psutil.virtual_memory().used / 1024**3

        processing_time = end_time - start_time
        memory_usage = end_memory - start_memory
        chars_per_second = len(text) / processing_time

        print(f"\n📊 Performance-Statistiken:")
        print(f"⏱️  Verarbeitungszeit: {processing_time:.2f}s")
        print(f"💾 Speicher-Verbrauch: {memory_usage:.2f}GB")
        print(f"🏃 Zeichen/Sekunde: {chars_per_second:.1f}")
        print(f"📝 Original-Länge: {len(text)} Zeichen")
        print(f"📝 Korrigiert-Länge: {len(corrected)} Zeichen")

        return corrected

# Verwendung
text = "Das ist ein langer text mit viele fehler..." * 20
corrected = monitor_correction_performance(text)
```

---

## 🛠️ Erweiterte Features

### Batch-Verarbeitung großer Dateien

```python
import os
from pathlib import Path
from whisper_transcription_tool.module5_text_correction import BatchProcessor, LLMCorrector

def process_directory_batch(input_dir: str, output_dir: str):
    """Alle .txt Dateien in einem Verzeichnis korrigieren."""

    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    txt_files = list(input_path.glob("*.txt"))
    print(f"Gefundene Dateien: {len(txt_files)}")

    with LLMCorrector() as corrector:
        processor = BatchProcessor(
            max_context_length=2048,
            overlap_sentences=1
        )

        for file_path in txt_files:
            print(f"\n📄 Verarbeite: {file_path.name}")

            # Datei lesen
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()

            # Text chunking
            chunks = processor.chunk_text(text)
            print(f"   Chunks: {len(chunks)}")

            # Korrektur-Funktion
            def correct_chunk(chunk_text: str) -> str:
                return corrector.correct_text(
                    chunk_text,
                    correction_level="advanced"
                )

            # Verarbeitung mit Progress
            def progress(current, total, status):
                percent = (current / total) * 100
                print(f"   Progress: {percent:.1f}% ({current}/{total})")

            # Synchrone Verarbeitung (für Stabilität)
            result = processor.process_chunks_sync(
                chunks,
                correct_chunk,
                progress_callback=progress
            )

            # Ergebnis speichern
            output_file = output_path / f"corrected_{file_path.name}"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(result)

            print(f"   ✅ Gespeichert: {output_file}")

# Verwendung
process_directory_batch("./input_texts/", "./corrected_texts/")
```

### Integration in bestehende Workflows

```python
def transcribe_and_correct_pipeline(audio_file: str) -> dict:
    """Vollständige Pipeline: Transkription → Korrektur."""

    from whisper_transcription_tool.module1_transcribe import WhisperWrapper
    from whisper_transcription_tool.module5_text_correction import LLMCorrector

    results = {}

    # 1. Transkription
    print("🎤 Starte Transkription...")
    with WhisperWrapper() as transcriber:
        transcription = transcriber.transcribe(audio_file)
        results['original_transcription'] = transcription['text']

    print(f"📝 Transkription: {len(results['original_transcription'])} Zeichen")

    # 2. Textkorrektur
    print("✏️  Starte Textkorrektur...")
    with LLMCorrector() as corrector:
        corrected = corrector.correct_text(
            results['original_transcription'],
            correction_level="advanced"
        )
        results['corrected_transcription'] = corrected

    print(f"✨ Korrigiert: {len(results['corrected_transcription'])} Zeichen")

    # 3. Vergleich und Metriken
    original_words = len(results['original_transcription'].split())
    corrected_words = len(results['corrected_transcription'].split())

    results['metrics'] = {
        'original_word_count': original_words,
        'corrected_word_count': corrected_words,
        'word_change_ratio': corrected_words / original_words if original_words > 0 else 0,
        'character_change': len(results['corrected_transcription']) - len(results['original_transcription'])
    }

    return results

# Verwendung
result = transcribe_and_correct_pipeline("recording.mp3")
print("\n📊 Ergebnisse:")
print(f"Original: {result['original_transcription'][:100]}...")
print(f"Korrigiert: {result['corrected_transcription'][:100]}...")
print(f"Metriken: {result['metrics']}")
```

---

## 🔍 Qualitätskontrolle und Testing

### Korrektur-Qualität bewerten

```python
def evaluate_correction_quality(original: str, corrected: str) -> dict:
    """Bewerte die Qualität einer Textkorrektur."""

    import re
    from difflib import SequenceMatcher

    # Basis-Metriken
    original_words = original.lower().split()
    corrected_words = corrected.lower().split()

    # Ähnlichkeit berechnen
    similarity = SequenceMatcher(None, original, corrected).ratio()

    # Wort-Änderungen
    word_changes = abs(len(corrected_words) - len(original_words))

    # Rechtschreibfehler-Schätzung (vereinfacht)
    def count_potential_errors(text):
        # Einfache Heuristiken für typische Fehler
        errors = 0
        errors += len(re.findall(r'\b\w*[äöü]\w*[aou]\w*\b', text))  # Umlaut-Fehler
        errors += len(re.findall(r'\b[a-z]+\s+[A-Z]', text))  # Groß-/Kleinschreibung
        errors += len(re.findall(r'[a-zA-Z]{2,}\s*[.!?]', text))  # Fehlende Leerzeichen
        return errors

    original_errors = count_potential_errors(original)
    corrected_errors = count_potential_errors(corrected)

    quality_metrics = {
        'similarity_ratio': round(similarity, 3),
        'word_change_count': word_changes,
        'word_change_percentage': round(word_changes / len(original_words) * 100, 1),
        'estimated_original_errors': original_errors,
        'estimated_corrected_errors': corrected_errors,
        'estimated_fixes': max(0, original_errors - corrected_errors),
        'quality_score': round(similarity * (1 + max(0, original_errors - corrected_errors) / max(1, original_errors)), 3)
    }

    return quality_metrics

# Test-Beispiele
test_cases = [
    "Das ist ein test mit viele fehler und schlecht grammar.",
    "Ich bin gestern in die stadt gegangen und hab eingekauft.",
    "der bericht zeigt das die verkaufszahlen gestiegen sind.",
]

with LLMCorrector() as corrector:
    for test_text in test_cases:
        corrected = corrector.correct_text(test_text, correction_level="advanced")
        quality = evaluate_correction_quality(test_text, corrected)

        print(f"\n📝 Original: {test_text}")
        print(f"✨ Korrigiert: {corrected}")
        print(f"📊 Qualität: {quality}")
```

### A/B Testing verschiedener Korrekturstufen

```python
def compare_correction_levels(text: str) -> dict:
    """Vergleiche alle Korrekturstufen für einen Text."""

    results = {}

    with LLMCorrector() as corrector:
        for level in ['basic', 'advanced', 'formal']:
            print(f"🔧 Teste Level: {level}")

            start_time = time.time()
            corrected = corrector.correct_text(text, correction_level=level)
            processing_time = time.time() - start_time

            quality = evaluate_correction_quality(text, corrected)

            results[level] = {
                'corrected_text': corrected,
                'processing_time': processing_time,
                'quality_metrics': quality
            }

    return results

# Vergleichs-Test
test_text = "Das ergebnis der studie zeigt das sehr viele fehler in automatisch transkribierte texte sind und das eine korrektur sinnvoll ist."

comparison = compare_correction_levels(test_text)

print("\n🔍 Vergleich der Korrekturstufen:")
for level, data in comparison.items():
    print(f"\n{level.upper()}:")
    print(f"  Text: {data['corrected_text']}")
    print(f"  Zeit: {data['processing_time']:.2f}s")
    print(f"  Qualität: {data['quality_metrics']['quality_score']}")
```

---

## 🌟 Best Practices

### 1. Speicher-Management

```python
# ✅ Gut: Context Manager verwenden
with LLMCorrector() as corrector:
    result = corrector.correct_text(text)

# ❌ Vermeiden: Modell nicht explizit freigeben
corrector = LLMCorrector()
corrector.load_model()
# ... vergessen corrector.unload_model() zu rufen
```

### 2. Batch-Verarbeitung optimieren

```python
# ✅ Gut: Sinnvolle Chunk-Größen
processor = BatchProcessor(
    max_context_length=1600,  # Lässt Platz für Prompt
    overlap_sentences=1       # Minimal notwendiger Overlap
)

# ❌ Vermeiden: Zu kleine/große Chunks
processor = BatchProcessor(
    max_context_length=8192,  # Kann Memory-Probleme verursachen
    overlap_sentences=5       # Unnötig hoher Overhead
)
```

### 3. Fehler-Behandlung

```python
# ✅ Gut: Robuste Fehlerbehandlung
def safe_correction(text: str, max_retries: int = 3) -> str:
    for attempt in range(max_retries):
        try:
            with LLMCorrector() as corrector:
                return corrector.correct_text(text)
        except Exception as e:
            logger.warning(f"Korrektur-Versuch {attempt + 1} fehlgeschlagen: {e}")
            if attempt == max_retries - 1:
                logger.error("Alle Korrektur-Versuche fehlgeschlagen, gebe Originaltext zurück")
                return text
            time.sleep(2 ** attempt)  # Exponential backoff
    return text
```

### 4. Performance-Monitoring

```python
# ✅ Gut: Performance überwachen
def monitored_correction(text: str) -> tuple[str, dict]:
    start_memory = psutil.virtual_memory().used
    start_time = time.time()

    try:
        with LLMCorrector() as corrector:
            result = corrector.correct_text(text)

            metrics = {
                'processing_time': time.time() - start_time,
                'memory_used': (psutil.virtual_memory().used - start_memory) / 1024**2,  # MB
                'chars_per_second': len(text) / (time.time() - start_time),
                'success': True
            }

            return result, metrics

    except Exception as e:
        metrics = {
            'processing_time': time.time() - start_time,
            'error': str(e),
            'success': False
        }
        return text, metrics  # Fallback auf Original
```

---

## 🎯 Anwendungsfälle und Beispiele

### 1. Podcast-Transkription korrigieren

```python
def correct_podcast_transcription(audio_file: str, speaker_names: list = None):
    """Korrigiere Podcast-Transkription mit Sprecher-Erkennung."""

    # Transkription mit Timestamps
    from whisper_transcription_tool.module1_transcribe import WhisperWrapper

    with WhisperWrapper() as transcriber:
        result = transcriber.transcribe(
            audio_file,
            output_format="segments"  # Mit Zeitstempel
        )

    corrected_segments = []

    with LLMCorrector() as corrector:
        for segment in result['segments']:
            original_text = segment['text']

            # Korrektur mit Formal-Level für professionelle Podcasts
            corrected_text = corrector.correct_text(
                original_text,
                correction_level="formal"
            )

            corrected_segments.append({
                'start': segment['start'],
                'end': segment['end'],
                'original': original_text,
                'corrected': corrected_text,
                'speaker': speaker_names[segment.get('speaker', 0)] if speaker_names else None
            })

    return corrected_segments
```

### 2. Medizinische Diktate

```python
def correct_medical_dictation(text: str) -> str:
    """Spezialisierte Korrektur für medizinische Texte."""

    # Medizinische Fachbegriffe vorbehandeln
    medical_terms = {
        'anamnese': 'Anamnese',
        'diagnose': 'Diagnose',
        'therapie': 'Therapie',
        'röntgen': 'Röntgen',
        'ekg': 'EKG',
        'mrt': 'MRT'
    }

    # Fachbegriffe schützen
    protected_text = text
    for term, replacement in medical_terms.items():
        protected_text = re.sub(
            f r'\b{term}\b',
            replacement,
            protected_text,
            flags=re.IGNORECASE
        )

    with LLMCorrector() as corrector:
        corrected = corrector.correct_text(
            protected_text,
            correction_level="formal"  # Formelle Sprache für medizinische Dokumentation
        )

    return corrected
```

### 3. Interview-Transkripte

```python
def correct_interview_transcript(text: str, preserve_colloquial: bool = True) -> str:
    """Korrigiere Interview-Transkript unter Beibehaltung des Gesprächsstils."""

    correction_level = "basic" if preserve_colloquial else "advanced"

    with LLMCorrector() as corrector:
        # Custom prompt für Interviews
        if preserve_colloquial:
            # Temporär vereinfachte Prompts für natürlicheren Stil
            original_prompts = corrector.CORRECTION_PROMPTS

            corrector.CORRECTION_PROMPTS = {
                "basic": {
                    "de": """Korrigiere den folgenden Interview-Text:
- Behebe nur offensichtliche Rechtschreibfehler
- Korrigiere grundlegende Grammatik
- BEHALTE den natürlichen Gesprächsstil bei
- ENTFERNE keine Füllwörter oder Umgangssprache

Text: {text}

Korrigierter Text:"""
                }
            }

        corrected = corrector.correct_text(text, correction_level=correction_level)

        # Originale Prompts wiederherstellen
        if preserve_colloquial:
            corrector.CORRECTION_PROMPTS = original_prompts

    return corrected
```

---

## 📚 Weiterführende Ressourcen

### Offizielle Dokumentation und Quellen

- **LeoLM Model**: [Hessian.AI LeoLM Repository](https://huggingface.co/LeoLM)
- **llama-cpp-python**: [GitHub Repository](https://github.com/abetlen/llama-cpp-python)
- **Metal Performance**: [Apple Metal Documentation](https://developer.apple.com/metal/)
- **GGUF Format**: [GGML Documentation](https://github.com/ggerganov/ggml)

### Community und Support

- **LM Studio Community**: [Discord](https://discord.com/invite/aPQfnNkxGC)
- **Whisper Tool Issues**: [GitHub Issues](https://github.com/cubetribe/WhisperCC_MacOS_Local/issues)
- **Hessian.AI**: [Offizielle Website](https://hessian.ai/)

### Weiterführende Tutorials

1. **LLM Fine-tuning für deutsche Texte**
2. **Custom Prompt Engineering**
3. **Performance Benchmarking**
4. **Integration in andere Python-Workflows**

---

## 📄 Lizenz und Haftungsausschluss

### LeoLM Lizenz
Das LeoLM-Modell ist unter der **MIT License** von Hessian.AI verfügbar:
- ✅ Kommerzielle Nutzung erlaubt
- ✅ Modifikation und Redistribution erlaubt
- ✅ Private Nutzung erlaubt
- ❗ Ohne Gewährleistung

### Whisper Tool Lizenz
Dieses Tool ist für **persönliche Nutzung** kostenlos verfügbar.
- Kommerzielle Lizenz auf Anfrage: mail@goaiex.com

### Haftungsausschluss
- Textkorrektur-Ergebnisse sind **nicht garantiert**
- Prüfen Sie wichtige Texte **manuell nach**
- Keine Haftung für **inkorrekte Korrekturen**
- Verwenden Sie das Tool **auf eigenes Risiko**

---

**Version**: 1.0.0 | **Datum**: September 2025
**Erstellt von**: aiEX Academy | **Website**: [www.goaiex.com](https://www.goaiex.com)

Dieses Handbuch wird kontinuierlich aktualisiert. Feedback und Verbesserungsvorschläge sind willkommen!