import asyncio
import os
import sys
from pathlib import Path

from server_query import GoldSrcServerQuery, GOLDSRC_GAMES

OUTPUT_DIR = Path(__file__).parent / "docs" / "v1" / "servers"


async def generate_one(query: GoldSrcServerQuery, gamedir: str) -> int:
    servers = await query.get_server_list(gamedir)
    lines = [f"gs {ip}:{port}" for ip, port in servers]

    out_path = OUTPUT_DIR / gamedir
    out_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")

    return len(servers)


async def main() -> None:
    api_key = os.environ.get("STEAM_API_KEY")
    if not api_key:
        print("STEAM_API_KEY is not set", file=sys.stderr)
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    query = GoldSrcServerQuery(steam_api_key=api_key)

    for gamedir in GOLDSRC_GAMES:
        try:
            count = await generate_one(query, gamedir)
            print(f"{gamedir}: {count}")
        except Exception as e:
            print(f"{gamedir}: FAILED ({e})", file=sys.stderr)


if __name__ == "__main__":
    asyncio.run(main())
