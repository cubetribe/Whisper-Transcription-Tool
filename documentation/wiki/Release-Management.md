# Release-Management

## Versionierung
- **Schema:** `vMAJOR.MINOR.PATCH` (z.B. v0.9.7)
- **Branches:**
  - `main` – stabile Releases
  - `telefontest` / Feature-Branches – aktive Entwicklung
- **Tags:** Generiert bei Veröffentlichung (`git tag v0.9.7`)

## Vorbereitende Schritte
1. Testmatrix (`Testing-and-QA.md`) vollständig durchlaufen
2. CHANGELOG (`CHANGELOG.md`) aktualisieren (Features, Fixes, Roadmap)
3. README/Wiki prüfen, Screenshots aktualisieren
4. Session-Dokumentation erstellen (`SESSION_DOCUMENTATION_vX.Y.Z.md`)

## Release-Prozess
```bash
git checkout main
git pull origin main
# Änderungen committen (siehe Commit-Standards in Contribution Guide)
git tag v0.9.7
git push origin main --tags
```

## macOS-App Release
1. `bash macos/prepare_final_release.sh`
2. `bash macos/create_release.sh`
3. Notarization & Stapling (siehe `macos/WhisperLocalMacOs/README.md`)
4. Artifacts in GitHub Releases hochladen

## Post-Release
- Tickets abschließen, Milestones aktualisieren
- Wiki & Docs ggf. für nächste Iteration anpassen
- Monitoring der ersten Nutzer-Rückmeldungen (Slack, Issues)

Referenzen:
- [.github/workflows/build-macos-app.yml](https://github.com/cubetribe/WhisperCC_MacOS_Local/blob/main/.github/workflows/build-macos-app.yml)
- [documentation/UPDATE_LOG.md](https://github.com/cubetribe/WhisperCC_MacOS_Local/blob/main/documentation/UPDATE_LOG.md)
- [SESSION_DOCUMENTATION_v0.9.7.1.md](https://github.com/cubetribe/WhisperCC_MacOS_Local/blob/main/SESSION_DOCUMENTATION_v0.9.7.1.md)
