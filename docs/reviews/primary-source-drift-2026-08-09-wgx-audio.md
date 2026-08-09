# Primärquellen-Driftprüfung – 9. August 2026: WGX und Audio

## Ausgangslage

Der frische Driftbericht `c6257eff520aec6a3cd73fdda715f748c9c292ad297a8443081548d8d9013c4c` meldet genau zwei materielle Primärquellenänderungen: `repo:wgx` und `repo:audio`. Die Beobachtungen stammen vom 9. August 2026, 06:54 MESZ.

## WGX

Die neue Primärquelle `254d4fa821f50b88362793c9ccd37082e2d0ed9d:README.md` verengt die Rolle ausdrücklich. WGX ist kein allgemeiner Besitzer geteilter Fleet-CI-Checks und kein breiter CI-Frontdoor-Router mehr. Es ist ein kleiner Kompatibilitätsrunner für repository-eigene `.wgx/profile.yml`-Profile. Es besitzt die WGX-v1-Parser-/Runner-Semantik, Taskauflistung sowie explizite `quick`/`full`-Validierung. Fleet- und Policy-Wahrheit bleiben bei Metarepo, Taskkoordination bei Bureau, Git-/Worktree-/Prozess-/Deploy-Autorität bei Grabowski/GitHub und repositoryübergreifender Codekontext bei RepoGround.

Entscheidung: Die Katalogsemantik wird verengt. `shared_fleet_ci_checks` wird durch `wgx_profile_runner_contract` ersetzt; die WGX→CI-Beziehung beschreibt nur noch die optionale Ausführung repository-deklarierter Profilvalidierung.

## Audio

Die neue Primärquelle `a9d2899f5ed415cafaaa99e6951aeace04d2525a:README.md` erweitert das Produkt um iPad/PWA- und Bridge-Oberflächen, ändert aber nicht seine stabile Katalogrolle als kanonisches Audio-Repository für Konfiguration, Aufnahme, Wiedergabe, Instrumente und experimentelle Musiksysteme. Die bestehenden Grenzen zu Live-Hardware, Runtime-Gesundheit, Task- und Merge-Autorität bleiben zutreffend.

Entscheidung: Keine Audio-Semantikänderung; nur revisions- und digestgebundene Quellenaktualisierung.

## Grenzen

Diese Prüfung etabliert keine Runtime-Gesundheit, keine konkrete Hardwarepräsenz, keinen Taskstatus, keine Merge-Reife und keine automatische Deployment-Autorität.
