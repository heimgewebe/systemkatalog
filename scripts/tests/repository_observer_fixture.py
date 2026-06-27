from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

import repository_observer as observer


def run(*args: str) -> bytes:
    return subprocess.run(
        list(args), check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    ).stdout


class ObserverFixture:
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.cabinet = self.root / "cabinet"
        self.sources = self.root / "repos"
        (self.cabinet / "policy").mkdir(parents=True)
        self.sources.mkdir()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def make_reference(self, repository_id: str, remote: str) -> str:
        relative = Path("references") / repository_id / "Repository Reference.md"
        path = self.cabinet / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "\n".join(
                [
                    f"# {repository_id}",
                    "",
                    "| Feld | Wert |",
                    "|---|---|",
                    f"| Repository | `{repository_id}` |",
                    f"| Remote | `{remote}` |",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return relative.as_posix()

    def entry(self, repository_id: str) -> dict[str, str]:
        remote = f"github.com:heimgewebe/{repository_id}.git"
        return {
            "id": repository_id,
            "directory": repository_id,
            "expected_remote": remote,
            "reference": self.make_reference(repository_id, remote),
        }

    def write_policy(self, repositories: list[dict[str, str]]) -> Path:
        relative = Path("policy/repository-observation.json")
        (self.cabinet / relative).write_text(
            json.dumps(
                {"schema": observer.POLICY_SCHEMA, "repositories": repositories},
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        return relative

    def make_repository(
        self,
        repository_id: str,
        *,
        remote: str | None = None,
        dirty: bool = False,
        detached: bool = False,
    ) -> Path:
        path = self.sources / repository_id
        run("git", "init", "-q", "-b", "main", str(path))
        run("git", "-C", str(path), "config", "user.name", "Observer Test")
        run("git", "-C", str(path), "config", "user.email", "observer@example.invalid")
        (path / "README.md").write_text("initial\n", encoding="utf-8")
        run("git", "-C", str(path), "add", "README.md")
        run("git", "-C", str(path), "commit", "-q", "-m", "initial")
        run(
            "git",
            "-C",
            str(path),
            "remote",
            "add",
            "origin",
            remote or f"git@github.com:heimgewebe/{repository_id}.git",
        )
        if detached:
            run("git", "-C", str(path), "checkout", "-q", "--detach", "HEAD")
        if dirty:
            (path / "dirty.txt").write_text("dirty\n", encoding="utf-8")
        return path
