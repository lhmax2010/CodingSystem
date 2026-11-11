"""Scan current files and all proposed commit messages using only the standard library."""

from __future__ import annotations

import subprocess
import sys

from ci.checks import check_content, content_hits, git, json_file


def check_updates(updates: str) -> int:
    """Use Git's exact pre-push ref updates, including new branches and annotated tags."""
    failures = check_content()
    rules = json_file("ci/content_policy.json")["rules"]
    commits: set[str] = set()
    for line in updates.splitlines():
        fields = line.split()
        if len(fields) != 4:
            raise ValueError("Expected pre-push ref update")
        _, local, _, remote = fields
        if set(local) == {"0"}:
            continue
        kind = git("cat-file", "-t", local).strip()
        if kind == b"tag":
            for rule, lineno in content_hits(git("cat-file", "tag", local), rules):
                print(f"PUSH_TAG_FAIL {local}:{lineno} rule={rule}")
                failures = 1
        args = ["rev-list", local]
        if set(remote) != {"0"}:
            # An unavailable remote object must not cause a message to be omitted.
            exists = subprocess.run(["git", "cat-file", "-e", remote], capture_output=True)
            if exists.returncode == 0:
                args += ["^" + remote]
        commits.update(git(*args).decode().splitlines())
    for commit in sorted(commits):
        message = git("show", "-s", "--format=%B", commit)
        for rule, lineno in content_hits(message, rules):
            print(f"PUSH_MESSAGE_FAIL {commit}:{lineno} rule={rule}")
            failures = 1
    print(f"Pre-push commits checked: {len(commits)}; result={'fail' if failures else 'pass'}")
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(check_updates(sys.stdin.read()))
