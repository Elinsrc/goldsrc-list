# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Elinsrc

import asyncio
import os
import sys
from pathlib import Path

from server_query import GoldSrcServerQuery

OUTPUT_DIR = Path(__file__).parent / "docs" / "v1" / "servers"


def write_one(gamedir: str, servers: list) -> str:
    lines = [f"gs {ip}:{port}" for ip, port in servers]

    out_path = OUTPUT_DIR / gamedir
    old = out_path.read_text(encoding="utf-8").splitlines() if out_path.exists() else []

    if not lines:
        raise RuntimeError("no valid servers found, keeping the old list")

    if lines == old:
        return f"{len(lines)} servers (unchanged)"

    tmp = out_path.with_suffix(".tmp")
    tmp.write_text("\n".join(lines) + "\n", encoding="utf-8")
    tmp.replace(out_path)
    return f"{len(lines)} servers (was {len(old)})"


async def main() -> int:
    api_key = os.environ.get("STEAM_API_KEY")
    if not api_key:
        print("STEAM_API_KEY is not set", file=sys.stderr)
        return 1

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    query = GoldSrcServerQuery(steam_api_key=api_key)

    try:
        lists = await query.get_all_server_lists()
    except Exception as e:
        print(f"Steam/query FAILED ({e})", file=sys.stderr)
        return 1

    failed = 0
    for gamedir, servers in lists.items():
        try:
            print(f"{gamedir}: {write_one(gamedir, servers)}")
        except Exception as e:
            failed += 1
            print(f"{gamedir}: FAILED ({e})", file=sys.stderr)

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))