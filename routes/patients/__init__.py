"""Patient routes.

Registration order is load-bearing: fragment and static paths must be registered
before the `/patients/{patient_id}` wildcard, or `/patients/table` is captured as
a patient id.
"""

from __future__ import annotations

from routes.patients._data import register_patient_data_routes
from routes.patients._pages import register_patient_page_routes


def register_patient_routes(rt) -> None:
    register_patient_data_routes(rt)
    register_patient_page_routes(rt)
