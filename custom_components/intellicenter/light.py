import logging
from typing import Any, Callable, Dict, List, Optional

from homeassistant.components.light import LightEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.typing import HomeAssistantType

from . import PoolEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry: ConfigEntry, async_add_entities):
    """Load Intellicenter lights based on a config entry."""

    controller = hass.data[DOMAIN][entry.entry_id].controller

    lights = []

    for object in controller.model.objectList:
        if object.isALight:
            _LOGGER.debug(f"mapping {object}")
            lights.append(PoolLight(entry, controller, object))
    async_add_entities(lights)

class PoolLight(PoolEntity, LightEntity):
    """Representation of an Pentair light."""

    @property
    def is_on(self) -> bool:
        """Return the state of the light."""
        return self._poolObject.status == self._poolObject.onStatus

    def turn_off(self, **kwargs: Any) -> None:
        """Turn off the light."""
        self.requestChanges({'STATUS': 'OFF'})

    def turn_on(self, **kwargs: Any) -> None:
        """Turn off the light."""
        self.requestChanges({'STATUS': self._poolObject.onStatus})