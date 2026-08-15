"""The four states every data view must render.

Loading, populated, empty, and *indeterminate*. The last one exists because
backbone's search swallows every exception and returns an empty list, so an empty
result genuinely might be a failure. A clinical view that renders "no allergies"
for a query that actually failed is the dangerous version of that bug — so an
uncertain result never renders as a confident absence.
"""

from __future__ import annotations

from fasthtml.common import Div, P, Span


def skeleton(rows: int = 5):
    return Div(
        *[Div(cls="skeleton-row") for _ in range(rows)],
        cls="skeleton",
        aria_busy="true",
        aria_label="Loading",
    )


def empty_state(message: str, hint: str | None = None):
    """Use ONLY when the query is known to have succeeded."""
    return Div(
        P(message, cls="empty-title"),
        P(hint, cls="empty-hint") if hint else None,
        cls="state-empty",
        role="status",
    )


def indeterminate_state(what: str):
    """An empty result we cannot vouch for."""
    return Div(
        P(f"Could not confirm {what}.", cls="empty-title"),
        P(
            "The record service returned nothing, which may mean there is no data "
            "or may mean the request failed. Reload before drawing any conclusion.",
            cls="empty-hint",
        ),
        cls="state-indeterminate",
        role="alert",
    )


def error_state(message: str, denied: bool = False):
    return Div(
        P("You do not have access to this." if denied else "Something went wrong.",
          cls="empty-title"),
        P(message, cls="empty-hint"),
        cls="state-error",
        role="alert",
    )


def capped_notice(shown: int):
    """Counts are never totals — say so wherever one is displayed."""
    return Span(
        f"Showing the first {shown}. The record service does not report a total, "
        "so this is not a count of everything.",
        cls="capped-notice",
    )


def render_list(result, render, *, noun: str, empty_message: str, empty_hint: str | None = None):
    """Single funnel for list rendering, so the certain/empty distinction is never
    re-implemented — or forgotten — per feature."""
    if not result.certain and not len(result):
        return indeterminate_state(noun)
    if not len(result):
        return empty_state(empty_message, empty_hint)
    body = render(result.items)
    return Div(body, capped_notice(len(result))) if result.capped else body


def demo() -> None:
    from services.medbackend.fhir_client import SearchResult

    rendered = str(render_list(SearchResult([], certain=False), lambda i: Div("x"),
                               noun="patients", empty_message="No patients"))
    assert "Could not confirm patients" in rendered
    assert "No patients" not in rendered, "an uncertain result must not claim emptiness"

    rendered = str(render_list(SearchResult([], certain=True), lambda i: Div("x"),
                               noun="patients", empty_message="No patients"))
    assert "No patients" in rendered and "Could not confirm" not in rendered

    rendered = str(render_list(SearchResult([{"id": "1"}], certain=True, capped=True),
                               lambda i: Div("row"), noun="patients",
                               empty_message="No patients"))
    assert "row" in rendered and "not a count of everything" in rendered

    rendered = str(render_list(SearchResult([{"id": "1"}], certain=True, capped=False),
                               lambda i: Div("row"), noun="patients",
                               empty_message="No patients"))
    assert "row" in rendered and "not a count of everything" not in rendered
    print("states self-check ok")


if __name__ == "__main__":
    demo()
