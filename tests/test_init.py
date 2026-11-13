"""Tests for intellicenter's __init__.py: setup/unload flow and PoolEntity base class."""

from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_HOST
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.intellicenter import PoolEntity
from custom_components.intellicenter.const import DOMAIN
from custom_components.intellicenter.pyintellicenter import SystemInfo

MODEL_CONTROLLER = "custom_components.intellicenter.ModelController"


def _system_info() -> SystemInfo:
    return SystemInfo(
        "_5451",
        {"PROPNAME": "Test Pool", "VER": "1.2.3", "MODE": "ENGLISH", "SNAME": "x"},
    )


def _controller_factory(start_exc: Exception = None):
    """Return (patch side_effect, list of created instances) for ModelController."""
    created = []

    def factory(host, model, port=6681, loop=None):
        instance = MagicMock()
        instance.host = host
        instance.model = model
        instance.systemInfo = None
        instance._updatedCallback = None
        instance._diconnectedCallback = None

        async def _start():
            if start_exc:
                raise start_exc
            instance.systemInfo = _system_info()

        instance.start = AsyncMock(side_effect=_start)
        instance.stop = MagicMock()
        created.append(instance)
        return instance

    return factory, created


async def test_async_setup_entry_success(hass):
    entry = MockConfigEntry(domain=DOMAIN, data={CONF_HOST: "1.2.3.4"})
    entry.add_to_hass(hass)

    factory, created = _controller_factory()
    with patch(MODEL_CONTROLLER, side_effect=factory):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.LOADED
    assert DOMAIN in hass.data
    handler = hass.data[DOMAIN][entry.entry_id]
    assert handler.controller is created[0]


async def test_async_setup_entry_succeeds_even_if_initial_connection_fails(hass):
    """Setup is optimistic.

    ConnectionHandler.start() only *schedules* the connect loop (asyncio.create_task)
    without awaiting it, and any connection failure is caught and retried inside that
    background loop rather than propagating out. So a failed first connection attempt
    doesn't prevent the config entry from loading; it just means the integration's
    platforms won't be forwarded until a later retry actually connects.
    """
    entry = MockConfigEntry(domain=DOMAIN, data={CONF_HOST: "1.2.3.4"})
    entry.add_to_hass(hass)

    factory, created = _controller_factory(start_exc=ConnectionRefusedError())
    with patch(MODEL_CONTROLLER, side_effect=factory):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.LOADED
    assert hass.data[DOMAIN][entry.entry_id].controller is created[0]
    created[0].start.assert_called_once()


async def test_async_unload_entry_cleans_up(hass):
    entry = MockConfigEntry(domain=DOMAIN, data={CONF_HOST: "1.2.3.4"})
    entry.add_to_hass(hass)

    factory, created = _controller_factory()
    with patch(MODEL_CONTROLLER, side_effect=factory):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        assert await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_block_till_done()

    created[0].stop.assert_called_once()
    assert DOMAIN not in hass.data


class TestPoolEntity:
    """Direct unit tests for the PoolEntity base class."""

    def _entity(self, mock_config_entry, mock_controller, pool_object_factory, **kwargs):
        obj = pool_object_factory(
            "C0006", "CIRCUIT", "POOL", SNAME="Pool", STATUS="OFF"
        )
        return PoolEntity(mock_config_entry, mock_controller, obj, **kwargs)

    def test_name_defaults_to_poolobject_sname(
        self, mock_config_entry, mock_controller, pool_object_factory
    ):
        entity = self._entity(mock_config_entry, mock_controller, pool_object_factory)

        assert entity.name == "Pool"

    def test_name_suffix_convention(
        self, mock_config_entry, mock_controller, pool_object_factory
    ):
        entity = self._entity(
            mock_config_entry, mock_controller, pool_object_factory, name="+ power"
        )

        assert entity.name == "Pool power"

    def test_name_explicit_overrides_poolobject_sname(
        self, mock_config_entry, mock_controller, pool_object_factory
    ):
        entity = self._entity(
            mock_config_entry, mock_controller, pool_object_factory, name="Custom Name"
        )

        assert entity.name == "Custom Name"

    def test_unique_id_includes_entry_and_objnam(
        self, mock_config_entry, mock_controller, pool_object_factory
    ):
        entity = self._entity(mock_config_entry, mock_controller, pool_object_factory)

        assert entity.unique_id == mock_config_entry.entry_id + "C0006"

    def test_unique_id_includes_attribute_key_when_not_status(
        self, mock_config_entry, mock_controller, pool_object_factory
    ):
        from custom_components.intellicenter.pyintellicenter import PWR_ATTR

        entity = self._entity(
            mock_config_entry,
            mock_controller,
            pool_object_factory,
            attribute_key=PWR_ATTR,
        )

        assert entity.unique_id == mock_config_entry.entry_id + "C0006" + PWR_ATTR

    def test_device_info_uses_controller_system_info(
        self, mock_config_entry, mock_controller, pool_object_factory
    ):
        entity = self._entity(mock_config_entry, mock_controller, pool_object_factory)

        info = entity.device_info

        assert info["name"] == "Test Pool"
        assert info["manufacturer"] == "Pentair"
        assert info["identifiers"] == {(DOMAIN, mock_config_entry.entry_id)}

    def test_extra_state_attributes_includes_objtype_and_status(
        self, mock_config_entry, mock_controller, pool_object_factory
    ):
        entity = self._entity(mock_config_entry, mock_controller, pool_object_factory)

        attrs = entity.extra_state_attributes

        assert attrs["OBJNAM"] == "C0006"
        assert attrs["OBJTYPE"] == "CIRCUIT/POOL"
        # STATUS is "OFF" which is falsy-looking but a non-empty string, so it's included
        assert attrs["Status"] == "OFF"

    def test_request_changes_delegates_to_controller(
        self, mock_config_entry, mock_controller, pool_object_factory
    ):
        entity = self._entity(mock_config_entry, mock_controller, pool_object_factory)

        entity.requestChanges({"STATUS": "ON"})

        mock_controller.requestChanges.assert_called_once_with(
            "C0006", {"STATUS": "ON"}, waitForResponse=False
        )

    def test_default_is_updated_checks_attribute_key(
        self, mock_config_entry, mock_controller, pool_object_factory
    ):
        entity = self._entity(mock_config_entry, mock_controller, pool_object_factory)

        assert entity.isUpdated({"C0006": {"STATUS": "ON"}}) is True
        assert entity.isUpdated({"C0006": {"SNAME": "Pool"}}) is False
        assert entity.isUpdated({"OTHER": {"STATUS": "ON"}}) is False

    def test_update_callback_writes_state_when_updated(
        self, mock_config_entry, mock_controller, pool_object_factory
    ):
        entity = self._entity(mock_config_entry, mock_controller, pool_object_factory)
        entity.async_write_ha_state = MagicMock()
        entity._attr_available = False

        entity._update_callback({"C0006": {"STATUS": "ON"}})

        assert entity._attr_available is True
        entity.async_write_ha_state.assert_called_once()

    def test_update_callback_ignores_unrelated_updates(
        self, mock_config_entry, mock_controller, pool_object_factory
    ):
        entity = self._entity(mock_config_entry, mock_controller, pool_object_factory)
        entity.async_write_ha_state = MagicMock()

        entity._update_callback({"OTHER": {"STATUS": "ON"}})

        entity.async_write_ha_state.assert_not_called()

    def test_connection_callback_disconnected_marks_unavailable(
        self, mock_config_entry, mock_controller, pool_object_factory
    ):
        entity = self._entity(mock_config_entry, mock_controller, pool_object_factory)
        entity.async_write_ha_state = MagicMock()

        entity._connection_callback(False)

        assert entity._attr_available is False
        entity.async_write_ha_state.assert_called_once()

    def test_connection_callback_reconnected_refreshes_poolobject(
        self, mock_config_entry, mock_controller, pool_object_factory, pool_model
    ):
        entity = self._entity(mock_config_entry, mock_controller, pool_object_factory)
        pool_model.addObject(
            "C0006",
            {"OBJTYP": "CIRCUIT", "SUBTYP": "POOL", "SNAME": "Pool", "STATUS": "ON"},
        )
        entity.async_write_ha_state = MagicMock()

        entity._connection_callback(True)

        assert entity._attr_available is True
        assert entity._poolObject is pool_model["C0006"]
        entity.async_write_ha_state.assert_called_once()

    def test_connection_callback_reconnected_object_missing(
        self, mock_config_entry, mock_controller, pool_object_factory
    ):
        # pool_model (via mock_controller) is empty, so the object can't be found
        entity = self._entity(mock_config_entry, mock_controller, pool_object_factory)
        entity.async_write_ha_state = MagicMock()

        entity._connection_callback(True)

        # bails out before touching availability/state when the object disappeared
        assert entity._poolObject is None
        entity.async_write_ha_state.assert_not_called()
