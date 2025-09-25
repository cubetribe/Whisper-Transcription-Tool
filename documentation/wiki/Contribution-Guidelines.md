# Contribution Guide

## Arbeitsweise
1. **Ticket auswählen** (GitHub Issue oder `.kiro/specs/.../tasks.md` Eintrag)
2. **Branch erstellen** (`feature/<topic>` oder `fix/<issue-id>`)
3. **Implementieren** – Code + Tests + Dokumentation
4. **CI prüfen** – `tox`, `pytest`, macOS-Skripte
5. **PR eröffnen** – Template ausfüllen, Reviewer taggen

## Coding Standards
- Python: PEP 8, Typannotationen, Docstrings bei öffentlichen Funktionen
- Frontend: Jinja + Bootstrap, JS modular (`static/js/`), keine Inline-Skripte
- Swift: SwiftLint konform, View-Model-Trennung
- Kommentare nur bei komplexer Logik (kein „Selbstverständliches“)

## Commits
- Präfixe: `feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `build:`
- Ein Commit pro logische Änderung
- Keine Secrets oder personenbezogenen Daten einchecken

## Reviews
- Fokus auf Funktionalität, Tests, Security, Performance
- Checkliste nutzen ([CODE_REVIEW_CHECKLIST.md](https://github.com/cubetribe/WhisperCC_MacOS_Local/blob/main/documentation/CODE_REVIEW_CHECKLIST.md) falls vorhanden)
- Mindestens 1 Approver (Core-Team)

## Dokumentation
- README/Wiki anpassen, wenn Feature sichtbar ist
- CHANGELOG aktualisieren (neue Versionen, Breaking Changes)
- Screenshots via `.playwright-mcp/` oder manuelle Captures hinzufügen

## Kommunikation
- Slack `#whisper-dev` für schnelle Abstimmung
- Meetings: Wöchentliche Syncs, Ad-hoc Bugtriage
- Probleme frühzeitig eskalieren (Issue + Ping im Slack)

Danke fürs Mitwirken! Bei Fragen: Maintainer @Dennis, @CoreArchitect-Team.
