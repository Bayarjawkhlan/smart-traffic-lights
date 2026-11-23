from __future__ import annotations

from ..model import Site
from ..sensing import SiteView
from .base import Controller

MIN_PEDESTRIAN_PHASE = 15.0


class FixedTimeController(Controller):
    name = "fixed-time"
    label = "Fixed-time (today's baseline)"

    def propose(self, site: Site, view: SiteView) -> int:
        phase = site.phases[view.phase]
        duration = phase.default_duration
        if all(site.links[i].pedestrian for i in phase.green):
            duration = max(duration, MIN_PEDESTRIAN_PHASE)
        if view.green_elapsed < duration:
            return view.phase
        return (view.phase + 1) % len(site.phases)
