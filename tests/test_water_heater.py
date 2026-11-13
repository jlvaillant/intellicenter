"""Tests for the intellicenter water_heater platform."""

from unittest.mock import MagicMock

from homeassistant.const import ATTR_TEMPERATURE, STATE_IDLE, STATE_OFF, STATE_ON
from homeassistant.const import UnitOfTemperature

from custom_components.intellicenter.pyintellicenter import NULL_OBJNAM
from custom_components.intellicenter.water_heater import PoolWaterHeater, async_setup_entry


async def _run_setup(hass, mock_config_entry):
    added = []
    async_add_entities = MagicMock(side_effect=lambda entities: added.extend(entities))
    await async_setup_entry(hass, mock_config_entry, async_add_entities)
    return added


def _setup_heater_and_bodies(pool_model):
    pool_model.addObject(
        "H0001",
        {"OBJTYP": "HEATER", "SUBTYP": "GENERIC", "SNAME": "Gas Heater", "BODY": "B1101 B1202", "LISTORD": "1"},
    )
    pool_model.addObject(
        "B1101",
        {
            "OBJTYP": "BODY",
            "SUBTYP": "POOL",
            "SNAME": "Pool",
            "STATUS": "ON",
            "HEATER": "H0001",
            "HTMODE": "1",
            "LSTTMP": "82",
            "LOTMP": "84",
        },
    )
    pool_model.addObject(
        "B1202",
        {
            "OBJTYP": "BODY",
            "SUBTYP": "SPA",
            "SNAME": "Spa",
            "STATUS": "OFF",
            "HEATER": NULL_OBJNAM,
            "HTMODE": "0",
            "LSTTMP": "80",
            "LOTMP": "96",
        },
    )


async def test_setup_creates_one_water_heater_per_body_with_a_matching_heater(
    hass, mock_config_entry, setup_integration, pool_model
):
    _setup_heater_and_bodies(pool_model)

    added = await _run_setup(hass, mock_config_entry)

    assert len(added) == 2
    assert {e._poolObject.objnam for e in added} == {"B1101", "B1202"}


async def test_body_without_matching_heater_gets_no_entity(
    hass, mock_config_entry, setup_integration, pool_model
):
    pool_model.addObject(
        "H0001", {"OBJTYP": "HEATER", "SUBTYP": "GENERIC", "SNAME": "Gas Heater", "BODY": "B1101", "LISTORD": "1"}
    )
    pool_model.addObject(
        "B1202",
        {"OBJTYP": "BODY", "SUBTYP": "SPA", "SNAME": "Spa", "STATUS": "OFF", "HEATER": NULL_OBJNAM, "HTMODE": "0"},
    )

    added = await _run_setup(hass, mock_config_entry)

    assert added == []


def _make_water_heater(mock_config_entry, mock_controller, pool_model, pool_object_factory, **body_overrides):
    pool_model.addObject(
        "H0001", {"OBJTYP": "HEATER", "SUBTYP": "GENERIC", "SNAME": "Gas Heater", "BODY": "B1101"}
    )
    defaults = {
        "STATUS": "ON",
        "HEATER": "H0001",
        "HTMODE": "1",
        "LSTTMP": "82",
        "LOTMP": "84",
    }
    defaults.update(body_overrides)
    body = pool_object_factory("B1101", "BODY", "POOL", SNAME="Pool", **defaults)
    return PoolWaterHeater(mock_config_entry, mock_controller, body, ["H0001"])


def test_state_is_on_when_actively_heating(mock_config_entry, mock_controller, pool_model, pool_object_factory):
    heater = _make_water_heater(mock_config_entry, mock_controller, pool_model, pool_object_factory)

    assert heater.state == STATE_ON


def test_state_is_idle_when_heater_assigned_but_not_actively_heating(
    mock_config_entry, mock_controller, pool_model, pool_object_factory
):
    heater = _make_water_heater(mock_config_entry, mock_controller, pool_model, pool_object_factory, HTMODE="0")

    assert heater.state == STATE_IDLE


def test_state_is_off_when_no_heater_assigned(mock_config_entry, mock_controller, pool_model, pool_object_factory):
    heater = _make_water_heater(mock_config_entry, mock_controller, pool_model, pool_object_factory, HEATER=NULL_OBJNAM)

    assert heater.state == STATE_OFF


def test_temperature_properties(mock_config_entry, mock_controller, pool_model, pool_object_factory):
    heater = _make_water_heater(mock_config_entry, mock_controller, pool_model, pool_object_factory)

    assert heater.temperature_unit == UnitOfTemperature.FAHRENHEIT
    assert heater.min_temp == 40.0
    assert heater.max_temp == 104.0
    assert heater.current_temperature == 82.0
    assert heater.target_temperature == 84.0


def test_set_temperature_requests_change(mock_config_entry, mock_controller, pool_model, pool_object_factory):
    heater = _make_water_heater(mock_config_entry, mock_controller, pool_model, pool_object_factory)

    heater.set_temperature(**{ATTR_TEMPERATURE: 86.0})

    mock_controller.requestChanges.assert_called_once_with(
        "B1101", {"LOTMP": "86"}, waitForResponse=False
    )


def test_current_operation_and_operation_list(mock_config_entry, mock_controller, pool_model, pool_object_factory):
    heater = _make_water_heater(mock_config_entry, mock_controller, pool_model, pool_object_factory)

    assert heater.current_operation == "Gas Heater"
    assert heater.operation_list == [STATE_OFF, "Gas Heater"]


def test_set_operation_mode_to_heater_and_off(mock_config_entry, mock_controller, pool_model, pool_object_factory):
    heater = _make_water_heater(mock_config_entry, mock_controller, pool_model, pool_object_factory)

    heater.set_operation_mode(STATE_OFF)
    mock_controller.requestChanges.assert_called_with(
        "B1101", {"HEATER": NULL_OBJNAM}, waitForResponse=False
    )

    heater.set_operation_mode("Gas Heater")
    mock_controller.requestChanges.assert_called_with(
        "B1101", {"HEATER": "H0001"}, waitForResponse=False
    )


async def test_turn_on_restores_last_heater(mock_config_entry, mock_controller, pool_model, pool_object_factory):
    heater = _make_water_heater(mock_config_entry, mock_controller, pool_model, pool_object_factory, HEATER=NULL_OBJNAM)
    heater._lastHeater = "H0001"

    await heater.async_turn_on()

    mock_controller.requestChanges.assert_called_once_with(
        "B1101", {"HEATER": "H0001"}, waitForResponse=False
    )


def test_is_updated_tracks_last_heater(mock_config_entry, mock_controller, pool_model, pool_object_factory):
    heater = _make_water_heater(mock_config_entry, mock_controller, pool_model, pool_object_factory)

    assert heater.isUpdated({"B1101": {"HTMODE": "0"}})
    assert heater._lastHeater == "H0001"
    assert not heater.isUpdated({"B1101": {"SNAME": "x"}})
    assert not heater.isUpdated({"OTHER": {"STATUS": "ON"}})
