from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.services import sde


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download and extract EVE SDE SQLite dump.")
    parser.add_argument(
        "--target",
        default=os.getenv("SDE_PATH", "/data/sde.db"),
        help="Destination file path for sde.db",
    )
    parser.add_argument(
        "--version-file",
        default=None,
        help="Version metadata file path (default: same directory as target).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    target = Path(args.target)
    version_file = Path(args.version_file) if args.version_file else target.with_name("sde_version.txt")

    downloaded = sde.download_sde(target_path=target, version_path=version_file)
    print(f"Downloaded SDE to: {downloaded}")
    print(f"Version metadata: {version_file}")


if __name__ == "__main__":
    main()
