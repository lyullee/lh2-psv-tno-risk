"""Command-line summary for the published research record."""

from __future__ import annotations

import json

from .analysis import load_published_results


def main() -> None:
    print(json.dumps(load_published_results(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
