"""Tests for the intellicenter binary_sensor platform."""

from unittest.mock import MagicMock

from custom_components.intellicenter.binary_sensor import (
    HeaterBinarySensor,
    PoolBinarySensor,
    async_setup_entry,
)


async def _run_setup(hass, mock_config_entry):
    added = []
    async_add_entities = MagicMock(side_effect=lambda entities: added.extend(entities))
    await async_setup_entry(hass, mock_config_entry, async_add_entities)
    return added


async def test_freeze_circuit_creates_binary_sensor(
    hass, mock_config_entry, setup_integration, pool_model
):
    pool_model.addObject(
        "_FEA2", {"OBJTYP": "CIRCUIT", "SUBTYP": "FRZ", "SNAME": "Freeze", "STATUS": "OFF"}
    )

    added = await _run_setup(hass, mock_config_entry)

    assert len(added) == 1
    assert isinstance(added[0], PoolBinarySensor)
    assert added[0].icon == "mdi:snowflake"
    assert added[0].is_on is False


async def test_sched_creates_binary_sensor_disabled_by_default(
    hass, mock_config_entry, setup_integration, pool_model
):
    pool_model.addObject(
        "SCH00", {"OBJTYP": "SCHED", "SNAME": "Pool", "ACT": "ON", "VACFLO": "OFF"}
    )

    added = await _run_setup(hass, mock_config_entry)

    assert len(added) == 1
    sensor = added[0]
    assert sensor.entity_registry_enabled_default is False
    assert sensor.name == "Pool (schedule)"
    assert sensor.is_on is True


async def test_pump_binary_sensor_on_value_is_10(
    hass, mock_config_entry, setup_integration, pool_model
):
    pool_model.addObject("PMP01", {"OBJTYP": "PUMP", "SUBTYP": "VSF", "SNAME": "VSF", "STATUS": "10"})

    added = await _run_setup(hass, mock_config_entry)

    assert len(added) == 1
    assert added[0].is_on is True


async def test_heater_binary_sensor_on_when_body_actively_heating(
    hass, mock_config_entry, setup_integration, pool_model
):
    pool_model.addObject(
        "H0001", {"OBJTYP": "HEATER", "SUBTYP": "GENERIC", "SNAME": "Gas Heater", "BODY": "B1101"}
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
        },
    )

    added = await _run_setup(hass, mock_config_entry)

    assert len(added) == 1
    heater_sensor = added[0]
    assert isinstance(heater_sensor, HeaterBinarySensor)
    assert heater_sensor.is_on is True


async def test_heater_binary_sensor_off_when_body_not_using_this_heater(
    hass, mock_config_entry, setup_integration, pool_model
):
    pool_model.addObject(
        "H0001", {"OBJTYP": "HEATER", "SUBTYP": "GENERIC", "SNAME": "Gas Heater", "BODY": "B1101"}
    )
    pool_model.addObject(
        "B1101",
        {
            "OBJTYP": "BODY",
            "SUBTYP": "POOL",
            "SNAME": "Pool",
            "STATUS": "ON",
            "HEATER": "00000",
            "HTMODE": "0",
        },
    )

    added = await _run_setup(hass, mock_config_entry)

    assert added[0].is_on is False


def test_heater_binary_sensor_is_updated_checks_tracked_bodies(
    mock_config_entry, mock_controller, pool_object_factory
):
    heater_obj = pool_object_factory(
        "H0001", "HEATER", "GENERIC", SNAME="Gas Heater", BODY="B1101 B1202"
    )
    sensor = HeaterBinarySensor(mock_config_entry, mock_controller, heater_obj)

    assert sensor.isUpdated({"B1101": {"STATUS": "ON"}})
    assert sensor.isUpdated({"B1202": {"HTMODE": "1"}})
    assert not sensor.isUpdated({"B1101": {"SNAME": "x"}})
    assert not sensor.isUpdated({"OTHER": {"STATUS": "ON"}})
