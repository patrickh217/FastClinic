"""Runs each module's built-in self-check under pytest.

The assertions live next to the code they protect, so this file only wires them
into the suite rather than restating them.
"""

from __future__ import annotations

import importlib

import pytest

MODULES = [
    "config.config",
    "services.medbackend.fhir_client",
    "services.patients_service",
    "services.clinical_service",
    "auth.oauth_config",
    "auth.oauth_service",
    "auth.auth_utils",
    "middleware.auth_gate",
    "components.sidebar",
    "components.common.states",
    "tools.seed_demo_data",
]


@pytest.mark.unit
@pytest.mark.parametrize("name", MODULES)
def test_module_self_check(name):
    """GIVEN a shipped module WHEN its demo() runs THEN every invariant holds."""
    module = importlib.import_module(name)
    assert hasattr(module, "demo"), f"{name} has no self-check"
    module.demo()
