"""Tests for the intellicenter number platform."""

from unittest.mock import MagicMock

from homeassistant.const import PERCENTAGE

from custom_components.intellicenter.number import PoolNumber, async_setup_entry
from custom_components.intellicenter.pyintellicenter import (
    BODY_ATTR,
    CHEM_TYPE,
    PRIM_ATTR,
    SEC_ATTR,
)


def _add_body(pool_model, objnam, subtype, sname):
    pool_model.addObject(objnam, {"OBJTYP": "BODY", "SUBTYP": subtype, "SNAME": sname})


def _add_intellichlor(pool_model, body_attr, sname="IntelliChlor 1"):
    pool_model.addObject(
        "CHEM01",
        {
            "OBJTYP": CHEM_TYPE,
            "SUBTYP": "ICHLOR",
            "SNAME": sname,
            BODY_ATTR: body_attr,
            PRIM_ATTR: "20",
            SEC_ATTR: "10",
        },
    )


async def _run_setup(hass, mock_config_entry):
    added = []
    async_add_entities = MagicMock(side_effect=lambda entities: added.extend(entities))
    await async_setup_entry(hass, mock_config_entry, async_add_entities)
    return added


async def test_setup_intellichlor_pool_only(hass, mock_config_entry, setup_integration, pool_model):
    _add_body(pool_model, "B1101", "POOL", "Pool")
    _add_intellichlor(pool_model, "B1101")

    added = await _run_setup(hass, mock_config_entry)

    assert len(added) == 1
    entity = added[0]
    assert isinstance(entity, PoolNumber)
    assert entity.name == "IntelliChlor 1 Output % (Pool)"
    assert entity.native_unit_of_measurement == PERCENTAGE
    assert entity._attribute_key == PRIM_ATTR


async def test_setup_intellichlor_pool_and_spa_both_exist(
    hass, mock_config_entry, setup_integration, pool_model
):
    _add_body(pool_model, "B1101", "POOL", "Pool")
    _add_body(pool_model, "B1202", "SPA", "Spa")
    _add_intellichlor(pool_model, "B1101 B1202")

    added = await _run_setup(hass, mock_config_entry)

    assert len(added) == 2
    by_key = {e._attribute_key: e for e in added}
    assert by_key[PRIM_ATTR].name == "IntelliChlor 1 Output % (Pool)"
    assert by_key[SEC_ATTR].name == "IntelliChlor 1 Output % (Spa)"


async def test_setup_intellichlor_spa_body_missing(
    hass, mock_config_entry, setup_integration, pool_model
):
    _add_body(pool_model, "B1101", "POOL", "Pool")
    # B1202 (spa) is referenced but never added to the model
    _add_intellichlor(pool_model, "B1101 B1202")

    added = await _run_setup(hass, mock_config_entry)

    assert len(added) == 1
    assert added[0]._attribute_key == PRIM_ATTR


async def test_setup_no_intellichlor_present(hass, mock_config_entry, setup_integration):
    added = await _run_setup(hass, mock_config_entry)

    assert added == []


def test_pool_number_entity_value_and_set_value(
    mock_config_entry, mock_controller, pool_object_factory
):
    obj = pool_object_factory(
        "CHEM01", CHEM_TYPE, "ICHLOR", SNAME="IntelliChlor 1", PRIM="20"
    )
    entity = PoolNumber(
        mock_config_entry,
        mock_controller,
        obj,
        attribute_key=PRIM_ATTR,
        unit_of_measurement=PERCENTAGE,
    )

    assert entity.native_value == "20"
    assert entity.icon == "mdi:gauge"
    assert entity.native_min_value == 0
    assert entity.native_max_value == 100
    assert entity.native_step == 1

    entity.set_native_value(30.0)

    mock_controller.requestChanges.assert_called_once_with(
        "CHEM01", {PRIM_ATTR: "30"}, waitForResponse=False
    )
