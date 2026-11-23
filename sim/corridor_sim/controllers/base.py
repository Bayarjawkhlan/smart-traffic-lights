from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar

from ..model import Site
from ..sensing import SiteView


class Controller(ABC):
    name: ClassVar[str]
    label: ClassVar[str]

    @abstractmethod
    def propose(self, site: Site, view: SiteView) -> int: ...

    def attach(self, views: dict[str, SiteView]) -> None:
        pass

    def explain(self, site: Site, view: SiteView) -> dict[str, float]:
        return {}
