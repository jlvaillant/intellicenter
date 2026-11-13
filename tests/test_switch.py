"""Tests for the intellicenter switch platform."""

from unittest.mock import MagicMock

from custom_components.intellicenter.switch import (
    PoolBody,
    PoolCircuit,
    async_setup_entry,
)
from custom_components.intellicenter.pyintellicenter import SUPER_ATTR, VACFLO_ATTR


async def _run_setup(hass, mock_config_entry):
    added = []
    async_add_entities = MagicMock(side_effect=lambda entities: added.extend(entities))
    await async_setup_entry(hass, mock_config_entry, async_add_entities)
    return added


async def test_body_creates_pool_body_switch(hass, mock_config_entry, setup_integration, pool_model):
    pool_model.addObject("B1101", {"OBJTYP": "BODY", "SUBTYP": "POOL", "SNAME": "Pool", "STATUS": "ON"})

    added = await _run_setup(hass, mock_config_entry)

    assert len(added) == 1
    assert isinstance(added[0], PoolBody)
    assert added[0].icon == "mdi:pool"
    assert added[0].is_on is True


async def test_intellichlor_superchlorinate_switch(
    hass, mock_config_entry, setup_integration, pool_model
):
    pool_model.addObject(
        "CHEM01",
        {"OBJTYP": "CHEM", "SUBTYP": "ICHLOR", "SNAME": "IntelliChlor 1", SUPER_ATTR: "OFF"},
    )

    added = await _run_setup(hass, mock_config_entry)

    assert len(added) == 1
    assert added[0]._attribute_key == SUPER_ATTR
    assert added[0].name == "IntelliChlor 1 Superchlorinate"


async def test_featured_non_light_circuit_creates_switch(
    hass, mock_config_entry, setup_integration, pool_model
):
    pool_model.addObject(
        "C0002",
        {"OBJTYP": "CIRCUIT", "SUBTYP": "GENERIC", "SNAME": "Air Blower", "FEATR": "ON", "STATUS": "OFF"},
    )

    added = await _run_setup(hass, mock_config_entry)

    assert len(added) == 1
    assert isinstance(added[0], PoolCircuit)
    assert added[0].icon == "mdi:alpha-f-box-outline"


async def test_featured_light_circuit_is_excluded(
    hass, mock_config_entry, setup_integration, pool_model
):
    # GLOWT is a light subtype, so even though it's featured it should NOT get a switch
    pool_model.addObject(
        "C0005",
        {"OBJTYP": "CIRCUIT", "SUBTYP": "GLOWT", "SNAME": "Pool Lights", "FEATR": "ON", "STATUS": "OFF"},
    )

    added = await _run_setup(hass, mock_config_entry)

    assert added == []


async def test_circgrp_circuit_creates_switch(
    hass, mock_config_entry, setup_integration, pool_model
):
    pool_model.addObject(
        "G0001",
        {"OBJTYP": "CIRCUIT", "SUBTYP": "CIRCGRP", "SNAME": "Group", "FEATR": "OFF", "STATUS": "OFF"},
    )

    added = await _run_setup(hass, mock_config_entry)

    assert len(added) == 1
    assert added[0].icon == "mdi:alpha-g-box-outline"


async def test_system_creates_vacation_mode_switch(
    hass, mock_config_entry, setup_integration, pool_model
):
    pool_model.addObject("_5451", {"OBJTYP": "SYSTEM", "SNAME": "x", VACFLO_ATTR: "OFF"})

    added = await _run_setup(hass, mock_config_entry)

    assert len(added) == 1
    assert added[0].name == "Vacation mode"
    assert added[0].entity_registry_enabled_default is False


def test_pool_circuit_turn_on_off(mock_config_entry, mock_controller, pool_object_factory):
    obj = pool_object_factory("C0002", "CIRCUIT", "GENERIC", SNAME="Air Blower", STATUS="OFF")
    entity = PoolCircuit(mock_config_entry, mock_controller, obj)

    entity.turn_on()
    mock_controller.requestChanges.assert_called_with("C0002", {"STATUS": "ON"}, waitForResponse=False)

    entity.turn_off()
    mock_controller.requestChanges.assert_called_with("C0002", {"STATUS": "OFF"}, waitForResponse=False)
