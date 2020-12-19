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
            switches.append(PoolBody(entry, controller, object))
        elif object.objtype == 'CIRCUIT' and not object.isALight and object.isFeatured:
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
    """Representation of a body of water."""

    def __init__(self, entry: ConfigEntry, controller, poolObject):
        super().__init__(entry, controller, poolObject)
        self._extraStateAttributes = ['VOL','HEATER','HTMODE']

    @property
    def icon(self):
        return "mdi:pool"
