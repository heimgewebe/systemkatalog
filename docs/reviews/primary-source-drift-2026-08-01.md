# Primärquellen-Driftprüfung – 1. August 2026

**Beobachtung:** `2026-08-01T05:08:43.853085Z` über den read-only GitHub-Inventar- und Inhaltsabruf; Heimserver zusätzlich revisionsgebunden auf `4c4099e234a277b5ea48a28939f0ec4d08711f2a` geprüft.

## Urteil

Sieben gebundene Primärquellen sind materiell vom gespeicherten Stand abgewichen. Die Änderungen werden nicht blind als reine Hash-Aktualisierung behandelt. Systemkatalog, Leitstand, Metarepo und Audio bleiben innerhalb ihrer bisherigen Katalogrollen. WGX präzisiert seine Rolle von einem breit lesbaren Fleet-Workflow-Werkzeug zu einem Repository-Verifikationsadapter. Commonworld führt einen eigenen, maschinenlesbaren Commons-Aufnahmevertrag ein. Heimserver ist auf GitHub öffentlich, bleibt aber außer Betrieb und ohne aktuelle Infrastrukturautorität.

## Belegte Entscheidungen

| System | geprüfter Quellstand | Entscheidung |
| --- | --- | --- |
| `repo:systemkatalog` | `fd96a544eb848b8047e62561efe63db27a087281:README.md` | Bindung aktualisieren; Zweck und Autoritätsgrenzen unverändert. |
| `repo:leitstand` | `362dda6ac161bf275a38682d18998fc284eebe52:README.md` | Bindung aktualisieren; zusätzliche read-only Snapshots ändern die Beobachtungsrolle nicht. |
| `repo:metarepo` | `f3524f9b040be957cfead5b80f7a683d0ea6df72:system/metarepo-role.v1.json` | Bindung aktualisieren; providerneutraler Änderungsgrenzenvertrag bleibt unter der bestehenden Rolle „Fleet-Mitgliedschaft und gemeinsame Verträge“. |
| `repo:wgx` | `45611f094cd7c4019c7eda4bd36b6fa862503132:README.md` | Zweck und Nichtzuständigkeiten präzisieren; die enge Domäne `shared_fleet_ci_checks` bleibt bestehen. |
| `repo:audio` | `49710c62c017019ba3778d0599e511e6b8bc61a7:README.md` | Bindung, Einstiegspunkt und Evidenz aktualisieren; Audiozentrale und Aufnahmeverträge liegen innerhalb der bestehenden kanonischen Audiorolle. |
| `repo:commonworld` | `35b6b19529891d33f0b0db3f864256f7069bbba4:README.md` | Zweck um evidenzgebundenen Katalog und Aufnahmevertrag ergänzen; neue, eng benannte Autoritätsdomäne `commonworld_commons_admission`. |
| `repo:heimserver` | `4c4099e234a277b5ea48a28939f0ec4d08711f2a:repo.meta.yaml` | Private Metadatenprojektion durch öffentliche, commitgebundene normative Datei ersetzen; Lifecycle bleibt `retired`. |

## Widerspruch

GitHub meldet `heimgewebe/heimserver` als öffentlich. `README.md` und `repo.meta.yaml` nennen es weiterhin privat. Für Sichtbarkeit gilt die aktuelle GitHub-Organisationsbeobachtung; die Dateien belegen nur Rolle und Stilllegung. Die Dokumentationskorrektur ist getrennte Folgearbeit und darf die Katalogaktualisierung nicht blockieren.

## Sicherheitsgrenzen

- Keine Runtime-, Task-, PR- oder Health-Wahrheit wird in den Katalog übernommen.
- WGX erhält keine Bureau-, Grabowski- oder Deployment-Autorität.
- Commonworld besitzt nur seinen veröffentlichten Aufnahmevertrag, keine universale Commons-Governance.
- Der Heimserver erhält trotz öffentlicher Sichtbarkeit keine aktive Rolle zurück.
- Alle Bindungen bleiben Commit-, Pfad- und SHA-256-gebunden.

## Unsicherheit

Gesamtunsicherheit: **0,08**. Ursache ist ausschließlich die widersprüchliche Sichtbarkeitsbeschreibung im Heimserver-Repository; die übrigen Primärquellen sind direkt und reproduzierbar geprüft.
