# Stabile Resilienzsemantik v1

## Zweck

`registry/ecosystem/resilience.v1.json` beschreibt stabile Resilienzeigenschaften katalogisierter Systeme und ausgewählter Beziehungen. Die Datei beantwortet, welche Kritikalität fachlich geprüft ist, welche gemeinsamen Ausfalldomänen bekannt sind, wie relevante Kanten bei Teilausfällen gekoppelt sind und welche Recoverywege grundsätzlich zulässig sind.

Sie ist keine Laufzeitbeobachtung und keine Control Plane.

## Drei getrennte Aussagen

1. **Kritikalität** beschreibt die fachliche Bedeutung eines Systemverlusts.
2. **Ausfalldomänen** beschreiben stabile gemeinsame Abhängigkeiten.
3. **Recoverymodi** beschreiben zulässige Pfade, gemeinsame Fehlerursachen und Rückkehrbedingungen.

Keine dieser Aussagen belegt aktuelle Gesundheit, Recoverybereitschaft oder Ausführungsautorität.

## Ehrliches `unknown`

Jedes katalogisierte System besitzt genau einen Eintrag. Nicht geprüfte Kritikalität bleibt `unknown`; fehlende Klassifikation wird nicht aus Knotengrad, Repositorysichtbarkeit oder technischer Lautstärke geschätzt. Eine leere Recoveryliste bedeutet, dass kein stabiler Pfad katalogisiert ist, nicht dass Recovery unmöglich oder unnötig wäre.

## Kanten

Nur ausfall- oder autoritätsrelevante stabile Kanten erhalten zusätzliche Semantik:

- `coupling`: Art der betrieblichen Abhängigkeit;
- `failurePolicy`: blockieren, puffern, degradieren, fallbacken oder ignorieren;
- `authorityDirection`: Richtung der fachlichen Wahrheit;
- `recoveryModeRef`: optionaler vorab definierter Ersatzpfad.

Nicht klassifizierte Kanten werden in der Projektion mit `—` gezeigt. Das ist eine Wissenslücke, keine Entwarnung.

## Recoverygrenze

Ein Recoverymodus enthält Triggerklasse, Rückkehrbedingung, Ausfalldomänen, Unabhängigkeitsklasse und `doesNotEstablish`. Er darf weder von Systemkatalog noch von Schauwerk oder Leitstand ausgelöst werden. Live-Prüfung und Ausführung bleiben bei Runtime, Grabowski und den jeweiligen Primärquellen; Abschlussanforderungen gehören in den Konvergenzregelkreis.

## Verbotene Abkürzungen

- keine automatische Kritikalität aus Graphzentralität;
- keine aktuelle Health-, Task-, CI- oder Lease-Angabe;
- keine freie adaptive Neuverdrahtung;
- keine Autoritätsübernahme durch Fallback;
- keine Behauptung unabhängiger Redundanz bei gemeinsamen Ausfalldomänen;
- kein globaler Resilienz- oder Gesundheitsscore.

## Verbraucher

- Bureau darf die stabilen Klassen in revisiongebundene Claims und Pläne übernehmen.
- Grabowski darf sie als Eingabe für Live-Preflights verwenden, muss den Zustand aber selbst beobachten.
- Konvergenzregelkreis darf daraus Evidenzanforderungen ableiten, wenn die Quellenbindung frisch ist.
- Schauwerk und Leitstand dürfen sie darstellen, aber nicht verändern oder als Livewahrheit ausgeben.
