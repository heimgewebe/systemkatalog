# Heim-PC ChatGPT Dashboard — Systemgrenze

Stand: 2026-09-01

## Rolle

Das Heim-PC ChatGPT Dashboard ist eine lokale, read-only Präsentations- und Zugriffsschicht für ChatGPT. Es bündelt Hostmetriken und begrenzte Projektionen kanonischer Primärsysteme, ohne deren Wahrheits- oder Ausführungszuständigkeit zu übernehmen.

Es ist bewusst **nicht** mit `repo:leitstand` identisch. Leitstand ist seit dem 15. November 2026 archiviert; die frühere allgemeine Operator-Anzeige besitzt derzeit keinen im Katalog belegten aktiven Nachfolger. Das lokale ChatGPT Dashboard bleibt eine Zugriffssicht mit engem Heim-PC- und ChatGPT-Zuschnitt.

Die Identitäten sind absichtlich getrennt: `repo:heim-pc-dashboard-chatgpt-app` bezeichnet ausschließlich den privaten Implementierungs- und Quellcodebestand. `service:heim-pc-chatgpt-dashboard` bezeichnet die lokale laufende Zugriffsschicht. Der Repositoryknoten implementiert den Service, übernimmt dadurch aber keine zusätzliche Wahrheits-, Prioritäts-, Claim-, Dispatch- oder Ausführungsautorität.

## Wahrheitsgrenzen

- Bureau besitzt Aufgaben-, Claim- und Completion-Wahrheit. Das Dashboard darf operative Bureau-Werte nur aus dem dafür vorgesehenen read-only Control-Plane-/Dashboard-Vertrag projizieren. Eine Queue-Kompatibilitätsansicht begründet keine Prioritäts-, Claim- oder Dispatch-Wahrheit.
- Grabowski besitzt lokale Ausführung, konkrete Ressourcen- und Operatorzustände. Das Dashboard darf nur kanonische, begrenzte read-only Projektionen darstellen und keine Mutation oder Ausführungsentscheidung auslösen.
- `general_operator_display` ist derzeit unbesetzt; die historische Leitstand-Zuständigkeit bleibt im archivierten Repository nachvollziehbar. Das lokale Dashboard besitzt keine eigene Truth-Domain und darf aus seiner Darstellung keine zweite Lifecycle-, Prioritäts- oder Runtime-Wahrheit erzeugen.
- GitHub, CI und Runtime bleiben für ihre jeweiligen Fakten Primärquellen; eine Darstellung im Dashboard überträgt keine Autorität.
- Das private Repository besitzt nur seine Code- und Versionshistorie. Die Existenz eines Commits oder einer Repositoryänderung ist keine operative Dashboard-, Bureau- oder Grabowski-Wahrheit.

## Ausfallsemantik

Fällt das lokale Dashboard aus, laufen Bureau, Grabowski, GitHub, CI und Runtime unverändert weiter. Fehlende oder veraltete Eingaben werden als unbekannt beziehungsweise degradiert dargestellt; sie werden nicht durch lokale Heuristiken ersetzt.

Fällt GitHub oder der private Repositoryzugang aus, kann die bestehende lokale Serviceinstanz weiterlaufen. Quellcodeänderung, Wiederaufbau und Veröffentlichung sind dann eingeschränkt; die Primärsysteme und deren Wahrheiten bleiben davon unberührt.

## Nicht-Ziele

Das Dashboard ist nicht zuständig für:

- Task-Autorisierung oder Priorisierung;
- Claims oder Dispatch;
- Agentenrouting;
- Runtime-Mutation, Deployments oder Cleanup;
- eigene fachliche Rekonstruktion von Bureau-Blockern aus Freitext;
- die Übernahme einer allgemeinen Operator-Wahrheit.

Diese Grenze bleibt bestehen. Eine neue allgemeine Operator-Anzeige erfordert eine ausdrücklich belegte Zuständigkeit; aus dem Archivstatus folgt keine automatische Autoritätsübertragung.
