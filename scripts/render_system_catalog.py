#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any
from urllib.parse import quote

from system_catalog_fleet import validate_coverage
from system_catalog_scope import validate_scope

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = Path("rendered/system-catalog.md")


def _load(root: Path, relative: str) -> dict[str, Any]:
    value = json.loads((root / relative).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{relative}: root must be an object")
    return value


def _cell(value: Any) -> str:
    return str(value or "").replace("|", "\\|").replace("\n", " ").strip()


def _render_href(target: str) -> str:
    if "://" in target or target.startswith("mailto:") or target.startswith("#"):
        return target
    return f"../{target.lstrip('/')}"


def _string_list_cell(value: Any) -> str:
    if not isinstance(value, list) or not value:
        return "—"
    return "<br>".join(_cell(item) for item in value)


def _entrypoints_cell(value: Any) -> str:
    if not isinstance(value, dict) or not value:
        return "—"
    rendered: list[str] = []
    for label, target in sorted(value.items(), key=lambda item: str(item[0]).casefold()):
        raw_target = str(target)
        href = quote(
            _render_href(raw_target),
            safe="/:#?&=@[]!$'*,;%-._~",
        )
        rendered.append(
            f"`{_cell(label)}`: [{_cell(raw_target)}]({href})"
        )
    return "<br>".join(rendered)


def render_text(root: Path = ROOT) -> str:
    root = root.resolve()
    policy = _load(root, "policy/system-catalog.v1.json")
    nodes_doc = _load(root, "registry/ecosystem/nodes.json")
    edges_doc = _load(root, "registry/ecosystem/edges.json")
    authority = _load(root, "registry/ecosystem/authority-matrix.v1.json")
    resilience = _load(root, "registry/ecosystem/resilience.v1.json")

    nodes = [item for item in nodes_doc.get("nodes", []) if isinstance(item, dict)]
    node_by_id = {item.get("id"): item for item in nodes if isinstance(item.get("id"), str)}
    stable_classes = set(policy.get("stableRelationClasses", []))
    edges = [
        item for item in edges_doc.get("edges", [])
        if isinstance(item, dict)
        and item.get("stability") in stable_classes
        and item.get("from") in node_by_id
        and item.get("to") in node_by_id
    ]
    authorities = [item for item in authority.get("authorities", []) if isinstance(item, dict)]
    entrypoints = [item for item in policy.get("entrypoints", []) if isinstance(item, dict)]
    repository_nodes = {item["id"] for item in nodes if item.get("type") == "repository"}
    fleet_coverage = validate_coverage(root, repository_nodes)
    repository_refs = {item["node"]: item for item in fleet_coverage["repositories"]}
    organization_scope = validate_scope(root, repository_nodes, fleet_coverage)
    resilience_by_system = {item["system"]: item for item in resilience["systems"]}
    resilience_by_relation = {
        (item["relation"]["from"], item["relation"]["to"], item["relation"]["type"]): item
        for item in resilience["relations"]
    }

    lines = [
        "# Systemkatalog",
        "",
        "> Automatisch erzeugte, app-unabhängige Leseansicht. Sie beschreibt stabile Rollen und verweist auf Primärquellen; sie enthält keinen Live-, Task- oder Merge-Status.",
        "",
        "## Zweck",
        "",
        "Der Katalog beantwortet, welche Systeme existieren, welchem Zweck sie dienen, wem welche Wahrheit gehört, welche stabilen Beziehungen bestehen und wo die Einstiegspunkte liegen.",
        "",
        "## Systeme",
        "",
        "| System | Typ | Kritikalität | Ausfalldomänen | Zweck | Nicht zuständig für | Wahrheitsbesitz | Einstiegspunkte |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for node in sorted(nodes, key=lambda item: (str(item.get("type", "")).casefold(), str(item.get("name", "")).casefold(), str(item.get("id", "")))):
        stable = resilience_by_system[node["id"]]
        lines.append(
            f"| {_cell(node.get('name'))} | {_cell(node.get('type'))} | "
            f"`{_cell(stable.get('criticality'))}` | {_string_list_cell(stable.get('failureDomains'))} | "
            f"{_cell(node.get('purpose'))} | {_string_list_cell(node.get('notResponsibleFor'))} | "
            f"{_string_list_cell(node.get('truthOwnership'))} | "
            f"{_entrypoints_cell(node.get('entrypoints'))} |"
        )

    lines.extend([
        "", "## Repository-Abdeckung", "",
        "Metarepo ist Primärquelle für die Fleet-Mitgliedschaft. Der Systemkatalog bleibt Primärquelle für Zweck, Beziehungen, Wahrheitszuständigkeiten und Einstiegspunkte.",
        "", "| System | Repository | Einordnung | Einstieg |", "|---|---|---|---|",
    ])
    for node in sorted((item for item in nodes if item.get("type") == "repository"), key=lambda item: str(item.get("name", "")).casefold()):
        reference = repository_refs[node["id"]]
        entrypoint = _cell(reference["entrypoint"])
        lines.append(
            f"| {_cell(node.get('name'))} | `{_cell(reference['repository'])}` | "
            f"`{_cell(reference['membership'])}` | [{entrypoint}]({entrypoint}) |"
        )
    lines.extend(["", "Explizit ohne aktive Fleet-Mitgliedschaft:", ""])
    for item in sorted(fleet_coverage["sourceExclusions"], key=lambda value: str(value.get("name", ""))):
        lines.append(f"- `{_cell(item.get('name'))}` — {_cell(item.get('reason'))}")

    organization_rows = organization_scope["repositories"]
    catalog_count = sum(item["classification"] == "catalog" for item in organization_rows)
    archived_references = sorted(
        (
            item
            for item in organization_rows
            if item["classification"] == "archived_reference"
        ),
        key=lambda item: str(item["name"]).casefold(),
    )
    excluded = sorted(
        (item for item in organization_rows if item["classification"] == "excluded"),
        key=lambda item: str(item["name"]).casefold(),
    )
    lines.extend([
        "", "## Organisationsumfang", "",
        f"Der GitHub-Snapshot umfasst {len(organization_rows)} nicht geforkte Repositories. "
        f"Davon sind {catalog_count} aktive Katalogsysteme, "
        f"{len(archived_references)} "
        f"{'archivierte Referenz' if len(archived_references) == 1 else 'archivierte Referenzen'} "
        f"und {len(excluded)} begründet ausgeschlossen.",
        "", "Archivierte Referenzen ohne aktive Betriebsautorität:", "",
    ])
    for item in archived_references:
        lines.append(
            f"- `{_cell(item['repository'])}` (`{_cell(item['visibility'])}`) — "
            f"{_cell(item['reason'])}"
        )
    lines.extend(["", "Begründete Ausschlüsse:", ""])
    for item in excluded:
        lines.append(
            f"- `{_cell(item['repository'])}` (`{_cell(item['visibility'])}`) — "
            f"{_cell(item['reason'])}"
        )

    lines.extend(["", "## Wahrheitszuständigkeiten", "", "| Bereich | Primärquelle | Nicht-autoritative Projektionen |", "|---|---|---|"])
    for item in sorted(authorities, key=lambda value: str(value.get("domain", ""))):
        projections = item.get("projections", [])
        rendered = ", ".join(str(value) for value in projections) if projections else "—"
        lines.append(f"| `{_cell(item.get('domain'))}` | `{_cell(item.get('owner'))}` | {_cell(rendered)} |")

    lines.extend([
        "", "## Stabile Beziehungen", "",
        "Nur Beziehungen der Klassen `stable`, `bounded` oder `related` werden angezeigt. Die Klasse beschreibt die Dauerhaftigkeit der Architekturbeziehung, nicht ihren aktuellen Betriebszustand. Resilienzfelder erscheinen nur für fachlich geprüfte, ausfall- oder autoritätsrelevante Kanten; `—` bedeutet nicht geprüft, nicht automatisch harmlos.",
        "", "| Von | Beziehung | Zu | Klasse | Kopplung | Ausfallpolitik | Autoritätsrichtung | Recovery | Bedeutung |", "|---|---|---|---|---|---|---|---|---|",
    ])
    for edge in sorted(edges, key=lambda item: (str(item.get("from", "")), str(item.get("type", "")), str(item.get("to", "")))):
        source = node_by_id.get(edge.get("from"), {})
        target = node_by_id.get(edge.get("to"), {})
        stable = resilience_by_relation.get((edge["from"], edge["to"], edge["type"]))
        lines.append(
            f"| {_cell(source.get('name') or edge.get('from'))} | `{_cell(edge.get('type'))}` | "
            f"{_cell(target.get('name') or edge.get('to'))} | `{_cell(edge.get('stability'))}` | "
            f"`{_cell(stable.get('coupling') if stable else '—')}` | "
            f"`{_cell(stable.get('failurePolicy') if stable else '—')}` | "
            f"`{_cell(stable.get('authorityDirection') if stable else '—')}` | "
            f"`{_cell((stable.get('recoveryModeRef') or '—') if stable else '—')}` | {_cell(edge.get('meaning'))} |"
        )

    lines.extend([
        "", "## Ausfalldomänen", "",
        "Ausfalldomänen beschreiben stabile gemeinsame Abhängigkeiten. Sie sind keine Aussage über aktuellen Ausfall oder Gesundheit.",
        "", "| ID | Art | Bedeutung |", "|---|---|---|",
    ])
    for item in sorted(resilience["failureDomains"], key=lambda value: value["id"]):
        lines.append(f"| `{_cell(item['id'])}` | `{_cell(item['kind'])}` | {_cell(item['meaning'])} |")

    lines.extend([
        "", "## Deklarierte Recoverymodi", "",
        "Ein Recoverymodus beschreibt einen zulässigen Pfad und seine gemeinsamen Fehlerursachen. Er belegt weder aktuelle Bereitschaft noch Ausführungsautorität.",
        "", "| Modus | System | Art | Unabhängigkeit | Gemeinsame Ausfalldomänen | Rückkehrbedingung |", "|---|---|---|---|---|---|",
    ])
    for item in sorted(resilience["recoveryModes"], key=lambda value: value["id"]):
        lines.append(
            f"| `{_cell(item['id'])}` | `{_cell(item['system'])}` | `{_cell(item['kind'])}` | "
            f"`{_cell(item['independence'])}` | {_string_list_cell(item['sharedFailureDomains'])} | "
            f"{_cell(item['returnCondition'])} |"
        )

    lines.extend(["", "## Einstiegspunkte", "", "| System | Einstieg |", "|---|---|"])
    for item in sorted(entrypoints, key=lambda value: str(value.get("label", "")).casefold()):
        label = _cell(item.get("label"))
        target = _cell(item.get("target"))
        lines.append(f"| {label} | [{target}]({_cell(_render_href(target))}) |")

    lines.extend([
        "", "## Grenzen", "",
        "- Aufgaben, Queue und Receipts: Bureau.",
        "- Repository-, PR- und Reviewzustand: GitHub.",
        "- Technische Prüfergebnisse: CI und Review-Gates.",
        "- Laufende Dienste: Runtime, Healthchecks, systemd und Logs.",
        "- Lokale und repositorybezogene Ausführung: Grabowski nach Freigabe.",
        "- Konkrete Runtime-Identitäten, Provider-Agenten und Topologie sind keine Katalogsysteme.",
        "- Die frühere Cabinet-Oberfläche ist archiviert; der Katalog wird ausschließlich als versionierte Markdown-, Mermaid- und JSON-Artefakte bereitgestellt.",
        "- Frühere dynamische Claims und Radarflächen sind historische Kompatibilität, keine aktuelle Katalogwahrheit.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    root = args.repo_root.resolve()
    expected = render_text(root)
    output = args.output if args.output.is_absolute() else root / args.output
    try:
        output.resolve().relative_to(root)
    except ValueError as exc:
        raise SystemExit(f"system catalog output escapes repository: {output}") from exc
    if args.check:
        actual = output.read_text(encoding="utf-8") if output.is_file() else None
        if actual != expected:
            raise SystemExit(f"system catalog projection is stale: {output}")
        print(json.dumps({"status": "valid", "output": str(output.relative_to(root))}, sort_keys=True))
        return 0
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(expected, encoding="utf-8")
    print(json.dumps({"status": "written", "output": str(output.relative_to(root))}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
