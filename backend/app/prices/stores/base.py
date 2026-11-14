from app.core.http import HttpClient
from app.prices.models import Offer


class StoreError(Exception):
    """The store responded but we could not get results."""


class StoreBlocked(StoreError):
    """The store served a captcha / bot wall instead of results."""


class Store:
    id: str = ""
    name: str = ""
    home: str = ""
    kind: str = "PC Specialist"  # Marketplace | Electronics | PC Specialist
    color: str = "#64748b"

    async def search(self, http: HttpClient, query: str, limit: int = 24) -> list[Offer]:
        raise NotImplementedError

    def info(self) -> dict:
        return {"id": self.id, "name": self.name, "home": self.home, "kind": self.kind, "color": self.color}

    @staticmethod
    def check(resp, *, blocked_markers: tuple[str, ...] = ()) -> str:
        if resp.status_code == 403 or resp.status_code == 429:
            raise StoreBlocked(f"HTTP {resp.status_code}")
        if resp.status_code >= 400:
            raise StoreError(f"HTTP {resp.status_code}")
        text = resp.text
        head = text[:20000].lower()
        for marker in blocked_markers:
            if marker.lower() in head:
                raise StoreBlocked("bot check page")
        return text
