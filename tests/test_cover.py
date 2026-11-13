"""Tests for the intellicenter cover platform."""

from unittest.mock import MagicMock

import pytest

from custom_components.intellicenter.cover import PoolCover, async_setup_entry


async def _run_setup(hass, mock_config_entry):
    added = []
    async_add_entities = MagicMock(side_effect=lambda entities: added.extend(entities))
    await async_setup_entry(hass, mock_config_entry, async_add_entities)
    return added


async def test_extinstr_cover_creates_entity(hass, mock_config_entry, setup_integration, pool_model):
    pool_model.addObject(
        "EI01", {"OBJTYP": "EXTINSTR", "SUBTYP": "COVER", "SNAME": "Pool Cover", "STATUS": "OFF", "NORMAL": "OFF"}
    )

    added = await _run_setup(hass, mock_config_entry)

    assert len(added) == 1
    assert isinstance(added[0], PoolCover)
    assert added[0].icon == "mdi:arrow-expand-horizontal"


async def test_non_cover_extinstr_subtype_is_ignored(
    hass, mock_config_entry, setup_integration, pool_model
):
    pool_model.addObject(
        "EI01", {"OBJTYP": "EXTINSTR", "SUBTYP": "OTHER", "SNAME": "Something Else"}
    )

    added = await _run_setup(hass, mock_config_entry)

    assert added == []


@pytest.mark.parametrize(
    ("status", "normal", "expected_closed"),
    [
        ("ON", "ON", True),   # normally closed, currently in that state
        ("OFF", "OFF", True),  # normally open, but currently closed
        ("OFF", "ON", False),  # normally closed, currently open
        ("ON", "OFF", False),  # normally open, currently open
    ],
)
def test_is_closed_depends_on_status_and_normal(
    mock_config_entry, mock_controller, pool_object_factory, status, normal, expected_closed
):
    obj = pool_object_factory(
        "EI01", "EXTINSTR", "COVER", SNAME="Pool Cover", STATUS=status, NORMAL=normal
    )
    cover = PoolCover(mock_config_entry, mock_controller, obj)

    assert cover.is_closed is expected_closed


async def test_open_and_close_cover(mock_config_entry, mock_controller, pool_object_factory):
    obj = pool_object_factory(
        "EI01", "EXTINSTR", "COVER", SNAME="Pool Cover", STATUS="OFF", NORMAL="ON"
    )
    cover = PoolCover(mock_config_entry, mock_controller, obj)

    await cover.async_open_cover()
    mock_controller.requestChanges.assert_called_with(
        "EI01", {"STATUS": "OFF"}, waitForResponse=False
    )

    await cover.async_close_cover()
    mock_controller.requestChanges.assert_called_with(
        "EI01", {"STATUS": "ON"}, waitForResponse=False
    )


def test_is_updated_checks_status_and_normal(mock_config_entry, mock_controller, pool_object_factory):
    obj = pool_object_factory("EI01", "EXTINSTR", "COVER", SNAME="Pool Cover", STATUS="OFF", NORMAL="ON")
    cover = PoolCover(mock_config_entry, mock_controller, obj)

    assert cover.isUpdated({"EI01": {"STATUS": "ON"}})
    assert cover.isUpdated({"EI01": {"NORMAL": "OFF"}})
    assert not cover.isUpdated({"EI01": {"SNAME": "x"}})
