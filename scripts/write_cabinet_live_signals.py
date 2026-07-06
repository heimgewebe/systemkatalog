#!/usr/bin/env python3
from __future__ import annotations

import argparse, json
from datetime import datetime, timezone
from pathlib import Path

from validate_ecosystem_signals import (
    CONTRACT_PATH, CONTRACT_VERSION, DOES_NOT_ESTABLISH, EFFECT_FLAGS, KIND, SCHEMA_PATH, validate_signal
)
from write_cabinet_maintenance_report import build_report

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = Path('registry/ecosystem/external-dump-sources.json')
DEFAULT_OUTPUT = Path('pruefung/10 Laeufe/cab-qa-007-live-signal-producer-v0.jsonl')


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


def flags() -> dict[str, bool]:
    return {key: False for key in EFFECT_FLAGS}


def make_signal(*, signal_id, observed_at, subject, predicate, object_value, evidence, confidence=0.84):
    row = {
        'schemaVersion': 1,
        'kind': KIND,
        'contractVersion': CONTRACT_VERSION,
        'contractPath': CONTRACT_PATH,
        'schemaPath': SCHEMA_PATH,
        'id': signal_id,
        'observedAt': observed_at,
        'sourceSystem': 'local_git',
        'subject': subject,
        'predicate': predicate,
        'object': object_value,
        'evidence': evidence,
        'freshness': {'basis': 'observedAt', 'maxAgeHours': 24},
        'confidence': confidence,
        'effectFlags': flags(),
        'doesNotEstablish': list(DOES_NOT_ESTABLISH),
    }
    validate_signal(row)
    return row


def source_rows(registry: dict, observed_at: str) -> list[dict]:
    rows = []
    for source in registry.get('sources', []):
        family = str(source.get('artifactFamily') or 'unknown')
        obs = source.get('observation') if isinstance(source.get('observation'), dict) else {}
        status = str(obs.get('status') or 'unknown')
        generated = str(obs.get('latestManifestGeneratedAt') or 'unobserved')
        evidence = {
            'type': 'external_dump_source_registry',
            'ref': str(REGISTRY),
            'sourceId': str(source.get('id') or ''),
            'artifactFamily': family,
            'status': status,
        }
        if obs.get('latestManifestPath'):
            evidence['latestManifestPath'] = obs['latestManifestPath']
        if obs.get('latestManifestGeneratedAt'):
            evidence['latestManifestGeneratedAt'] = obs['latestManifestGeneratedAt']
        rows.append(make_signal(
            signal_id=f'signal:local_git:cabinet:external-dump:{family}:manifest:{status}:{generated}',
            observed_at=observed_at,
            subject=f'external-dump:{family}:cabinet/main',
            predicate='external_dump_manifest_status',
            object_value=status,
            evidence=[evidence],
            confidence=0.86 if status == 'observed' else 0.72,
        ))
    return rows


def report_row(report: dict, observed_at: str) -> dict:
    summary = report.get('summary') if isinstance(report.get('summary'), dict) else {}
    status = str(summary.get('status') or 'unknown')
    source = report.get('source') if isinstance(report.get('source'), dict) else {}
    commit = str(source.get('commit') or 'unknown')
    return make_signal(
        signal_id=f'signal:local_git:cabinet:maintenance-report:status:{status}:{commit[:12]}',
        observed_at=observed_at,
        subject='repo:cabinet',
        predicate='cabinet_maintenance_report_status',
        object_value=status,
        evidence=[{
            'type': 'cabinet_maintenance_report',
            'ref': 'scripts/write_cabinet_maintenance_report.py',
            'status': status,
            'findingCount': summary.get('findingCount'),
            'epistemicGapCount': summary.get('epistemicGapCount'),
            'sourceCommit': commit,
        }],
    )


def build_rows(repo_root: Path, observed_at: str | None = None) -> list[dict]:
    observed_at = observed_at or now_utc()
    registry = json.loads((repo_root / REGISTRY).read_text(encoding='utf-8'))
    rows = source_rows(registry, observed_at)
    rows.append(report_row(build_report(repo_root, generated_at=observed_at), observed_at))
    return rows


def write_jsonl(rows: list[dict], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(''.join(json.dumps(row, sort_keys=True) + '\n' for row in rows), encoding='utf-8')


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo-root', type=Path, default=ROOT)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--observed-at')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args(argv)
    repo_root = args.repo_root.resolve()
    rows = build_rows(repo_root, args.observed_at)
    output = args.output
    if output is not None:
        output = output if output.is_absolute() else repo_root / output
        write_jsonl(rows, output)
    if args.json:
        print(json.dumps({'ok': True, 'kind': KIND, 'signalCount': len(rows), 'output': str(output) if output else None}, sort_keys=True))
    elif output is None:
        for row in rows:
            print(json.dumps(row, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
