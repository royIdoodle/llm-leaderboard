from __future__ import annotations
import sys
from .services.ingest import ingest

USAGE = "Usage: python -m app.cli [terminal-bench|osworld|all]"


def main() -> int:
    if len(sys.argv) < 2:
        print(USAGE)
        return 1
    bench = sys.argv[1]
    try:
        inserted, updated, total = ingest(bench)
        print(f"bench={bench} inserted={inserted} updated={updated} total={total}")
        return 0
    except Exception as e:
        print(f"error: {e}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
