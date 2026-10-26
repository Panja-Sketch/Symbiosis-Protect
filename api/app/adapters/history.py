from app.models import Location


class DerivedHistoryProvider:
    """Reads data/derived/history_*.json (via the seed loader) — BigQuery later."""

    def __init__(self, derived: dict[str, dict]):
        self._d = derived

    def stats(self, loc: Location) -> dict:
        return self._d[f"history_{loc.id}"]

    def storms(self, loc: Location) -> dict:
        return self._d["storm_events_az"]["locations"][loc.id]

    def nri(self, loc: Location) -> dict:
        return self._d["nri_az"]["locations"][loc.id]
