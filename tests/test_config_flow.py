"""Tests for the intellicenter config flow."""

from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant import config_entries, data_entry_flow
from homeassistant.const import CONF_HOST

from custom_components.intellicenter.const import DOMAIN
from custom_components.intellicenter.pyintellicenter import SystemInfo

CONFIG_FLOW_BASE_CONTROLLER = "custom_components.intellicenter.config_flow.BaseController"


def _system_info(sname="pool-1") -> SystemInfo:
    return SystemInfo(
        "_5451",
        {"PROPNAME": "Test Pool", "VER": "1.2.3", "MODE": "ENGLISH", "SNAME": sname},
    )


def _fake_controller(system_info: SystemInfo = None, start_exc: Exception = None) -> MagicMock:
    controller = MagicMock()
    controller.start = AsyncMock(side_effect=start_exc)
    controller.stop = MagicMock()
    controller.systemInfo = system_info
    return controller


async def test_user_step_shows_form_initially(hass):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}


async def test_user_step_creates_entry_on_success(hass):
    with patch(CONFIG_FLOW_BASE_CONTROLLER, return_value=_fake_controller(_system_info())):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_HOST: "1.2.3.4"}
        )

    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["title"] == "Test Pool"
    assert result["data"] == {CONF_HOST: "1.2.3.4"}


async def test_user_step_cannot_connect(hass):
    with patch(
        CONFIG_FLOW_BASE_CONTROLLER,
        return_value=_fake_controller(start_exc=ConnectionRefusedError()),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_HOST: "1.2.3.4"}
        )

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_user_step_already_configured(hass):
    with patch(CONFIG_FLOW_BASE_CONTROLLER, return_value=_fake_controller(_system_info())):
        first = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        await hass.config_entries.flow.async_configure(
            first["flow_id"], {CONF_HOST: "1.2.3.4"}
        )

        second = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            second["flow_id"], {CONF_HOST: "5.6.7.8"}
        )

    assert result["type"] == data_entry_flow.FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_zeroconf_discovery_shows_confirm_dialog(hass):
    discovery_info = MagicMock(host="1.2.3.4")

    with patch(CONFIG_FLOW_BASE_CONTROLLER, return_value=_fake_controller(_system_info())):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_ZEROCONF},
            data=discovery_info,
        )

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "zeroconf_confirm"


async def test_zeroconf_discovery_aborts_if_host_already_configured(hass, mock_config_entry):
    discovery_info = MagicMock(host="1.2.3.4")

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=discovery_info,
    )

    assert result["type"] == data_entry_flow.FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_zeroconf_confirm_creates_entry(hass):
    discovery_info = MagicMock(host="1.2.3.4")

    with patch(CONFIG_FLOW_BASE_CONTROLLER, return_value=_fake_controller(_system_info())):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_ZEROCONF},
            data=discovery_info,
        )
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["data"] == {CONF_HOST: "1.2.3.4"}
