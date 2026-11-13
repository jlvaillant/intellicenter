"""Common test fixtures for intellicenter tests."""

import json
from pathlib import Path
from unittest.mock import MagicMock

from homeassistant.const import CONF_HOST
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.intellicenter.const import DOMAIN
from custom_components.intellicenter.pyintellicenter import (
    ModelController,
    PoolModel,
    PoolObject,
    SystemInfo,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Allow hass to load this custom component in every test."""
    yield


def _make_object(objnam: str, objtype: str, subtype: str = None, **properties) -> PoolObject:
    """Build a real PoolObject the same way the wire protocol would."""
    params = dict(properties)
    params["OBJTYP"] = objtype
    if subtype is not None:
        params["SUBTYP"] = subtype
    return PoolObject(objnam, params)


@pytest.fixture
def pool_object_factory():
    """Return a factory for building PoolObjects from flat kwargs."""
    return _make_object


@pytest.fixture
def pool_model():
    """An empty PoolModel ready to have objects added to it."""
    return PoolModel()


@pytest.fixture
def sample_pool_model():
    """A PoolModel loaded from a scrubbed real-world diagnostics dump."""
    model = PoolModel()
    objects = json.loads((FIXTURES_DIR / "sample_objects.json").read_text())
    model.addObjects(objects)
    return model


@pytest.fixture
def system_info():
    """A SystemInfo built the same way the real controller builds one."""
    return SystemInfo(
        "_5451",
        {
            "PROPNAME": "Test Pool",
            "VER": "1.2.3",
            "MODE": "ENGLISH",
            "SNAME": "Test Pool System",
        },
    )


@pytest.fixture
def mock_controller(pool_model, system_info):
    """A controller double with a real model/systemInfo but no network I/O."""
    controller = MagicMock(spec=ModelController)
    controller.model = pool_model
    controller.systemInfo = system_info
    controller.host = "1.2.3.4"
    return controller


@pytest.fixture
def mock_handler(mock_controller):
    """Stand-in for the Handler object the integration stores in hass.data[DOMAIN]."""
    handler = MagicMock()
    handler.controller = mock_controller
    return handler


@pytest.fixture
def mock_config_entry(hass):
    """A config entry registered with hass."""
    entry = MockConfigEntry(
        domain=DOMAIN, data={CONF_HOST: "1.2.3.4"}, entry_id="test_entry_id"
    )
    entry.add_to_hass(hass)
    return entry


@pytest.fixture
def setup_integration(hass, mock_config_entry, mock_handler):
    """Inject the mocked handler into hass.data, as if async_setup_entry had run."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][mock_config_entry.entry_id] = mock_handler
    return mock_config_entry
