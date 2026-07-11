# Cabinet-Era: historischer Index

Status: archivierte Entscheidungs- und Kompatibilitätsflächen

Diese Dateien erklären frühere Cabinet-Rollen und Experimente. Sie sind **keine** aktuelle Katalog-, Task-, Runtime- oder Merge-Wahrheit.

## Erhaltene Belege

- [Dynamische Claims v0](ecosystem-dynamic-claims-v0.jsonl) — frühere status-, confidence- und expiry-basierte Radarclaims; nur noch für Legacy-Kompatibilität.
- [Frühere Rollenentscheidung – Original](cabinet-role-boundary-v1.superseded.md) — bitgenauer historischer Wortlaut.
- [Aktueller Superseded-Verweis](../../blueprints/cabinet-role-boundary-v1.md) — verweist auf die heutige Systemkatalog-Policy.
- [Operator-Redundanz-Audit](../../../registry/ecosystem/operator-redundancy-audit.v1.json) — datierter Entscheidungsbeleg, kein Live-Status.
- [Handgepflegte Karte](../../../rendered/ecosystem-map.mmd) — nicht autoritative historische Orientierung.

Aktuelle Einstiege: [Systemkatalog](../../../rendered/system-catalog.md), [Policy](../../../policy/system-catalog.v1.json), [Authority Matrix](../../../registry/ecosystem/authority-matrix.v1.json).

## Legacy-Bridge-Probe

Die historische Bureau-Probe erwartet den alten Claims-Pfad. `scripts/prepare_legacy_bridge_probe.py` erzeugt deshalb ausschließlich im CI-Arbeitsverzeichnis eine temporäre, nicht autoritative Sandbox aus der hashgebundenen Archivdatei. Die stabilen Katalogclaims werden nicht als Taskkandidaten exponiert.
