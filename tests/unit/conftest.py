"""Unit-test conftest: disable the live-Firefly session setup.

Unit tests use AsyncMock clients exclusively, so the root conftest's
session-scoped `_setup_test_data` fixture (which creates accounts and
budgets in a live Firefly III test instance) is unnecessary — and fails
when no test instance is reachable. Overriding it here lets the unit
suite run standalone (e.g. locally without tests/.env.test pointing at
a real instance), while integration tests keep the live setup.
"""

import pytest


@pytest.fixture(scope='session', autouse=True)
async def _setup_test_data():
    """No-op override of the root conftest's live data setup."""
    return
