# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Elinsrc

import asyncio
import ipaddress
import re
import time

import aiohttp
import asyncio_dgram

GOLDSRC_APPIDS = [10, 70]

HDR = b"\xff\xff\xff\xff"
INFO = HDR + b"TSource Engine Query\x00"
URL = "https://api.steampowered.com/IGameServersService/GetServerList/v1/"
SAFE_GAMEDIR_RE = re.compile(r"^[a-zA-Z0-9_\-]+$")


def _str(d: bytes, o: int):
    e = d.index(b"\x00", o)
    return d[o:e].decode("utf-8", "replace").strip(), e + 1


class GoldSrcServerQuery:
    def __init__(self, steam_api_key: str, app_ids: list[int] = None, timeout: float = 2.0, concurrency: int = 200):
        self.steam_api_key = steam_api_key
        self.app_ids = app_ids or GOLDSRC_APPIDS
        self.timeout = timeout
        self.concurrency = concurrency

    async def _udp(self, ip, port, data):
        try:
            s = await asyncio_dgram.connect((ip, port))
            try:
                await s.send(data)
                return (await asyncio.wait_for(s.recv(), self.timeout))[0]
            finally:
                s.close()
        except Exception:
            return None

    async def query(self, ip, port):
        t0 = time.perf_counter()
        d = await self._udp(ip, port, INFO)
        if d and len(d) >= 9 and d[:5] == HDR + b"\x41":
            d = await self._udp(ip, port, INFO + d[5:9])
        if not d or d[:4] != HDR or d[4] not in (0x49, 0x6D):
            return None

        try:
            o, rep = 5, None
            if d[4] == 0x49:
                o += 1
                name, o = _str(d, o)
                _, o = _str(d, o)
                gd, o = _str(d, o)
                game, o = _str(d, o)
                o += 2
                players, maxpl, _ = d[o], d[o + 1], d[o + 5]
            else:
                rep, o = _str(d, o)
                name, o = _str(d, o)
                _, o = _str(d, o)
                gd, o = _str(d, o)
                game, o = _str(d, o)
                players, maxpl = d[o], d[o + 1]
                tail = d[o + 2:o + 6]
                if len(tail) < 4 or chr(tail[1]).lower() not in "dlp" or chr(tail[2]).lower() not in "lw":
                    return None
        except (IndexError, ValueError):
            return None

        if game.upper() == "HLTV" or not 0 < maxpl <= 32 or not name:
            return None

        gd = gd.lower()
        if not gd or not SAFE_GAMEDIR_RE.match(gd):
            return None

        orig = None
        if rep and ":" in rep:
            rip, _, rport = rep.rpartition(":")
            try:
                a = ipaddress.ip_address(rip)
                if not (a.is_unspecified or a.is_private) and rip != ip and rport.isdigit():
                    orig = f"{rip}:{rport}"
            except ValueError:
                pass

        return {
            "ip": ip,
            "port": port,
            "gamedir": gd,
            "players": players,
            "orig": orig,
            "rtt": time.perf_counter() - t0,
        }

    async def get_all_server_lists(self) -> dict[str, list[tuple[str, int]]]:
        cands = set()
        async with aiohttp.ClientSession() as session:
            for appid in set(self.app_ids):
                params = {"key": self.steam_api_key, "filter": f"\\appid\\{appid}", "limit": 5000}
                async with session.get(URL, params=params, timeout=aiohttp.ClientTimeout(total=15)) as r:
                    r.raise_for_status()
                    j = await r.json()
                for s in j.get("response", {}).get("servers", []):
                    ip, _, port = s.get("addr", "").rpartition(":")
                    if ip and port.isdigit() and s.get("players", 0) <= 32 and 0 < s.get("max_players", 1) <= 32:
                        cands.add((ip, int(port)))

        sem = asyncio.Semaphore(self.concurrency)

        async def probe(ip, port):
            async with sem:
                return await self.query(ip, port)

        def valid(results):
            return {(r["ip"], r["port"]): r for r in results if r and r.get("gamedir")}

        found = valid(await asyncio.gather(*(probe(*c) for c in cands)))

        extra = set()
        for r in found.values():
            if r["orig"]:
                ip, _, port = r["orig"].rpartition(":")
                if (ip, int(port)) not in cands:
                    extra.add((ip, int(port)))
        found.update(valid(await asyncio.gather(*(probe(*c) for c in extra))))

        groups = {}
        for r in found.values():
            groups.setdefault(r["orig"] or f"{r['ip']}:{r['port']}", []).append(r)

        lists: dict[str, set] = {}
        for key, g in groups.items():
            ip, _, port = key.rpartition(":")
            if len(g) == 1 and g[0]["orig"]:
                ip, port = g[0]["ip"], g[0]["port"]
            gd = g[0]["gamedir"]
            lists.setdefault(gd, set()).add((ip, int(port)))

        return {
            gd: sorted(v, key=lambda a: (ipaddress.ip_address(a[0]), a[1]))
            for gd, v in sorted(lists.items())
        }

    async def get_server_list(self, gamedir: str) -> list[tuple[str, int]]:
        return (await self.get_all_server_lists()).get(gamedir, [])