# WhisperCC MacOS Local – Projekt-Wiki

Willkommen im zentralen Wissenshub für das Whisper Transcription Tool. Die Anwendung verbindet Whisper.cpp-basierte Transkription mit einer modernen Weboberfläche und optionaler LLM-gestützter Textkorrektur (LeoLM 13B). Dieses Wiki richtet sich an Entwickler, Tester und Projekt-Stakeholder und ergänzt die Repo-Dokumentation mit kuratierten Referenzen, Abläufen und Best Practices.

## Schnellzugriff
- **[Schnellstart & Installation](Getting-Started.md)** – Umgebung vorbereiten, Modelle laden, App starten.
- **[Funktionsübersicht](Feature-Overview.md)** – Kernfeatures, Module, geplante Erweiterungen.
- **[Textkorrektur-Workflow](Text-Correction-Workflow.md)** – LeoLM-Integration, Ressourcenmanagement, UI-Flow.
- **[Architektur & Komponenten](Architecture.md)** – Systemdiagramme, Modulverantwortlichkeiten, Datenflüsse.
- **[Konfiguration & Betrieb](Configuration.md)** – Einstellungen, CLI-Flags, Deployment-Hinweise.
- **[Qualitätssicherung](Testing-and-QA.md)** – Testmatrix, automatisierte Suites, manuelle Checklisten.
- **[Troubleshooting & FAQ](Troubleshooting-and-FAQ.md)** – Häufige Fehlerbilder und Lösungsstrategien.
- **[Release-Management](Release-Management.md)** – Versionierung, Changelog, Veröffentlichungsschritte.
- **[Contribution Guide](Contribution-Guidelines.md)** – Arbeitsabläufe, Branch-Policy, Code-Standards.

## Aktueller Status (Stand v0.9.7.3)
- **Transkription:** Whisper.cpp (large-v3-turbo) lauffähig, DependencyError-Hotfix aktiv.
- **Textkorrektur:** Modul 5 (LeoLM) liefert aktuell 0 Änderungen → Debugging offen.
- **Frontend:** Zeigt Modell, Laufzeit, Änderungscount zur Diagnose.
- **macOS-App:** Xcode-Projekt und CI-Workflows für notarized Builds.
- **Testabdeckung:** Unit-, Integrations- und End-to-End-Tests (FastAPI, CLI, UI, Resource Manager).

## Kommunikationsrichtlinien
- **Project Tracking:** siehe `.kiro/specs` für Spezifikationen und Aufgaben.
- **Issue Management:** GitHub Issues nach Feature-Label (Transcription, TextCorrection, UI, macOS).
- **Stand-ups & Reviews:** Ergebnisse als Session-Dokumentation (`SESSION_DOCUMENTATION_vX.Y.Z.md`).

Viel Erfolg beim Arbeiten mit WhisperCC! Für fehlende Informationen oder Feedback bitte im `#whisper-dev` Slack-Channel melden oder ein Issue mit Label `documentation` erstellen.
