# Cabinet Runtime Retirement Preflight v1

Status: aktiver Vertrag für den rein lesenden T013-Preflight

Bureau-Task: `OPERATOR-ECOSYSTEM-REDUNDANCY-V1-T013`

## Zweck

Dieser Vertrag trennt zwei Dinge, die nicht vermischt werden dürfen:

1. **Private Livebeobachtung:** exakte lokale Pfade, Prozessdaten, Listenerdetails, Dateihashes und Dienstmetadaten.
2. **Öffentlicher Entscheidungsbeleg:** redaktierte Summen, Abhängigkeiten, Vertragsdrift, Rollbackphasen und Wirkungsgrenzen.

Der öffentliche Beleg ist kein Live-Dashboard und keine Katalogwahrheit. Er hält nur fest, auf welcher Grundlage eine spätere, separat autorisierte Rückbauentscheidung getroffen werden kann.

## Artefakte

| Rolle | Ort | Versioniert |
|---|---|---:|
| privater Livebeleg | außerhalb des Repositories, Modus `0600` | nein |
| redaktierter Snapshot | `docs/migration/cabinet-runtime-retirement-preflight-v1.json` | ja |
| Autorisierungs- und Rollbackpaket | `docs/migration/cabinet-runtime-retirement-authorization-v1.md` | ja |
| Projektor | `scripts/write_runtime_retirement_preflight.py` | ja |
| Validator | `scripts/validate_runtime_retirement_preflight.py` | ja |

Der öffentliche Snapshot bindet den privaten Beleg ausschließlich über SHA-256. Er enthält keine privaten Pfade, keine konkreten Portnummern, keine Prozess-IDs, keine Kommandozeilen und keine Geheimnisse.

## Zulässige öffentliche Aussagen

- Beobachtungszeitpunkt und Quellcommit.
- Verifizierte T004-, T007-, T012- und T018-Abhängigkeiten.
- Aggregierte Prozess-, Listener-, Datei- und Bytezahlen.
- Listenerexposition als Klasse, etwa `loopback_only`.
- Beobachtete Runtimeversion und versionierter Altvertrag.
- Klassifizierter Vertragsdrift.
- Nicht ausgeführte Rollbackphasen.
- Explizite Aussage, dass Runtimewirkung und Repository-Rename nicht autorisiert sind.

## Verbotene öffentliche Details

- lokale Home-, Konfigurations-, Zustands- oder App-Pfade;
- konkrete Portnummern oder Loopbackadressen;
- PIDs, Parent-PIDs oder Prozessargumente;
- Environment-Inhalte und Zugangsdaten;
- einzelne Dateipfade oder lokale Dienstdateien;
- eine Behauptung, dass Nichtnutzung oder gefahrlose Abschaltung bewiesen sei.

## Fail-closed-Regeln

Der Projektor verweigert die Ausgabe, wenn:

- eine T004/T007/T012/T018-Abhängigkeit nicht `verified` ist;
- der Repositoryzustand des privaten Belegs nicht sauber war;
- irgendeine Wirkung oder Autorisierung als `true` gemeldet wird;
- ein beobachteter Listener nicht ausschließlich loopbackgebunden war;
- Pflichtfelder oder Hashbindungen fehlen.

Der Validator verweigert den öffentlichen Snapshot, wenn:

- private Detailfelder oder private Zeichenketten auftauchen;
- Runtimewirkung oder Rename als autorisiert markiert werden;
- eine Rückbauphase bereits als ausgeführt erscheint;
- die erforderlichen Nicht-Claims oder expliziten Autorisierungsschritte fehlen;
- der bekannte Runtimevertragsdrift verschwiegen wird.

## Nicht-Claims

Ein grüner Preflight beweist nicht:

- sichere sofortige Abschaltung;
- aktuelle menschliche Nichtnutzung;
- Abwesenheit aller entfernten Consumer;
- Lösch-, Shutdown-, Retention- oder Rename-Erlaubnis;
- erfolgreiche spätere Runtimeentfernung.
