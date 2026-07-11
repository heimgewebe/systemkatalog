# Cabinet-Taskability-Befund 2026-07-02

## These

Cabinet besitzt die richtigen Zielorgane: Bestand, Prüfung und Steuerung.

## Antithese

Die Aufgabentafel war leer. Ein Blueprint ohne konkrete Tasks bleibt eine Landkarte, aber kein Steuerungsinstrument.

## Synthese

Der kleinste wirksame Schritt ist eine belegte Backlog-Schicht in `steuerung/20 Aufgaben/index.md`: Aufgaben mit Organführung, Scope, Risiko, Stop-Kriterium und Target-Proof.

## Belegt

- Offene GitHub-Issues: 0, erhoben am 2026-07-02T06:36:05+02:00.
- Offene Draft-PRs: #14 `Cards3`, #15 `fix: harden card evidence policy`.
- `steuerung/20 Aufgaben/index.md` war vor diesem Slice nur ein Platzhalter.

## Plausibel

- PR #15 sollte vor PR #14 geprüft werden, weil Evidence-Policy die Aussagegrenzen von Project Cards betrifft.
- PR #14 ist wegen des Titels `Cards3` semantisch unklarer und sollte nicht ohne Zerlegung fortgeführt werden.

## Spekulativ

- PR #14 könnte durch spätere Project-Card-Arbeiten teilweise überholt sein. Dafür fehlen Diff und Review-Kommentare.
- PR #15 könnte mergefähig sein. Dafür fehlen Draft-Auflösung, vollständiger Diff und Check-Auswertung.

## Resonanz- und Kontrastprüfung

Deutung A: Die offenen PRs sind der wichtigste nächste Hebel, weil vorhandene Arbeit abgeschlossen werden kann.

Deutung B: Die leere Aufgabensteuerung ist der tiefere Engpass, weil ohne Taskmodell jede PR-Prüfung isoliert bleibt.

Einordnung: B hat mehr Systemtiefe, A hat unmittelbaren Nutzen. Deshalb wurde zuerst die Aufgabensteuerung befüllt und PR #15 als nächste konkrete Aufgabe gesetzt.

## Epistemische Leere

- PR-Diffs #14/#15 fehlen, nötig für Merge-, Close- oder Split-Empfehlung.
- Aktuelle CI-Details fehlen, nötig für Mergefähigkeit.
- Codex- oder Review-Kommentare fehlen, nötig für vollständige Review-Pflicht.
- Bureau-Validator-Live-Stand fehlt, nötig für CAB-STE-006.

## Risiko und Nutzen

Nutzen: Steuerung wird von Platzhalter zu verwendbarer Tasktafel. Organzuständigkeiten verhindern Executor-Drift. Draft-PRs werden sichtbar, aber nicht voreilig gemergt.

Risiko: Die Tabelle kann als Freigabe missverstanden werden. Gegenmaßnahme: klare Arbeitsregel `Aufgabe ist keine Ausführungserlaubnis`.

## Entscheidung

Nicht direkt PR #15 anfassen, sondern zuerst die Steuerungsfläche herstellen und danach PR #15 als priorisierte Aufgabe reviewen.
