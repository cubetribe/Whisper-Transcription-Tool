# Qualitätssicherung & Tests

## Testarten
| Kategorie | Dateien/Tools | Fokus |
| --- | --- | --- |
| Unit Tests | `tests/unit/`, `test_module5_basic.py` | Module, Prompts, ResourceManager |
| Integration | `tests/integration/`, `test_module5_integration.py` | End-to-End Transkription + Korrektur |
| E2E UI | Playwright-Screenshots in `.playwright-mcp/` | Web-Flow, Regressionen |
| Performance | `test_chunking.py`, `test_module5_integration.py::test_memory_budget` | Chunking, RAM, Speed |
| macOS QA | Skripte in `macos/final_qa_validation.sh` | App-Bundle-Checks |

## Automatisierte Ausführung
```bash
# Unit + Integration
tox -e py311

# Spezifische Tests
pytest tests/integration/test_python_swift_integration.py
pytest test_module5_integration.py -k correction

# macOS QA
bash macos/final_qa_validation.sh
```

## Manuelle Checkliste
1. Startskripte (`Start.command`, `start_server.sh`) testen
2. Web-UI: Upload → Transkription → Korrektur → Download
3. LeoLM-Korrektur mit Opus-Datei (WhatsApp) prüfen
4. Telefonmodul (wenn aktiviert): Sample-Workflow + Mock-Daten
5. macOS-App: Starten, Menü, Logging, Exit

## Qualitätsmetriken
- **Transkriptionsdauer:** Ziel < Echtzeit * 1.5.
- **Korrekturdauer:** Ziel < 2x Transkriptionszeit.
- **RAM-Budget:** <= 6 GB zusätzlich bei LeoLM (Q4_K_M).

## Reporting
- Ergebnisse sammeln in `TEST_IMPLEMENTATION_REPORT.md`
- Regressionen dokumentieren in `SESSION_DOCUMENTATION_vX.Y.Z.md`
- Bugs → GitHub Issues (Label `bug`, `text-correction`, `ui`, etc.)

Weitere Details: [Tasks-Spezifikation](https://github.com/cubetribe/WhisperCC_MacOS_Local/blob/main/.kiro/specs/llm-text-correction/tasks.md) und [UPDATE_LOG.md](https://github.com/cubetribe/WhisperCC_MacOS_Local/blob/main/documentation/UPDATE_LOG.md).
