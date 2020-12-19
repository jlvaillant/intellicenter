import logging
from typing import Any, Dict, List, Optional

from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.typing import HomeAssistantType
from homeassistant.config_entries import ConfigEntry

from . import PoolEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry: ConfigEntry, async_add_entities):
    """Load Apple TV media player based on a config entry."""
    name = None # ??? config_entry.data[CONF_NAME]
    controller = hass.data[DOMAIN][entry.entry_id].controller

    switches = []

    for object in controller.model.objectList:
        if object.objtype == 'BODY':
            _LOGGER.debug(f"mapping {object} to a switch")
            switches.append(PoolBody(entry, controller, object))
        elif object.objtype == 'CIRCUIT' and not object.isALight and object.isFeatured:
            _LOGGER.debug(f"mapping {object} to a switch")
            switches.append(PoolCircuit(entry, controller, object))
           
    async_add_entities(switches)

class PoolCircuit(PoolEntity, SwitchEntity):
    """Representation of an pool circuit."""

    @property
    def is_on(self) -> bool:
        """Return the state of the circuit."""
        return self._poolObject.status == self._poolObject.onStatus

    def turn_off(self, **kwargs: Any) -> None:
        """Turn off the switch."""
        self.requestChanges({'STATUS': self._poolObject.offStatus})

    def turn_on(self, **kwargs: Any) -> None:
        """Turn off the switch."""
        self.requestChanges({'STATUS': self._poolObject.onStatus})

class PoolBody(PoolCircuit):

    @property
    def icon(self):
        return "mdi:pool"

    @property
    def device_state_attributes(self) -> Optional[Dict[str, Any]]:
        """Return the state attributes of the entity."""

        attributes = super().device_state_attributes

        object = self._poolObject

        if object['VOL']:
            attributes['Volume'] = object['VOL']

        if object['HEATER']:
            attributes['HEATER'] = object['HEATER']

        if object['HTMODE']:
            attributes['HTMODE'] = object['HTMODE']

        # for attribute in self._poolObject.attributes:
        #     value = self._poolObject[attribute]
        #     if value:
        #         attributes[attribute] = value

        return attributes