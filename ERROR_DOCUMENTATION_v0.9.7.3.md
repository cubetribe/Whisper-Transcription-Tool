# Fehler-Dokumentation v0.9.7.3
**Datum**: 2025-09-25
**Status**: UNGELÖST
**Kritikalität**: HOCH

## Zusammenfassung

Die Transkription schlug zunächst mit einem `AttributeError` beim Zugriff auf `DependencyError.details` fehl. Nach Hotfixes läuft die Transkription wieder an, jedoch liefert die LLM-Textkorrektur weiterhin **keine Änderungen (0 Korrekturen, Laufzeit < 1 s)**. Der Fehler gilt daher weiterhin als ungelöst.

## Fehlerbeschreibung

### Hauptfehler
```
Error transcribing audio: 'DependencyError' object has no attribute 'details'
```

### Kontext
- **Zeitpunkt**: Tritt auf direkt nach Audio-Upload, bevor Whisper.cpp aufgerufen wird
- **Betroffene Funktion**: Transkription (Module 1)
- **Textkorrektur-Status**: LLM ist verfügbar und korrekt konfiguriert
- **Server-Logs**: Zeigen keinen vollständigen Stack-Trace

### Aktueller Zustand nach Hotfix
- `DependencyError.details`-Zugriffe wurden gehärtet, Transkription startet wieder
- UI zeigt neue Zusammenfassung (Modell, Dauer, Änderungscount) – Werte bleiben allerdings `0`
- `_correction_metadata.json` enthält `method: "llm"`, aber `corrections_made: []` und `processing_time_seconds < 1`
- Logausgabe: `LLM correction completed in 0.34s with 0 adjustments (model=...)`
- Verdacht: LLM wird weiterhin nicht korrekt angesprochen → Fallback oder Prompt-Roundtrip liefert identischen Text

### Reproduktion
1. Server starten: `python -m src.whisper_transcription_tool.main web --port 8093`
2. Browser öffnen: http://localhost:8093/transcribe
3. Audio-Datei hochladen (beliebiges Format)
4. "Transkribieren" klicken
5. Fehler erscheint sofort

## Technische Analyse

### Problem-Historie

#### Ursprüngliches Problem
- LeoLM-13B Modell hatte Tensor-Dimension-Mismatch
- Fehler: `tensor 'token_embd.weight' has wrong shape; expected 5120, 32007, got 5120, 32128`
- Lösung: Alternative Modell `em_german_leo_mistral.Q4_K_M.gguf` heruntergeladen

#### DependencyError Constructor Problem
Die `DependencyError` Klasse wurde mit neuer Signatur definiert:
```python
def __init__(self, dependency: str, **kwargs):
```

Aber an vielen Stellen noch mit alter Signatur aufgerufen:
```python
raise DependencyError("Error message")  # Alt
raise DependencyError(dependency="Name")  # Neu
```

### Behobene Stellen

1. **module1_transcribe/__init__.py:188**
   - Alt: `raise DependencyError("Whisper.cpp binary not found...")`
   - Neu: `raise DependencyError(dependency="Whisper.cpp")`

2. **module2_extract/__init__.py:79**
   - Alt: `raise DependencyError("FFmpeg not found...")`
   - Neu: `raise DependencyError(dependency="FFmpeg")`

3. **core/audio_chunker.py:83 & 208**
   - Alt: `raise DependencyError(f"FFprobe failed: {e}")`
   - Neu: `raise DependencyError(dependency="FFprobe")`

4. **core/error_recovery.py**
   - Alt: `error.details.get(...)`
   - Neu: `getattr(error, 'details', {}).get(...)`

### Noch zu untersuchen

1. **Mögliche versteckte `.details` Zugriffe**
   ```bash
   grep -r "\.details" src/ --include="*.py" | grep -v "getattr"
   ```

2. **Import-Cache-Probleme**
   - Python könnte alte Klassendefinitionen gecacht haben
   - Lösung: Alle Server-Prozesse komplett beenden und neu starten

3. **Weitere DependencyError Instanziierungen**
   - Möglicherweise in Third-Party Code oder dynamisch generiert

4. **Exception-Weitergabe**
   - Fehler könnte von einem anderen Modul kommen und nur weitergereicht werden

5. **LLM-Korrektur greift nicht**
   - Prüfen ob `LLMCorrector` tatsächlich Antwort des Modells erhält
   - Logging erweitern (Prompt/Response-Ausschnitte, Fallback-Indikator)
   - Sicherstellen, dass kein regelbasierter Fallback (`method: "rule_based"`) aktiv ist

## Workaround

### Temporäre Lösung (nicht implementiert)
```python
# In core/exceptions.py
class DependencyError(WhisperToolError):
    def __init__(self, *args, **kwargs):
        # Backward compatibility
        if len(args) == 1 and isinstance(args[0], str) and 'dependency' not in kwargs:
            kwargs['dependency'] = 'unknown'
            message = args[0]
        else:
            dependency = kwargs.pop('dependency', 'unknown')
            message = kwargs.pop('message', f"Missing dependency: {dependency}")
            kwargs['dependency'] = dependency

        super().__init__(
            message,
            category=ErrorCategory.CRITICAL,
            recovery_action=RecoveryAction.ABORT,
            details={"dependency": kwargs.get('dependency', 'unknown')},
            **kwargs
        )
```

## Server-Status

### Aktuell laufende Prozesse
- Port 8090: Background Shell (Status: running)
- Port 8091: Background Shell (Status: running)
- Port 8092: Background Shell (Status: running)
- Port 8093: Background Shell (Status: running)

### Empfehlung
Alle Server-Prozesse beenden und nur einen sauber neu starten:
```bash
# Alle Python-Prozesse beenden
pkill -f "python.*whisper_transcription_tool"

# Neu starten
cd /Users/denniswestermann/Desktop/Coding\ Projekte/whisper_clean
source venv_new/bin/activate
python -m src.whisper_transcription_tool.main web --port 8090
```

## Nächste Schritte

1. **Vollständiger Stack-Trace benötigt**
   ```python
   import traceback
   except Exception as e:
       logger.error(f"Error transcribing audio: {str(e)}")
       logger.error(f"Full traceback:\n{traceback.format_exc()}")
   ```

2. **Import-Debugging**
   ```python
   import src.whisper_transcription_tool.core.exceptions
   print(src.whisper_transcription_tool.core.exceptions.DependencyError.__init__.__code__.co_varnames)
   ```

3. **Defensive Programmierung**
   - Alle Exception-Handler sollten robust gegen fehlende Attribute sein
   - Verwendung von `getattr()` mit Default-Werten

4. **Clean Restart**
   - Virtual Environment neu erstellen
   - Alle `.pyc` Dateien löschen
   - Fresh Import aller Module

5. **LLM-Korrektur validieren**
   - `_correction_metadata.json` prüfen (Feld `method`, `corrections_made`, `processing_time_seconds`)
   - Server-Logs auf Meldung `LLM correction completed … with N adjustments` überwachen
   - Testtext mit absichtlichen Fehlern einspeisen, um positive Korrekturen zu erzwingen
   - Ggf. Debug-Ausgaben in `LLMCorrector._generate_correction` aktivieren (Prompt/Response-Preview)

## Lessons Learned

1. **Exception-Signatur-Änderungen sind gefährlich**
   - Backward-Compatibility immer einplanen
   - Alle Aufrufstellen müssen atomisch geändert werden

2. **Python Import-Cache kann Probleme verursachen**
   - Bei Klassenänderungen immer Neustart
   - `importlib.reload()` reicht oft nicht

3. **Fehler-Logging muss vollständig sein**
   - Immer Stack-Trace loggen
   - Exception-Typ und alle Attribute ausgeben

## Kontakt für weitere Unterstützung

Diese Dokumentation wurde erstellt für die weitere Fehleranalyse. Der Fehler konnte in der aktuellen Session nicht vollständig behoben werden und benötigt tiefere Analyse mit vollständigem Stack-Trace.
