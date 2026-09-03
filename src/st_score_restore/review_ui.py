"""Dependency-free accessible teacher-review UI asset router for Stage 5."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from .review_ui_css import REVIEW_UI_CSS
from .review_ui_html import REVIEW_UI_HTML
from .review_ui_js import REVIEW_UI_JS

UI_VERSION: Final[str] = "1.0.0"


@dataclass(frozen=True)
class ReviewUiAsset:
    content_type: str
    body: bytes


_ASSETS: Final[dict[str, ReviewUiAsset]] = {
    "/review": ReviewUiAsset("text/html; charset=utf-8", REVIEW_UI_HTML),
    "/review/styles.css": ReviewUiAsset("text/css; charset=utf-8", REVIEW_UI_CSS),
    "/review/app.js": ReviewUiAsset("application/javascript; charset=utf-8", REVIEW_UI_JS),
}


def review_ui_asset(path: str) -> ReviewUiAsset | None:
    """Return an exact same-origin Stage 5 UI asset; unknown paths fail closed."""

    normalized = path.rstrip("/") or "/"
    return _ASSETS.get(normalized)


__all__ = [
    "REVIEW_UI_CSS",
    "REVIEW_UI_HTML",
    "REVIEW_UI_JS",
    "UI_VERSION",
    "ReviewUiAsset",
    "review_ui_asset",
]
