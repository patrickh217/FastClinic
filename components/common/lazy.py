"""Deferred content loading.

Load-bearing here, not an optimisation. Every FastClinic data view now blocks on a
network round-trip to backbone instead of a local SQL query, so a page route must
return its shell immediately and let the content arrive separately. Without this,
first paint waits on the slowest upstream call on the page.
"""

from __future__ import annotations

from fasthtml.common import Div

from components.common.states import skeleton


def lazy_content(url: str, section_id: str = "lazy-content", rows: int = 5):
    """A skeleton that replaces itself with `url` once the page has loaded."""
    return Div(
        skeleton(rows),
        id=section_id,
        hx_get=url,
        hx_trigger="load",
        hx_swap="outerHTML",
    )
