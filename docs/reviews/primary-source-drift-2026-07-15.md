# Semantische Prüfung der Primärquellenabweichungen vom 15. Juli 2026

## Bindung

- Driftbericht: `/tmp/systemkatalog-drift-konvergenz-20260715.json`
- Driftbericht SHA-256: `b796df297e20d7fc508f44274a4924c91115b77c0f7c34ae69d1ae57f87c63bd`
- GitHub-Beobachtungsjob: `grabowski-job-ffbb238cdd49`
- Beobachtungs-Receipt SHA-256: `ad6084d05d89ecb9e786114c8e57c018342490b4978c800c53c9e1a82bf50457`
- Änderungstyp: zehnmal `primary_source_changed`
- Weitere Driftarten: keine

## Ergebnis

Alle zehn geänderten Primärquellen wurden gegen den gebundenen und den beobachteten Commit verglichen. Die Änderungen bleiben innerhalb der bereits katalogisierten Systemzwecke und Wahrheitsgrenzen. Deshalb werden ausschließlich Commit- und Inhaltsbindungen aktualisiert; Knoten, Zwecke, Beziehungen und Autoritäten bleiben unverändert.

| System | Primärquelle | Klassifikation | Semantische Entscheidung |
|---|---|---|---|
| `repo:chronik` | `README.md` | Systemkontext-Migration | Entfernt veraltete Metarepo-Architekturverweise und verweist auf den Systemkatalog; Chronik-Zweck unverändert. |
| `repo:schauwerk` | `README.md` | Capability-Erweiterung | Dokumentiert SW-020 und paketgebundene Miro-Auslieferung innerhalb der bestehenden visuellen Projektions- und Publikationsrolle. |
| `repo:leitstand` | `README.md` | Systemkontext-Migration | Entfernt konkurrierendes Rollen-Inventar und bestätigt den read-only Systemkatalog-Consumer; Leitstand-Zweck unverändert. |
| `repo:plexer` | `README.md` | Systemkontext-Migration | Ersetzt historische Organismus-Verweise durch Systemkatalog-Grenzen; Transportrolle unverändert. |
| `repo:heimlern` | `README.md` | Lifecycle-Klarstellung | Kennzeichnet Heimlern ausdrücklich als historische Referenz; stimmt mit dem bereits katalogisierten Lifecycle überein. |
| `repo:metarepo` | `system/metarepo-role.v1.json` | normative Vertragsänderung | Präzisiert Fleet-Mitgliedschaft, generierte Kompatibilitätsprojektion und die Trennung zur Systemkatalog-Semantik; bestehender Metarepo-Zweck bleibt gültig. |
| `repo:wgx` | `README.md` | Systemkontext-Migration | Ersetzt historische Architekturverweise durch den Systemkatalog; Fleet-CLI- und Snapshotrolle unverändert. |
| `repo:hausKI` | `README.md` | Systemkontext-Migration | Ersetzt historische Architekturverweise durch den Systemkatalog; Assistenz- und Automationszweck unverändert. |
| `repo:semantAH` | `README.md` | Systemkontext-Migration | Ersetzt historische Architekturverweise durch den Systemkatalog; semantische Index- und Insightrolle unverändert. |
| `repo:heim-pc` | `manifest/operator-entry.v1.json` | Operatorvertrag-Erweiterung | Ergänzt Transfer- und Managed-Build-Regeln innerhalb des bestehenden primären lokalen Operator-Hosts; keine neue Ökosystemautorität. |

## Commit- und Hashbindung

| System | Neuer Commit | Neuer Inhalts-SHA-256 |
|---|---|---|
| `repo:chronik` | `ac2d01bdf7a15732c9239c95e715d6bb43cf19c6` | `dbf0f5c222a083662a4eb14aa4df698078ababd1f14c4bc796e1b17c3c54822e` |
| `repo:schauwerk` | `8b36a63efd7779f68d41162f3cfecf7fba36b421` | `4423dadfc37f8d6e3714b5697a98a4e364aec4b84fd34d8230f8a5aa01e913ae` |
| `repo:leitstand` | `da4cf5b12ad50d2b1dafbe1883dc3130a3d8a130` | `4ee374b07434dcf27a62232ca20058747b3fb42152ce4e85d9c875bff776847e` |
| `repo:plexer` | `93fb9aa2451d44eb6b8cff7c7fd054086804049e` | `9641bc2289e5829b92ac232e456bf6a0b282fc3efb4adf28f02e0a02fe93b3c8` |
| `repo:heimlern` | `d0a5d1bf26c9a5f555b7541d97fadb27a7cf9b31` | `5a4f64ccab00b6c31b0817769b53ade5ded61c5927a4bfb5184cfe501e4cc4a8` |
| `repo:metarepo` | `8c6990e024d3e54a0d3dc8f5a0766162d3683497` | `9848a87b77aeb58b80a307a0a3dceca320e92c696031547937fe9cfa95f158fd` |
| `repo:wgx` | `01efb27f424466c951a196f095c549d1afdd10da` | `0a92d8c162a78142f3090bc64c98995e65e015bd9ea33f45b9dc294593993acf` |
| `repo:hausKI` | `7ae329ed5cee56666a9f6571e7ebee1c9df59441` | `9bcb01379557fac7b2274021dc4c16894160849858c405cd861ab3022711d726` |
| `repo:semantAH` | `b50bd2813b3f146f5cc51bee2ad6887bfb28ce69` | `20d28707e1dd8fedebe9c175246fde78bdf3d42d2f7c941ada587d36216a9047` |
| `repo:heim-pc` | `aabfca5a4b5a0c6aad079148e8e9d2a509b8c8d6` | `6fb53595f41bbb8de8454e346f643ed1bd5b6b8e5dee4bd036d0b9da263165c7` |

## Nichtbehauptungen

Diese Prüfung etabliert weder Runtimegesundheit noch Deploymentwirkung, Taskabschluss oder automatische Mergeautorität. Sie belegt ausschließlich, dass die beobachteten Primärquellenänderungen semantisch mit den bestehenden Katalogaussagen vereinbar sind und daher neu gebunden werden dürfen.
