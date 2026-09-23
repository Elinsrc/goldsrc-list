import aiohttp

GOLDSRC_GAMES = {
    "cstrike": 10,
    "valve": 70,
}


class GoldSrcServerQuery:
    def __init__(self, steam_api_key: str, goldsrc_games: dict = None):
        self.steam_api_key = steam_api_key
        self.goldsrc_games = goldsrc_games or GOLDSRC_GAMES

    async def get_server_list(self, gamedir: str) -> list[tuple[str, str]]:
        appid = self.goldsrc_games.get(gamedir)
        if appid is None:
            return []

        url = "https://api.steampowered.com/IGameServersService/GetServerList/v1/"
        params = {
            "key": self.steam_api_key,
            "filter": f"\\appid\\{appid}",
            "limit": 5000,
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(
                url, params=params, timeout=aiohttp.ClientTimeout(total=10)
            ) as r:
                r.raise_for_status()
                j = await r.json()

        servers = []
        for s in j.get("response", {}).get("servers", []):
            addr = s.get("addr", "")
            if ":" not in addr:
                continue
            if s.get("players", 0) > 32:
                continue

            ip, port = addr.rsplit(":", 1)
            servers.append((ip, port))

        return servers
