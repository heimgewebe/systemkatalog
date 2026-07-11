# Architektur des Systemkatalogs

## Zweck

Der Systemkatalog ist eine kleine, app-unabhängige Wissensschicht. Er hält nur Informationen, die sich nicht mit jedem Lauf, Pull Request oder Task ändern.

## Kanon

| Inhalt | Kanonische Datei |
|---|---|
| Systeme | `registry/ecosystem/nodes.json` |
| Beziehungen | `registry/ecosystem/edges.json` |
| stabile, belegte Aussagen | `registry/ecosystem/claims.jsonl` |
| Wahrheitszuständigkeiten | `registry/ecosystem/authority-matrix.v1.json` |
| Rollen- und Wirkungsgrenze | `policy/system-catalog.v1.json` |

`rendered/system-catalog.md`, `rendered/ecosystem-registry-map.mmd` und das Karten-Manifest sind deterministische Projektionen. Sie dürfen den Kanon nicht überschreiben.

## Laufzeit

`systemkatalog.service` liest ausschließlich versionierte Repositorydateien und bietet sie lokal per HTTP an. Der Dienst ist zustandslos und read-only. Es gibt keine Datenbank, keine Queue und keine Mutationsroute.

## Archivgrenze

`docs/archive/cabinet-era/` enthält die frühere Cabinet-Oberfläche, Raumgerüste, operative Experimente und Migrationsbelege. Das Archiv wird nicht in den aktiven Katalog eingespeist und nicht von den Validatoren als Kanon interpretiert.

## Änderungsregel

Eine Information gehört nur dann in den Systemkatalog, wenn sie:

1. eine stabile Systemrolle, Grenze oder Beziehung beschreibt;
2. eine benannte Primärquelle besitzt;
3. keinen aktuellen Betriebs-, Task-, PR- oder Reviewzustand kopiert;
4. reproduzierbar validiert und projiziert werden kann.
