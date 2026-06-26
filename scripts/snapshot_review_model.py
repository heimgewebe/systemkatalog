from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SnapshotAssessment:
    repository: str
    relationship_class: str
    worktree_class: str
    evidence_class: str
    priority: int
    reason_code: str
    review_head: str
    import_head: str
    relationship: str
    import_worktree: str
    imported_at: str
    source_path: str


def relationship_kind(record: Any) -> tuple[str, str]:
    normalized = record.relationship.casefold()
    if record.review_head == record.import_head:
        return "snapshot-identical", "direct-head-equality"
    if any(word in normalized for word in ("divergent", "rewritten", "amended")):
        return "snapshot-divergence-claimed", "reference-claim"
    if "enthält" in normalized or "contains" in normalized:
        return "snapshot-review-contained", "reference-claim"
    return "snapshot-relationship-claimed", "reference-claim"


def assess_record(record: Any) -> SnapshotAssessment:
    relation, evidence = relationship_kind(record)
    state, raw_count = record.import_worktree.split(":", 1)
    count = int(raw_count)
    if relation == "snapshot-divergence-claimed":
        priority, reason = 1, "verify-divergence"
    elif state == "dirty":
        priority, reason = 2, f"refresh-dirty-{count}"
    elif relation in {"snapshot-review-contained", "snapshot-relationship-claimed"}:
        priority, reason = 3, "verify-nonidentical"
    else:
        priority, reason = 4, "routine"
    return SnapshotAssessment(
        repository=record.repository,
        relationship_class=relation,
        worktree_class=f"snapshot-{state}-at-import",
        evidence_class=evidence,
        priority=priority,
        reason_code=reason,
        review_head=record.review_head,
        import_head=record.import_head,
        relationship=record.relationship,
        import_worktree=record.import_worktree,
        imported_at=record.imported_at,
        source_path=record.source_path,
    )


def build_assessments(records: list[Any]) -> list[SnapshotAssessment]:
    return [assess_record(record) for record in records]


def priority_order(items: list[SnapshotAssessment]) -> list[SnapshotAssessment]:
    return sorted(
        items,
        key=lambda item: (item.priority, item.repository.casefold(), item.repository),
    )
