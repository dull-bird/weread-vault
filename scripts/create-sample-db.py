#!/usr/bin/env python3
"""Create a deterministic fake WeRead Vault SQLite database.

Examples:
  python3 scripts/create-sample-db.py --db /tmp/weread-vault-sample.db
  python3 scripts/create-sample-db.py --sql docs/sample-data/weread-vault-sample.sql
"""

from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

from sample_data import ROOT, create_sample_db, dump_sql


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a privacy-safe sample WeRead Vault database.")
    parser.add_argument("--db", type=Path, help="Output SQLite database path.")
    parser.add_argument("--sql", type=Path, help="Output SQL dump path.")
    args = parser.parse_args()

    if not args.db and not args.sql:
        args.db = ROOT / "docs" / "sample-data" / "weread-vault-sample.db"

    if args.db:
        create_sample_db(args.db)
        print(f"wrote {args.db}")

    if args.sql:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "weread-vault-sample.db"
            create_sample_db(db_path)
            dump_sql(db_path, args.sql)
        print(f"wrote {args.sql}")


if __name__ == "__main__":
    main()
