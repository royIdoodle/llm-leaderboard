from __future__ import annotations
from typing import Optional
import os
import yaml

_DEFAULT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/org_countries.yaml"))


class OrgCountryResolver:
    def __init__(self, mapping_path: str | None = None) -> None:
        self.mapping_path = mapping_path or _DEFAULT_PATH
        self._map = self._load_map()

    def _load_map(self) -> dict[str, str]:
        try:
            if not os.path.exists(self.mapping_path):
                return {}
            with open(self.mapping_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            # normalize keys to lower case
            return {str(k).strip().lower(): str(v).strip() for k, v in data.items() if k is not None and v is not None}
        except Exception:
            return {}

    def refresh(self) -> None:
        self._map = self._load_map()

    def get_country(self, org_name: Optional[str]) -> Optional[str]:
        if not org_name:
            return None
        key = org_name.strip().lower()
        return self._map.get(key)
