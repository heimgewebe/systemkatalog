# Semantische Prüfung der Primärquellenabweichungen vom 26. Juli 2026

## Bindung

- Ausgangscommit des Systemkatalogs: `1cda4ee29aacb39d99a5ab415611fff6da6c54aa`
- GitHub-Beobachtungsartefakt: `/tmp/systemkatalog-observations-20260726.json`
- Beobachtungs-SHA-256: `1a73a26ee1f3a715840106b755387e39c56d90f425f552e9821da24b69fad6a0`
- Beobachtungstask: `183dc7bced6b48b9ba75f27f`
- Beobachtungs-Receipt-SHA-256: `49e0e26d64232370a957be3fdd274f23631494ac5f487b30f1f0463130450ec5`
- Driftbericht: `/tmp/systemkatalog-drift-20260726.json`
- Driftbericht-SHA-256: `d559c4ab45b4c0910ce258946ca4d89a9412425c99dd5075870689816f4d5e5b`
- Vollständiger Primärquellenvergleich: `/tmp/systemkatalog-source-diffs-20260726.txt`
- Vergleichs-SHA-256: `bec1d4913558cfb21b6eca62445e42f95fed5bb3762af21bc504c7bc45367d13`
- Vergleichstask: `ba7225a534564b67a2b929df`
- Vergleichs-Receipt-SHA-256: `495b0f38144b4ebdcbea60b7a238c5bfc18731d62f7f41ab05072ca05f285f91`
- Änderungstyp: zehnmal `primary_source_changed`
- Weitere Driftarten: keine

## Ergebnis

Alle zehn geänderten Primärquellen wurden vollständig zwischen dem gebundenen und dem beobachteten Commit verglichen. Organisationsumfang, Sichtbarkeit, Archivstatus, Standardbranches und Metarepo-Fleet-Zuordnung zeigen keine Abweichung.

Die Änderungen bleiben innerhalb der bereits katalogisierten Systemzwecke, Lebenszyklen, Wahrheitsgrenzen und stabilen Beziehungen. Deshalb werden ausschließlich Commit- und Inhaltsbindungen aktualisiert. Knoten, Zwecke, Lebenszyklen, Kanten und Authority-Matrix bleiben unverändert.

| System | Primärquelle | Klassifikation | Semantische Entscheidung |
|---|---|---|---|
| `repo:systemkatalog` | `README.md` | Lifecycle-Klarstellung | Dokumentiert die bereits gemergte Trennung von langfristigem Knotenlebenszyklus, Laufzeitstatus und Kantenstabilität; bestehende Katalogrolle unverändert. |
| `repo:bureau` | `README.md` | Authority-Präzisierung | Präzisiert Grabowski als Effekt- und Revalidierungsinstanz sowie die read-only Beobachtungsrolle; Bureau bleibt Eigentümer von Aufgaben-, Claim- und Abschlusswahrheit. |
| `repo:weltgewebe` | `README.md` | Post-Cutover-Bereinigung | Entfernt die dokumentierte Legacy-RoN- und `mode`-Rollbackbrücke nach belegtem Cutover; Produktzweck und Ökosystemgrenzen bleiben unverändert. |
| `repo:repoground` | `README.md` | Produktgrenzen-Klarstellung | Entfernt frühere Produkte aus der aktiven Oberfläche und grenzt Atlas als optionales Observation-Subsystem ab; RepoGround bleibt Kontext- und Evidenzsystem. |
| `repo:vibe-lab` | `README.md` | Namens- und Consumer-Korrektur | Ersetzt RepoBrief durch den aktuellen Produktnamen RepoGround; Experiment-, Evidenz- und Nichtautoritätsgrenzen bleiben unverändert. |
| `repo:schauwerk` | `README.md` | Capability-Härtung | Dokumentiert evidence-gebundenes `gate-status` und Live-Doctor-Prüfung innerhalb der bestehenden visuellen Projektionsrolle. |
| `repo:leitstand` | `README.md` | Observer-Vertrag-Konsolidierung | Entfernt veraltete und teilweise mutierende Oberflächen, beschreibt die aktuelle read-only Runtime, Freshness-Semantik und Fallbacks; stimmt mit `general_operator_display` und den bestehenden Nichtzuständigkeiten überein. |
| `repo:wgx` | `README.md` | Prüfanweisung-Härtung | Pinnt den Metrikschema-Commit und präzisiert Draft-2020-Validierung; Fleet-CLI- und CI-Rolle unverändert. |
| `repo:heim-pc` | `manifest/operator-entry.v1.json` | Operatorvertrag-Erweiterung | Ergänzt den Managed-Build-Umgebungsresolver und ersetzt Steuerboard durch Reposkop für read-only Repository-Readiness. Der Systemkatalog weist diese Authority bereits Reposkop zu; historische Steuerboard-Bezüge liegen nur im Archiv. |
| `repo:commonworld` | `README.md` | Internationalisierungs-Erweiterung | Dokumentiert englische Standardsprache, deutsche statische Alternative und getrennte Übersetzungsdaten; interaktive Commons-Erkundung und Nichtautoritätsgrenzen bleiben unverändert. |

## Commit- und Hashbindung

| System | Neuer Commit | Neuer Inhalts-SHA-256 |
|---|---|---|
| `repo:systemkatalog` | `1cda4ee29aacb39d99a5ab415611fff6da6c54aa` | `dbd566b6d8337f5238313386537eece250c9ad05f92c1a6cab780d77f1679457` |
| `repo:bureau` | `bfa44a83a76de053991b271883c738e87c854397` | `395960b2ca6a06310216123b7c311ad58fb0fa3adc55837fc26a649ea7c0358c` |
| `repo:weltgewebe` | `9fda211859e0cdca9decf8e159ea6a630c4ea086` | `dadcfe97ed4ae110533f51f5c3d256ef5157fcf8578cbc5c2a3177f81f65ecd6` |
| `repo:repoground` | `40dd1088a642370c5a7cc0dfd19dbd59e6395a35` | `34de5eedbd3cc9c7340887c12c97e5241b8060c17f2ff90f9facc1e175f03d9c` |
| `repo:vibe-lab` | `63c3d533dad4d51775aba7746915b5c8c5086f42` | `0949d20b07df77ec2d1976b754258e837ef4b4a0b9a799daa4560f9413300bd8` |
| `repo:schauwerk` | `8bdc86d013de3dfde0cb8502291cc8cfee6faba0` | `72fc8e0d66600cefa4a3f01dfda9fc6e95f04067352216da6ffe79edfcd0e9ab` |
| `repo:leitstand` | `a85c14d0df83da61c68e43fe814a19d483f3f6f2` | `be0fd2f4b5c4829fab65e1e6c0f732827c79edf779f04ad3760b49bfc1c98655` |
| `repo:wgx` | `5c14e53674193446b8832eca6e312bcf58190248` | `b7103c3519a9470bfecf7c75b10ce837223ea6ce88b90289162063ae2e875357` |
| `repo:heim-pc` | `446dcef499147970ca3bc7abc1d95f551be8d279` | `480a23722c17a0ec8cfa67a69389ebba22a95f83ccac0631b6a2a3b44eeb03bb` |
| `repo:commonworld` | `47b6e82c6e359dda1b03737ab45de0dbbca8f794` | `1465617e273db98b25a3bc1390502a74a07581c3d0bd8c20e2e82a2b27fe9ed7` |

## Nichtbehauptungen

Diese Prüfung etabliert weder Runtimegesundheit noch Deploymentwirkung, Taskabschluss, Mergebereitschaft oder automatische Mergeautorität. Sie belegt ausschließlich, dass die beobachteten Primärquellenänderungen semantisch mit den bestehenden Katalogaussagen vereinbar sind und daher neu gebunden werden dürfen.
