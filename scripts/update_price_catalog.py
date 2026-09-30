from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.pricing import PriceCatalogError, catalog_from_configurator


def main() -> None:
    parser = argparse.ArgumentParser(description="Import a validated EPSS price configurator.")
    parser.add_argument("configurator", type=Path)
    parser.add_argument("--output", type=Path, default=ROOT / "data" / "epss_price_catalog.json")
    args = parser.parse_args()
    try:
        catalog = catalog_from_configurator(args.configurator.read_bytes(), args.configurator.name)
    except (OSError, PriceCatalogError) as error:
        parser.exit(1, f"{error}\n")
    content = catalog.to_bytes()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(".tmp")
    temporary.write_bytes(content)
    temporary.replace(args.output)
    print(f"Imported {len(catalog.records)} configurations; date: {catalog.source_date}; bytes: {len(content)}")


if __name__ == "__main__":
    main()
