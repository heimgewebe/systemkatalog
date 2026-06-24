# Cabinet Config Audit

Current tree snapshot: `44c85f3058cab389f88fe6ae4ab4bff2daed87c4` (clean worktree, branch `main`).

## tracked vs local-only

- Versioniert (`/home/alex/repos/cabinet`): `.cabinet`, `policy/cabinet-layout.json`, `.home/home.json`, Räume mit `Operating Rules.md`, `index.md`, `Repository Reference.md`.
- Lokal/nicht versioniert (laut `.gitignore` und `ops/manifest.json`):
  - `.agents/.runtime/`
  - `.agents/.conversations/`
  - `.agents/.memory/`
  - `.agents/.messages/`
  - `.agents/.config/`
  - `.agents/*/sessions/`
  - `.agents/*/workspace/`
  - `.global-agents/`
  - `.cabinet.db*`
  - `.cabinet-state/`
  - `runtime.env`
  - Installationspfade unter `~/.local/share/cabinet/`, `~/.local/bin/`

Shape-Report lokaler Configs (Dateipfad, Existenz, Typ, Größe): für `.agents/.config/` und `.home/home.json` verweigert, da `.home/home.json` kanonisch und versioniert ist. `.agents/.config/` wird von dieser Untersuchung ausgeschlossen (siehe Sicherheitsgrenzen).

## Consumer und Authority

| Datei/Oberfläche | Writer | Consumer | Versioniert | Authority |
|---|---|---|---|---|
| `policy/cabinet-layout.json` | Mensch (authoritativ) | Runtime/Layout-Validierung (`scripts/check-cabinet-layout.py`) | Ja | Repository |
| `.home/home.json` | Mensch/Runtime | Runtime (Default-Room-Zustand) | Ja | Mensch |
| `.cabinet` | Mensch | Runtime (Identifikation) | Ja | Repository |
| `<raum>/.cabinet` | Mensch | Runtime | Ja | Repository |
| `Repository Reference.md` | Werkzeug/Review-Import | Mensch/Agenten | Ja | Repository |
| `.agents/.config/workspace.json` | Runtime | Runtime | Nein | Lokal |
| `.global-agents/` | Nicht vorhanden (`.gitignore`) | Runtime (falls vorhanden) | Nein | Lokal |
| `ops/manifest.json` | Mensch | Installer (`ops/install/*`) | Ja | Repository |

## Enforced vs Konvention

- Erzwungen durch Technik:
  - Räume in `policy/cabinet-layout.json` müssen existieren und Namensregeln beachten (`scripts/check-cabinet-layout.py`).
  - `defaultRoom` in `policy/cabinet-layout.json` und `.home/home.json` ist dupliziert; Konsistenz wird durch Validierung geprüft.
  - Verbotene Top-Level-Räume und Namen wirken als Konfigurationsschranke.
- Reine Konvention:
  - Kabinett-Semantik (Bedeutungsräume/Arbeitsregime) liegt in Markdown-Texten und Indexdateien, nicht in Schema.
  - `Cabinet-Modell.md` ist dokumentarisch.

## Room-Semantik

- Räume: `betrieb`, `heimgewebe`, `labor`, `vorzimmer`, `weltgewebe`, `werkstatt`
- Jeder Raum hat: `index.md`, `Start Here.md`, `Operating Rules.md`, `Sources of Truth.md` und nummerierte Unterordner (00-90).
- Räume sind dokumentarisch strukturiert; sie gelten als Verzeichnisnamen mit Markdown-Inhalten. Keine technische Semantik für Routing ist belegt.

## Agenten-Semantik

- Versionierte Agenten: nicht vorhanden (`ops/manifest.json` lokal_only enthält `.global-agents/`).
- `.agents/.config/workspace.json` wird laut `.gitignore` lokal gehalten; ohne Shape-Report bleibt Inhalt unbelegt.
- Belegte Consumer: Runtime und CLI (`ops/bin/cabinet`).

## Provider- und Modell-Semantik

- CLI referenziert `runtime.env` und `cabinetai-0.4.4/dist/index.js`.
- Providerbindung, Modellwahl, Routing und Kostenlimit: keine versionierten Belege gefunden. Epistemische Leerstelle.

## Jobs und Heartbeats

- `policy/cabinet-layout.json` enthält `scheduler.jobs = 0`, `scheduler.heartbeats = 0`.
- `.jobs/.gitkeep` ist leer; keine Jobs definiert.
- Keine Jobs oder Heartbeats technisch belegt.

## Installer und Runtime

- Manifest: `ops/manifest.json` beschreibt Templates, Executables und Symlinks.
- Lokale Pfade unter `~/.config/systemd/user/`, `~/.local/bin/`, `~/.local/share/cabinet/` werden vom Installationsskript `ops/install/install-local-runtime.sh` verwaltet.
- Runtime-State- und Datenbankdateien sind in `.gitignore` und `local_only` ausgeschlossen.

## Safe Export

- `scripts/cabinet-safe-export.sh` existiert, Inhalt nicht auditiert.
- CI: `scripts/ci/validate-repository.sh` prüft Repo-Vertrag, Gitleaks und Installierbarkeit.

## Datenschutzrisiken

| Risiko | Status | Maßnahme |
|---|---|---|
| `.agents/.config/` lokal, nicht versioniert | Akzeptabel | Kein Commit in Repo |
| `runtime.env` lokal, nicht versioniert | Akzeptabel | Kein Commit in Repo |
| `.cabinet.db*` lokal, nicht versioniert | Akzeptabel | Kein Commit in Repo |
| `.global-agents/` lokal, nicht versioniert | Akzeptabel | Kein Commit in Repo |
| ` Repository Reference.md` enthält Pfade/Remotes | Akzeptabel | Keine Secrets enthalten |

## Capability-Belege

- Cabinet CLI kann Räume auflisten und verarbeiten (Beleg: `ops/bin/cabinet` und Manifestversion `0.4.4`).
- Vollständige Modell-/Providersteuerung ist aus diesem Repo nicht ersichtlich.
- Bestehende CI-Skripte validieren Repository-Integrität, aber keine semantischen Modelle.

## Epistemische Leerstellen

- Inhalt und Schema von `.agents/.config/workspace.json` unbelegt.
- Tatsächliche Modell-/Provider-/Fallbacks-Logik unbelegt.
- Schreibgrenzen der Runtime unbelegt.
- Ob Runtime-Konfiguration bzw. `.home/home.json` durch den laufenden Dienst geschrieben wird, unbelegt.
- Ob `.cabinet.db` Indexstrukturen enthält, unbelegt.
- Agenten-Dispatch-Semantik unbelegt (keine versionierten Agenten).
- Befundlebenszyklus unbelegt.