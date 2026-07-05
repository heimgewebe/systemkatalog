# Cabinet Ecosystem Signal Contract v1

## Status

- Typ: Contract
- Version: 1
- Owner: Cabinet
- Modus: read-only observation
- Bureau-Wirkung: keine direkte Task-Erzeugung

## Zweck

`cabinet_ecosystem_signal` beschreibt eine einzelne beobachtete Aussage aus einer primaeren Quelle des Heimgewebe-Ökosystems.

Ein Signal ist Rohwahrnehmung mit Evidenz, Frischebasis und Effektabschluss. Es ist kein Task, keine Freigabe und kein Wahrheitsersatz.

## These

Cabinet braucht echte Wahrnehmung aus GitHub, CI, lokalem Git/Worktree oder vergleichbaren Primaerquellen, bevor Claims oder Bureau-Kandidaten belastbar werden.

## Antithese

Wenn Signale ohne Quelle, Beobachtungszeit und Effektgrenze in Claims verwandelt werden, entsteht zirkulaere Evidenz: Cabinet bestätigt dann nur die eigene Beschreibung.

## Synthese

Jedes Signal bindet eine beobachtete Aussage an:

- `observedAt` als Frischebasis;
- `sourceSystem` als Quellenklasse;
- `subject`, `predicate`, `object` als minimale Aussage;
- `evidence` mit Primaerreferenz;
- `effectFlags`, die alle operativen Wirkungen ausschliessen;
- `doesNotEstablish`, damit der Befund nicht als Task- oder Merge-Recht missverstanden wird.

## Minimales Objekt

```json
{
  "schemaVersion": 1,
  "kind": "cabinet_ecosystem_signal",
  "contractVersion": "1",
  "contractPath": "docs/contracts/cabinet-ecosystem-signal-v1.md",
  "schemaPath": "docs/contracts/cabinet-ecosystem-signal-v1.schema.json",
  "id": "signal:github:heimgewebe.bureau:pr:95:state:5e832b320786",
  "observedAt": "2026-07-05T16:38:42Z",
  "sourceSystem": "github",
  "subject": "repo:bureau",
  "predicate": "github_pr_state",
  "object": "open",
  "evidence": [
    {
      "type": "github_pr",
      "ref": "heimgewebe/bureau#95",
      "url": "https://github.com/heimgewebe/bureau/pull/95",
      "observedHeadSha": "5e832b320786180bb142be565f0f7b58c6aa6e38"
    }
  ],
  "freshness": {
    "basis": "observedAt",
    "maxAgeHours": 24
  },
  "confidence": 0.82,
  "effectFlags": {
    "taskCreationAllowed": false,
    "queueMutationAllowed": false,
    "dispatchAllowed": false,
    "mergeOrPushAllowed": false,
    "runtimeMutationAllowed": false,
    "dumpGenerationAllowed": false,
    "authorityInferenceAllowed": false
  },
  "doesNotEstablish": [
    "task_approval",
    "merge_readiness",
    "runtime_correctness",
    "claim_truth",
    "autonomous_dispatch",
    "bureau_import_implemented"
  ]
}
```

## Erlaubte Source-Systeme

- `github`
- `ci`
- `local_git`
- `worktree`
- `fixture`

`fixture` ist nur fuer Tests und Beispiele erlaubt. Produktive Wahrnehmung soll Primaerquellen bevorzugen.

## Effektabschluss

Alle `effectFlags` muessen `false` sein. Dieses Contract-Objekt darf keine Bureau-Tasks erzeugen, keine Queue aendern, keinen Agenten dispatchen, nicht mergen oder pushen, keine Runtime veraendern und keine Dump-Erzeugung ausloesen.

## Bureau-Grenze

Bureau darf ein Signal nicht direkt importieren. Erst ein separater Cabinet-Claim oder Bridge-Kandidat mit Review-Feldern darf Bureau-preview-faehig werden.

## Frische

Frische kommt aus `observedAt`. Ein Batch-`expires_at` in einem spaeteren Claim darf diese Beobachtungszeit nicht ersetzen.

## Nicht behauptet

Ein valides Signal beweist nicht:

- Task-Freigabe;
- Merge-Reife;
- Runtime-Korrektheit;
- Claim-Wahrheit;
- autonomen Dispatch;
- Bureau-Import.

## Epistemische Leere

Ein Signal sagt nur, was beobachtet wurde. Es beweist nicht, dass alle relevanten Quellen beobachtet wurden. Dafuer braucht es getrennte Coverage- und Recall-Berichte.
