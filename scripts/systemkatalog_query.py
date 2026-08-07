#!/usr/bin/env python3
"""Deterministic read-only queries over the versioned Systemkatalog registry."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CATALOG_REPOSITORY = "heimgewebe/systemkatalog"
MANIFEST_PATH = "rendered/ecosystem-map-artifact-manifest.json"
NON_CLAIMS = [
    "runtime_health",
    "task_status",
    "pull_request_state",
    "ci_state",
    "merge_readiness",
    "execution_permission",
    "current_recovery_readiness",
    "automatic_failover_authority",
    "current_external_truth",
    "catalog_semantic_completeness",
    "consumer_view_correctness",
]
COMMAND_SOURCE_PATHS: dict[str, tuple[str, ...]] = {
    "system": (
        "registry/ecosystem/nodes.json",
        "registry/ecosystem/source-bindings.v1.json",
        "registry/ecosystem/resilience.v1.json",
    ),
    "repository": (
        "registry/ecosystem/nodes.json",
        "registry/ecosystem/source-bindings.v1.json",
        "registry/ecosystem/resilience.v1.json",
    ),
    "entrypoints": (
        "registry/ecosystem/nodes.json",
        "registry/ecosystem/source-bindings.v1.json",
        "registry/ecosystem/resilience.v1.json",
    ),
    "relations": (
        "registry/ecosystem/nodes.json",
        "registry/ecosystem/edges.json",
        "registry/ecosystem/source-bindings.v1.json",
        "registry/ecosystem/resilience.v1.json",
    ),
    "truth-owner": (
        "registry/ecosystem/nodes.json",
        "registry/ecosystem/authority-matrix.v1.json",
        "registry/ecosystem/source-bindings.v1.json",
        "registry/ecosystem/resilience.v1.json",
    ),
    "authority-matrix": ("registry/ecosystem/authority-matrix.v1.json",),
    "failure-domain": ("registry/ecosystem/resilience.v1.json",),
    "recovery-mode": ("registry/ecosystem/resilience.v1.json",),
    "manifest": (MANIFEST_PATH,),
}


class CatalogQueryError(RuntimeError):
    """Typed fail-closed query error."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        path: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.path = path
        self.details = details or {}


def _commit(root: Path) -> str | None:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    candidate = result.stdout.strip() if result.returncode == 0 else ""
    return candidate if len(candidate) == 40 else None


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _read_document(root: Path, relative: str) -> tuple[dict[str, Any], dict[str, Any]]:
    path = root / relative
    try:
        payload = path.read_bytes()
    except FileNotFoundError as exc:
        raise CatalogQueryError(
            "source_missing",
            f"required catalog source is missing: {relative}",
            path=relative,
        ) from exc
    except OSError as exc:
        raise CatalogQueryError(
            "source_unreadable",
            f"required catalog source is unreadable: {relative}",
            path=relative,
            details={"errorType": type(exc).__name__},
        ) from exc
    try:
        value = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CatalogQueryError(
            "source_malformed",
            f"required catalog source is not valid UTF-8 JSON: {relative}",
            path=relative,
            details={"errorType": type(exc).__name__},
        ) from exc
    if not isinstance(value, dict):
        raise CatalogQueryError(
            "source_malformed",
            f"{relative}: root must be an object",
            path=relative,
        )
    evidence = {
        "path": relative,
        "sha256": _sha256(payload),
        "bytes": len(payload),
        "documentSchemaVersion": value.get("schemaVersion", value.get("schema_version")),
        "documentKind": value.get("kind"),
    }
    return value, evidence


def _required_list(
    document: dict[str, Any],
    key: str,
    *,
    path: str,
) -> list[Any]:
    value = document.get(key)
    if not isinstance(value, list):
        raise CatalogQueryError(
            "source_malformed",
            f"{path}: {key} must be an array",
            path=path,
            details={"field": key},
        )
    return value


def _normal(value: str) -> str:
    return "".join(ch for ch in value.casefold() if ch.isalnum())


def _documents(
    root: Path,
    command: str,
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    source_paths = COMMAND_SOURCE_PATHS.get(command)
    if source_paths is None:
        raise CatalogQueryError(
            "unsupported_command",
            f"unsupported command: {command}",
            details={"command": command},
        )
    documents: dict[str, dict[str, Any]] = {}
    evidence: list[dict[str, Any]] = []
    for relative in source_paths:
        document, identity = _read_document(root, relative)
        documents[relative] = document
        evidence.append(identity)
    return documents, evidence


def _manifest_identity(root: Path) -> dict[str, Any]:
    manifest, evidence = _read_document(root, MANIFEST_PATH)
    if manifest.get("kind") != "system_catalog_map_artifact_manifest":
        raise CatalogQueryError(
            "source_malformed",
            f"{MANIFEST_PATH}: kind must identify the Systemkatalog artifact manifest",
            path=MANIFEST_PATH,
            details={"field": "kind"},
        )
    contract_version = manifest.get("contractVersion")
    if not isinstance(contract_version, str) or not contract_version:
        raise CatalogQueryError(
            "source_malformed",
            f"{MANIFEST_PATH}: contractVersion must be a non-empty string",
            path=MANIFEST_PATH,
            details={"field": "contractVersion"},
        )
    source = manifest.get("source")
    if not isinstance(source, dict):
        raise CatalogQueryError(
            "source_malformed",
            f"{MANIFEST_PATH}: source must be an object",
            path=MANIFEST_PATH,
            details={"field": "source"},
        )
    repository = source.get("repository")
    if not isinstance(repository, str) or not repository:
        raise CatalogQueryError(
            "source_malformed",
            f"{MANIFEST_PATH}: source.repository must be a non-empty string",
            path=MANIFEST_PATH,
            details={"field": "source.repository"},
        )
    if repository != CATALOG_REPOSITORY:
        raise CatalogQueryError(
            "inconsistent_catalog",
            f"{MANIFEST_PATH}: source.repository does not match the catalog repository",
            path=MANIFEST_PATH,
            details={
                "field": "source.repository",
                "expected": CATALOG_REPOSITORY,
                "actual": repository,
            },
        )
    commit = source.get("commit")
    if (
        not isinstance(commit, str)
        or len(commit) != 40
        or any(character not in "0123456789abcdef" for character in commit)
    ):
        raise CatalogQueryError(
            "source_malformed",
            f"{MANIFEST_PATH}: source.commit must be a lowercase 40-character Git object id",
            path=MANIFEST_PATH,
            details={"field": "source.commit"},
        )
    generated_at = source.get("generatedAt")
    if not isinstance(generated_at, str) or not generated_at:
        raise CatalogQueryError(
            "source_malformed",
            f"{MANIFEST_PATH}: source.generatedAt must be a non-empty string",
            path=MANIFEST_PATH,
            details={"field": "source.generatedAt"},
        )
    return {
        **evidence,
        "contractVersion": contract_version,
        "source": {
            "repository": repository,
            "commit": commit,
            "generatedAt": generated_at,
        },
    }


def _node(nodes: list[Any], query_value: str) -> dict[str, Any]:
    wanted = _normal(query_value)
    matches: list[dict[str, Any]] = []
    for candidate in nodes:
        if not isinstance(candidate, dict):
            raise CatalogQueryError(
                "source_malformed",
                "registry/ecosystem/nodes.json: every node must be an object",
                path="registry/ecosystem/nodes.json",
            )
        aliases = {str(candidate.get("id", "")), str(candidate.get("name", ""))}
        entrypoints = candidate.get("entrypoints")
        if candidate.get("type") == "repository" and isinstance(entrypoints, dict):
            repository = entrypoints.get("repository")
            if isinstance(repository, str):
                aliases.add(repository.rstrip("/").split("/")[-1])
        if wanted in {_normal(alias) for alias in aliases if alias}:
            matches.append(candidate)
    if len(matches) != 1:
        raise CatalogQueryError(
            "query_not_unique",
            f"system query must resolve exactly once: {query_value} ({len(matches)} matches)",
            details={"query": query_value, "matchCount": len(matches)},
        )
    return matches[0]


def _index_unique(
    items: list[Any],
    key_name: str,
    *,
    path: str,
) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for item in items:
        if not isinstance(item, dict) or not isinstance(item.get(key_name), str):
            raise CatalogQueryError(
                "source_malformed",
                f"{path}: every item must contain string field {key_name}",
                path=path,
                details={"field": key_name},
            )
        key = item[key_name]
        if key in result:
            raise CatalogQueryError(
                "inconsistent_catalog",
                f"{path}: duplicate {key_name}: {key}",
                path=path,
                details={"field": key_name, "value": key},
            )
        result[key] = item
    return result


def _require_indexed(
    index: dict[str, dict[str, Any]],
    key: str,
    *,
    path: str,
    relationship: str,
) -> dict[str, Any]:
    value = index.get(key)
    if value is None:
        raise CatalogQueryError(
            "inconsistent_catalog",
            f"{path}: missing {relationship} for {key}",
            path=path,
            details={"key": key, "relationship": relationship},
        )
    return value


def _system_indexes(
    documents: dict[str, dict[str, Any]],
) -> tuple[
    list[Any],
    dict[str, dict[str, Any]],
    dict[str, dict[str, Any]],
]:
    nodes_path = "registry/ecosystem/nodes.json"
    sources_path = "registry/ecosystem/source-bindings.v1.json"
    resilience_path = "registry/ecosystem/resilience.v1.json"
    nodes = _required_list(documents[nodes_path], "nodes", path=nodes_path)
    sources = _required_list(documents[sources_path], "systems", path=sources_path)
    resilience = _required_list(
        documents[resilience_path], "systems", path=resilience_path
    )
    return (
        nodes,
        _index_unique(sources, "system", path=sources_path),
        _index_unique(resilience, "system", path=resilience_path),
    )


def _relation_key(item: dict[str, Any], *, path: str) -> tuple[str, str, str]:
    relation = item.get("relation", item)
    if not isinstance(relation, dict):
        raise CatalogQueryError(
            "source_malformed",
            f"{path}: relation must be an object",
            path=path,
        )
    values = tuple(relation.get(field) for field in ("from", "to", "type"))
    if not all(isinstance(value, str) and value for value in values):
        raise CatalogQueryError(
            "source_malformed",
            f"{path}: relation requires from, to and type strings",
            path=path,
        )
    return values  # type: ignore[return-value]


def _relation_index(
    items: list[Any],
    *,
    path: str,
) -> dict[tuple[str, str, str], dict[str, Any]]:
    result: dict[tuple[str, str, str], dict[str, Any]] = {}
    for item in items:
        if not isinstance(item, dict):
            raise CatalogQueryError(
                "source_malformed",
                f"{path}: every relation item must be an object",
                path=path,
            )
        key = _relation_key(item, path=path)
        if key in result:
            raise CatalogQueryError(
                "inconsistent_catalog",
                f"{path}: duplicate relation {key}",
                path=path,
            )
        result[key] = item
    return result


def _validate_manifest_artifacts(
    root: Path,
    manifest: dict[str, Any],
) -> list[dict[str, Any]]:
    artifacts = _required_list(manifest, "artifacts", path=MANIFEST_PATH)
    checks: list[dict[str, Any]] = []
    mismatches: list[dict[str, Any]] = []
    for artifact in artifacts:
        if not isinstance(artifact, dict):
            raise CatalogQueryError(
                "source_malformed",
                f"{MANIFEST_PATH}: every artifact must be an object",
                path=MANIFEST_PATH,
            )
        relative = artifact.get("path")
        expected_sha256 = artifact.get("sha256")
        expected_bytes = artifact.get("bytes")
        if (
            not isinstance(relative, str)
            or not isinstance(expected_sha256, str)
            or not isinstance(expected_bytes, int)
        ):
            raise CatalogQueryError(
                "source_malformed",
                f"{MANIFEST_PATH}: artifact path, sha256 and bytes are required",
                path=MANIFEST_PATH,
            )
        artifact_path = root / relative
        try:
            payload = artifact_path.read_bytes()
        except FileNotFoundError:
            mismatches.append(
                {
                    "path": relative,
                    "reason": "missing",
                    "expectedSha256": expected_sha256,
                    "expectedBytes": expected_bytes,
                }
            )
            continue
        actual = {
            "path": relative,
            "sha256": _sha256(payload),
            "bytes": len(payload),
        }
        checks.append(actual)
        if actual["sha256"] != expected_sha256 or actual["bytes"] != expected_bytes:
            mismatches.append(
                {
                    **actual,
                    "reason": "content_mismatch",
                    "expectedSha256": expected_sha256,
                    "expectedBytes": expected_bytes,
                }
            )
    if mismatches:
        raise CatalogQueryError(
            "artifact_manifest_stale",
            "artifact manifest does not match the current published artifact bytes",
            path=MANIFEST_PATH,
            details={"mismatches": mismatches},
        )
    return checks


def _result_for(
    root: Path,
    command: str,
    value: str | None,
    documents: dict[str, dict[str, Any]],
) -> Any:
    nodes_path = "registry/ecosystem/nodes.json"
    edges_path = "registry/ecosystem/edges.json"
    authority_path = "registry/ecosystem/authority-matrix.v1.json"
    sources_path = "registry/ecosystem/source-bindings.v1.json"
    resilience_path = "registry/ecosystem/resilience.v1.json"

    if command in {"system", "repository", "entrypoints", "relations"}:
        if value is None:
            raise CatalogQueryError(
                "query_value_missing",
                f"{command} requires a query value",
                details={"command": command},
            )
        nodes, source_by_system, resilience_by_system = _system_indexes(documents)
        node = _node(nodes, value)
        node_id = node.get("id")
        if not isinstance(node_id, str):
            raise CatalogQueryError(
                "source_malformed",
                f"{nodes_path}: node id must be a string",
                path=nodes_path,
            )
        source_binding = _require_indexed(
            source_by_system,
            node_id,
            path=sources_path,
            relationship="source binding",
        )
        resilience = _require_indexed(
            resilience_by_system,
            node_id,
            path=resilience_path,
            relationship="resilience semantics",
        )
        if command == "system":
            return {
                "system": node,
                "sourceBinding": source_binding,
                "resilience": resilience,
            }
        if command == "repository":
            if node.get("type") != "repository":
                raise CatalogQueryError(
                    "query_type_mismatch",
                    f"not a repository system: {node_id}",
                    details={"system": node_id, "expectedType": "repository"},
                )
            entrypoints = node.get("entrypoints")
            repository = (
                entrypoints.get("repository")
                if isinstance(entrypoints, dict)
                else None
            )
            if not isinstance(repository, str):
                raise CatalogQueryError(
                    "inconsistent_catalog",
                    f"{nodes_path}: repository entrypoint missing for {node_id}",
                    path=nodes_path,
                    details={"system": node_id},
                )
            return {
                "system": node,
                "repository": repository,
                "sourceBinding": source_binding,
                "resilience": resilience,
            }
        if command == "entrypoints":
            entrypoints = node.get("entrypoints")
            if not isinstance(entrypoints, dict):
                raise CatalogQueryError(
                    "inconsistent_catalog",
                    f"{nodes_path}: entrypoints missing for {node_id}",
                    path=nodes_path,
                    details={"system": node_id},
                )
            return {
                "system": {
                    "id": node_id,
                    "name": node.get("name"),
                    "type": node.get("type"),
                },
                "entrypoints": entrypoints,
                "sourceBinding": source_binding,
                "resilience": resilience,
            }

        edges = _required_list(documents[edges_path], "edges", path=edges_path)
        relation_sources = _required_list(
            documents[sources_path], "relations", path=sources_path
        )
        relation_resilience = _required_list(
            documents[resilience_path], "relations", path=resilience_path
        )
        source_by_relation = _relation_index(relation_sources, path=sources_path)
        resilience_by_relation = _relation_index(
            relation_resilience, path=resilience_path
        )
        relations = []
        for edge in edges:
            if not isinstance(edge, dict):
                raise CatalogQueryError(
                    "source_malformed",
                    f"{edges_path}: every edge must be an object",
                    path=edges_path,
                )
            key = _relation_key(edge, path=edges_path)
            if node_id not in {key[0], key[1]}:
                continue
            source = source_by_relation.get(key)
            if source is None:
                raise CatalogQueryError(
                    "inconsistent_catalog",
                    f"{sources_path}: missing source binding for relation {key}",
                    path=sources_path,
                    details={"relation": list(key)},
                )
            relations.append(
                {
                    "relation": edge,
                    "sourceBinding": source,
                    "resilience": resilience_by_relation.get(key),
                }
            )
        return {
            "system": {"id": node_id, "name": node.get("name")},
            "relations": relations,
        }

    if command == "truth-owner":
        if value is None:
            raise CatalogQueryError(
                "query_value_missing",
                "truth-owner requires a query value",
                details={"command": command},
            )
        nodes, source_by_system, resilience_by_system = _system_indexes(documents)
        authorities = _required_list(
            documents[authority_path], "authorities", path=authority_path
        )
        matches = [
            item
            for item in authorities
            if isinstance(item, dict)
            and isinstance(item.get("domain"), str)
            and _normal(item["domain"]) == _normal(value)
        ]
        if len(matches) != 1:
            raise CatalogQueryError(
                "query_not_unique",
                f"truth-owner query must resolve exactly once: {value} ({len(matches)} matches)",
                details={"query": value, "matchCount": len(matches)},
            )
        authority = matches[0]
        domain = authority["domain"]
        owners = [
            candidate
            for candidate in nodes
            if isinstance(candidate, dict)
            and isinstance(candidate.get("truthOwnership"), list)
            and domain in candidate["truthOwnership"]
        ]
        if len(owners) != 1:
            raise CatalogQueryError(
                "inconsistent_catalog",
                f"truth ownership for {domain} must resolve exactly once ({len(owners)} matches)",
                path=nodes_path,
                details={
                    "domain": domain,
                    "owners": [item.get("id") for item in owners],
                    "matchCount": len(owners),
                },
            )
        owner = owners[0]
        owner_id = owner.get("id")
        if not isinstance(owner_id, str):
            raise CatalogQueryError(
                "source_malformed",
                f"{nodes_path}: truth owner id must be a string",
                path=nodes_path,
                details={"domain": domain},
            )
        return {
            "authority": authority,
            "ownerSystem": owner,
            "ownerSourceBinding": _require_indexed(
                source_by_system,
                owner_id,
                path=sources_path,
                relationship="owner source binding",
            ),
            "ownerResilience": _require_indexed(
                resilience_by_system,
                owner_id,
                path=resilience_path,
                relationship="owner resilience semantics",
            ),
        }

    if command == "authority-matrix":
        return {
            "authorities": _required_list(
                documents[authority_path], "authorities", path=authority_path
            )
        }

    if command in {"failure-domain", "recovery-mode"}:
        if value is None:
            raise CatalogQueryError(
                "query_value_missing",
                f"{command} requires a query value",
                details={"command": command},
            )
        resilience = documents[resilience_path]
        systems = _required_list(resilience, "systems", path=resilience_path)
        failure_domains = _index_unique(
            _required_list(resilience, "failureDomains", path=resilience_path),
            "id",
            path=resilience_path,
        )
        recovery_modes = _index_unique(
            _required_list(resilience, "recoveryModes", path=resilience_path),
            "id",
            path=resilience_path,
        )
        if command == "failure-domain":
            domain = failure_domains.get(value)
            if domain is None:
                raise CatalogQueryError(
                    "query_not_found",
                    f"unknown failure domain: {value}",
                    details={"query": value},
                )
            return {
                "failureDomain": domain,
                "systems": sorted(
                    item["system"]
                    for item in systems
                    if isinstance(item, dict)
                    and isinstance(item.get("system"), str)
                    and isinstance(item.get("failureDomains"), list)
                    and value in item["failureDomains"]
                ),
                "recoveryModes": sorted(
                    item["id"]
                    for item in recovery_modes.values()
                    if isinstance(item.get("failureDomains"), list)
                    and value in item["failureDomains"]
                ),
            }
        mode = recovery_modes.get(value)
        if mode is None:
            raise CatalogQueryError(
                "query_not_found",
                f"unknown recovery mode: {value}",
                details={"query": value},
            )
        return mode

    if command == "manifest":
        manifest = documents[MANIFEST_PATH]
        return {
            "manifest": manifest,
            "artifactChecks": _validate_manifest_artifacts(root, manifest),
        }

    raise CatalogQueryError(
        "unsupported_command",
        f"unsupported command: {command}",
        details={"command": command},
    )


def _envelope(
    root: Path,
    command: str,
    value: str | None,
    result: Any,
    evidence: list[dict[str, Any]],
) -> dict[str, Any]:
    catalog_commit = _commit(root)
    return {
        "schemaVersion": 2,
        "kind": "system_catalog_query_result",
        "status": "ok",
        "command": command,
        "query": {"value": value},
        "catalogRepository": CATALOG_REPOSITORY,
        "catalogCommit": catalog_commit,
        "catalogIdentity": {
            "repository": CATALOG_REPOSITORY,
            "commit": catalog_commit,
            "artifactManifest": _manifest_identity(root),
        },
        "result": result,
        "sourcePaths": [item["path"] for item in evidence],
        "sourceEvidence": evidence,
        "doesNotEstablish": NON_CLAIMS,
    }


def query(
    root: Path,
    command: str,
    value: str | None = None,
) -> dict[str, Any]:
    documents, evidence = _documents(root, command)
    result = _result_for(root, command, value, documents)
    return _envelope(root, command, value, result, evidence)


def _error_envelope(
    root: Path,
    command: str,
    value: str | None,
    error: CatalogQueryError,
) -> dict[str, Any]:
    return {
        "schemaVersion": 2,
        "kind": "system_catalog_query_error",
        "status": "degraded",
        "command": command,
        "query": {"value": value},
        "catalogRepository": CATALOG_REPOSITORY,
        "catalogCommit": _commit(root),
        "error": {
            "code": error.code,
            "message": str(error),
            "path": error.path,
            "details": error.details,
        },
        "doesNotEstablish": NON_CLAIMS,
    }


def query_safe(
    root: Path,
    command: str,
    value: str | None = None,
) -> dict[str, Any]:
    try:
        return query(root, command, value)
    except CatalogQueryError as exc:
        return _error_envelope(root, command, value, exc)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        return _error_envelope(
            root,
            command,
            value,
            CatalogQueryError(
                "unexpected_catalog_error",
                "catalog query failed closed",
                details={"errorType": type(exc).__name__},
            ),
        )


def _text(value: Any, indent: int = 0) -> str:
    prefix = " " * indent
    if isinstance(value, dict):
        lines = []
        for key, item in value.items():
            if isinstance(item, (dict, list)):
                lines.append(f"{prefix}{key}:")
                lines.append(_text(item, indent + 2))
            else:
                lines.append(f"{prefix}{key}: {item}")
        return "\n".join(lines)
    if isinstance(value, list):
        return "\n".join(
            f"{prefix}- {_text(item, indent + 2).lstrip()}" for item in value
        )
    return f"{prefix}{value}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--format", choices=("json", "text"), default="json")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in (
        "system",
        "repository",
        "entrypoints",
        "relations",
        "truth-owner",
        "failure-domain",
        "recovery-mode",
    ):
        child = sub.add_parser(name)
        child.add_argument("value")
    sub.add_parser("authority-matrix")
    sub.add_parser("manifest")
    args = parser.parse_args()
    result = query_safe(
        args.root.resolve(),
        args.command,
        getattr(args, "value", None),
    )
    print(
        json.dumps(result, ensure_ascii=False, sort_keys=True)
        if args.format == "json"
        else _text(result)
    )
    return 0 if result["status"] == "ok" else 3


if __name__ == "__main__":
    raise SystemExit(main())
