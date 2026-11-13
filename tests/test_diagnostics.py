"""Tests for the intellicenter diagnostics support."""

from custom_components.intellicenter.diagnostics import async_get_config_entry_diagnostics


async def test_diagnostics_returns_objects_from_the_model(
    hass, mock_config_entry, setup_integration, pool_model
):
    pool_model.addObject(
        "C0006", {"OBJTYP": "CIRCUIT", "SUBTYP": "POOL", "SNAME": "Pool", "STATUS": "ON"}
    )

    diagnostics = await async_get_config_entry_diagnostics(hass, mock_config_entry)

    assert diagnostics == {
        "objects": [
            {
                "objnam": "C0006",
                "objtype": "CIRCUIT",
                "subtype": "POOL",
                "properties": {"SNAME": "Pool", "STATUS": "ON"},
            }
        ]
    }


async def test_diagnostics_with_no_objects(hass, mock_config_entry, setup_integration):
    diagnostics = await async_get_config_entry_diagnostics(hass, mock_config_entry)

    assert diagnostics == {"objects": []}
