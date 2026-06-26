from dataclasses import dataclass


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
