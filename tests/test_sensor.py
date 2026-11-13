"""Tests for the intellicenter sensor platform."""

from unittest.mock import MagicMock

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import UnitOfElectricPotential, UnitOfPower, UnitOfTemperature

from custom_components.intellicenter.sensor import PARTS_PER_MILLION, PoolSensor, async_setup_entry
from custom_components.intellicenter.const import CONST_GPM, CONST_RPM


async def _run_setup(hass, mock_config_entry):
    added = []
    async_add_entities = MagicMock(side_effect=lambda entities: added.extend(entities))
    await async_setup_entry(hass, mock_config_entry, async_add_entities)
    return added


async def test_sense_object_creates_temperature_sensor(
    hass, mock_config_entry, setup_integration, pool_model
):
    pool_model.addObject(
        "SSW11", {"OBJTYP": "SENSE", "SUBTYP": "POOL", "SNAME": "Water Sensor", "SOURCE": "88"}
    )

    added = await _run_setup(hass, mock_config_entry)

    assert len(added) == 1
    sensor = added[0]
    assert sensor.name == "Water Sensor"
    assert sensor._attr_device_class == SensorDeviceClass.TEMPERATURE
    assert sensor.native_unit_of_measurement == UnitOfTemperature.FAHRENHEIT
    assert sensor.state == "88"


async def test_pump_creates_sensors_only_for_present_attributes(
    hass, mock_config_entry, setup_integration, pool_model
):
    pool_model.addObject(
        "PMP01", {"OBJTYP": "PUMP", "SUBTYP": "VSF", "SNAME": "VSF", "PWR": "879", "RPM": "2600"}
    )

    added = await _run_setup(hass, mock_config_entry)

    units = {s.native_unit_of_measurement for s in added}
    assert units == {UnitOfPower.WATT, CONST_RPM}
    assert len(added) == 2


async def test_pump_without_tracked_attributes_creates_no_sensors(
    hass, mock_config_entry, setup_integration, pool_model
):
    pool_model.addObject("PMP01", {"OBJTYP": "PUMP", "SUBTYP": "SPEED", "SNAME": "Pump"})

    added = await _run_setup(hass, mock_config_entry)

    assert added == []


async def test_body_creates_last_and_desired_temp_sensors(
    hass, mock_config_entry, setup_integration, pool_model
):
    pool_model.addObject(
        "B1101",
        {"OBJTYP": "BODY", "SUBTYP": "POOL", "SNAME": "Pool", "LSTTMP": "82", "LOTMP": "84"},
    )

    added = await _run_setup(hass, mock_config_entry)

    assert len(added) == 2
    by_name = {s.name: s for s in added}
    assert by_name["Pool last temp"].state == "82"
    assert by_name["Pool desired temp"].state == "84"


async def test_ichem_creates_ph_and_orp_sensors(
    hass, mock_config_entry, setup_integration, pool_model
):
    pool_model.addObject(
        "CHEM01",
        {
            "OBJTYP": "CHEM",
            "SUBTYP": "ICHEM",
            "SNAME": "IntelliChem",
            "PHVAL": "7.4",
            "ORPVAL": "720",
        },
    )

    added = await _run_setup(hass, mock_config_entry)

    assert len(added) == 2
    by_name = {s.name: s for s in added}
    assert set(by_name) == {"IntelliChem (pH)", "IntelliChem (ORP)"}
    assert by_name["IntelliChem (pH)"].native_unit_of_measurement == "pH"
    assert (
        by_name["IntelliChem (ORP)"].native_unit_of_measurement
        == UnitOfElectricPotential.MILLIVOLT
    )


async def test_ichlor_creates_salt_sensor(hass, mock_config_entry, setup_integration, pool_model):
    pool_model.addObject(
        "CHEM01",
        {"OBJTYP": "CHEM", "SUBTYP": "ICHLOR", "SNAME": "IntelliChlor", "SALT": "3200"},
    )

    added = await _run_setup(hass, mock_config_entry)

    assert len(added) == 1
    assert added[0].native_unit_of_measurement == PARTS_PER_MILLION
    assert added[0].state == "3200"


def test_rounding_factor_smooths_value(mock_config_entry, mock_controller, pool_object_factory):
    obj = pool_object_factory("PMP01", "PUMP", "VSF", SNAME="VSF", PWR="891")
    entity = PoolSensor(
        mock_config_entry,
        mock_controller,
        obj,
        device_class=SensorDeviceClass.POWER,
        attribute_key="PWR",
        rounding_factor=25,
    )

    assert entity.state == "900"
