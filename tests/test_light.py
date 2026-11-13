"""Tests for the intellicenter light platform."""

from unittest.mock import MagicMock

from custom_components.intellicenter.light import LIGHTS_EFFECTS, PoolLight, async_setup_entry
from custom_components.intellicenter.pyintellicenter import STATUS_ATTR, USE_ATTR


async def _run_setup(hass, mock_config_entry):
    added = []
    async_add_entities = MagicMock(side_effect=lambda entities: added.extend(entities))
    await async_setup_entry(hass, mock_config_entry, async_add_entities)
    return added


async def test_simple_light_without_color_effects(
    hass, mock_config_entry, setup_integration, pool_model
):
    pool_model.addObject(
        "C0010", {"OBJTYP": "CIRCUIT", "SUBTYP": "DIMMER", "SNAME": "Dimmer", "STATUS": "OFF"}
    )

    added = await _run_setup(hass, mock_config_entry)

    assert len(added) == 1
    light = added[0]
    assert isinstance(light, PoolLight)
    assert light.supported_features == 0
    assert light._lightEffects is None
    # guarded against crashing when there are no color effects to report
    assert light.effect_list is None
    assert light.effect is None


async def test_light_with_color_effects(hass, mock_config_entry, setup_integration, pool_model):
    pool_model.addObject(
        "C0005", {"OBJTYP": "CIRCUIT", "SUBTYP": "GLOW", "SNAME": "Pool Light", "STATUS": "OFF", "USE": "WHITER"}
    )

    added = await _run_setup(hass, mock_config_entry)

    assert len(added) == 1
    light = added[0]
    assert light._lightEffects == LIGHTS_EFFECTS
    assert light.effect == "White"
    assert set(light.effect_list) == set(LIGHTS_EFFECTS.values())


async def test_non_light_circuit_is_ignored(hass, mock_config_entry, setup_integration, pool_model):
    pool_model.addObject(
        "C0002", {"OBJTYP": "CIRCUIT", "SUBTYP": "GENERIC", "SNAME": "Pump", "STATUS": "OFF"}
    )

    added = await _run_setup(hass, mock_config_entry)

    assert added == []


async def test_light_show_aggregates_children_color_effect_support(
    hass, mock_config_entry, setup_integration, pool_model
):
    pool_model.addObject(
        "C0005", {"OBJTYP": "CIRCUIT", "SUBTYP": "GLOW", "SNAME": "Pool Light", "STATUS": "OFF"}
    )
    pool_model.addObject("M0001", {"OBJTYP": "CIRCGRP", "PARENT": "LS01", "CIRCUIT": "C0005"})
    pool_model.addObject(
        "LS01", {"OBJTYP": "CIRCUIT", "SUBTYP": "LITSHO", "SNAME": "Light Show", "STATUS": "OFF"}
    )

    added = await _run_setup(hass, mock_config_entry)

    show = next(e for e in added if e._poolObject.objnam == "LS01")
    assert show._lightEffects == LIGHTS_EFFECTS


def test_light_is_on_and_turn_on_off(mock_config_entry, mock_controller, pool_object_factory):
    obj = pool_object_factory("C0005", "CIRCUIT", "GLOW", SNAME="Pool Light", STATUS="OFF")
    entity = PoolLight(mock_config_entry, mock_controller, obj, LIGHTS_EFFECTS)

    assert entity.is_on is False

    entity.turn_on()
    mock_controller.requestChanges.assert_called_with(
        "C0005", {STATUS_ATTR: "ON"}, waitForResponse=False
    )

    entity.turn_off()
    mock_controller.requestChanges.assert_called_with(
        "C0005", {STATUS_ATTR: "OFF"}, waitForResponse=False
    )


def test_light_is_updated_for_status_or_use(mock_config_entry, mock_controller, pool_object_factory):
    obj = pool_object_factory("C0005", "CIRCUIT", "GLOW", SNAME="Pool Light", STATUS="OFF")
    entity = PoolLight(mock_config_entry, mock_controller, obj, LIGHTS_EFFECTS)

    assert entity.isUpdated({"C0005": {STATUS_ATTR: "ON"}})
    assert entity.isUpdated({"C0005": {USE_ATTR: "100"}})
    assert not entity.isUpdated({"C0005": {"SNAME": "x"}})
    assert not entity.isUpdated({"OTHER": {STATUS_ATTR: "ON"}})
