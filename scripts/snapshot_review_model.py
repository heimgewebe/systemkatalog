from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol

RelationshipClass = Literal[
    "snapshot-identical",
    "snapshot-review-contained",
    "snapshot-divergence-claimed",
    "snapshot-relationship-claimed",
]
WorktreeClass = Literal[
    "snapshot-clean-at-import",
    "snapshot-dirty-at-import",
]
EvidenceStatus = Literal["direct-head-equality", "reference-claim"]
ReasonCode = Literal[
    "verify-divergence",
    "refresh-dirty",
    "verify-nonidentical",
    "routine",
]

CONTAINED_RELATIONSHIPS = frozenset(
    {
        "live-stand enthält review-stand",
    }
)
DIVERGENCE_RELATIONSHIPS = frozenset(
    {
        "divergent oder rewritten/amended",
    }
)


class SnapshotRecord(Protocol):
    repository: str
    review_head: str
    import_head: str
    relationship: str
    import_worktree: str
    imported_at: str
    source_path: str


@dataclass(frozen=True)
class SnapshotAssessment:
    repository: str
    relationship_class: RelationshipClass
    worktree_class: WorktreeClass
    evidence_status: EvidenceStatus
    priority: int
    reason_code: ReasonCode
    change_count: int
    review_head: str
    import_head: str
    relationship: str
    import_worktree: str
    imported_at: str
    source_path: str


def _normalize_relationship(value: str) -> str:
    return " ".join(value.casefold().split())


def relationship_kind(record: SnapshotRecord) -> tuple[RelationshipClass, EvidenceStatus]:
    if record.review_head == record.import_head:
        return "snapshot-identical", "direct-head-equality"

    normalized = _normalize_relationship(record.relationship)
    if normalized in DIVERGENCE_RELATIONSHIPS:
        return "snapshot-divergence-claimed", "reference-claim"
    if normalized in CONTAINED_RELATIONSHIPS:
        return "snapshot-review-contained", "reference-claim"
    return "snapshot-relationship-claimed", "reference-claim"


def assess_record(record: SnapshotRecord) -> SnapshotAssessment:
    relation, evidence = relationship_kind(record)
    state, raw_count = record.import_worktree.split(":", 1)
    count = int(raw_count)
    if state not in {"clean", "dirty"}:
        raise ValueError(f"unsupported snapshot worktree state: {state!r}")

    if relation == "snapshot-divergence-claimed":
        priority: int = 1
        reason: ReasonCode = "verify-divergence"
    elif state == "dirty":
        priority = 2
        reason = "refresh-dirty"
    elif relation in {
        "snapshot-review-contained",
        "snapshot-relationship-claimed",
    }:
        priority = 3
        reason = "verify-nonidentical"
    else:
        priority = 4
        reason = "routine"

    worktree_class: WorktreeClass = (
        "snapshot-dirty-at-import"
        if state == "dirty"
        else "snapshot-clean-at-import"
    )
    return SnapshotAssessment(
        repository=record.repository,
        relationship_class=relation,
        worktree_class=worktree_class,
        evidence_status=evidence,
        priority=priority,
        reason_code=reason,
        change_count=count,
        review_head=record.review_head,
        import_head=record.import_head,
        relationship=record.relationship,
        import_worktree=record.import_worktree,
        imported_at=record.imported_at,
        source_path=record.source_path,
    )


def build_assessments(
    records: list[SnapshotRecord],
) -> list[SnapshotAssessment]:
    return [assess_record(record) for record in records]


def priority_order(
    items: list[SnapshotAssessment],
) -> list[SnapshotAssessment]:
    return sorted(
        items,
        key=lambda item: (
            item.priority,
            item.repository.casefold(),
            item.repository,
        ),
    )
