# Card Evidence Policy v1

## Zweck

Diese Policy ergänzt `Project Card v1` um zwei fail-closed Regeln für die Herkunft und zeitliche Einordnung von Evidenz.

## Regeln

1. Eine Projektkarte darf weder sich selbst noch eine andere Datei im Projektkartenordner als Quelle verwenden. Projektkarten sind Zusammenfassungen und keine Eigenbelege.
2. `reviewed_at` darf nicht nach dem Tag liegen, an dem die Policy geprüft wird.

Die Regeln verändern keine Repositorybeziehung und erzeugen keinen aktuellen Git-, CI- oder Runtimezustand.

## Prüfung

```bash
python3 scripts/card_policy_v1.py .
python3 -m unittest discover -s scripts/tests -p 'test_card_policy_*.py'
```

Erwarteter Abschluss:

```text
PROJECT-CARD-POLICY: PASS
```
