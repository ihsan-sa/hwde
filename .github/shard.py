"""Print the test files of CI shard K of N (usage: shard.py K N), 1-based.

Every tests/test_*.py goes to exactly one shard. Files are weighed by their
seconds in .github/test-times.json when it lists them, else by their line count
scaled to seconds, and dealt heaviest first to the lightest shard so far.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SECONDS_PER_LINE = 0.1


def shards(n: int) -> list[list[str]]:
    times_file = ROOT / ".github" / "test-times.json"
    times = json.loads(times_file.read_text()) if times_file.exists() else {}
    files = sorted(p.relative_to(ROOT).as_posix() for p in (ROOT / "tests").glob("test_*.py"))
    weight = {f: times.get(f, len((ROOT / f).read_text(encoding="utf-8").splitlines()) * SECONDS_PER_LINE)
              for f in files}
    out: list[list[str]] = [[] for _ in range(n)]
    load = [0.0] * n
    for f in sorted(files, key=lambda f: (-weight[f], f)):
        i = load.index(min(load))
        out[i].append(f)
        load[i] += weight[f]
    return out


if __name__ == "__main__":
    k, n = int(sys.argv[1]), int(sys.argv[2])
    print(" ".join(shards(n)[k - 1]))
