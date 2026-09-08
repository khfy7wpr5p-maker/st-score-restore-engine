"""Non-production RestorationJobService subclass with the Stage 11 V2a shadow hook.

The normal ``RestorationJobService`` and HTTP server entry point remain unchanged. This
subclass is an explicit validation surface for synthetic/non-held-out shadow observations.
"""
from __future__ import annotations

from .job_service import RestorationJobService
from .stage11_v2a_shadow_handoff import Stage11V2aShadowJobMixin


class Stage11V2aShadowRestorationJobService(
    Stage11V2aShadowJobMixin,
    RestorationJobService,
):
    """Existing non-production job workflow plus an explicit post-primary shadow method."""

    pass


__all__ = ["Stage11V2aShadowRestorationJobService"]
