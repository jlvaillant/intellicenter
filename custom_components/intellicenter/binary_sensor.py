"""Pentair Intellicenter binary sensors."""

import logging

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.typing import HomeAssistantType

from . import PoolEntity
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistantType, entry: ConfigEntry, async_add_entities
):
    """Load pool sensors based on a config entry."""

    controller = hass.data[DOMAIN][entry.entry_id].controller

    sensors = []

    for object in controller.model.objectList:
        if (
            object.objtype == "CIRCUIT" and object.subtype == "FRZ"
        ) or object.objtype == "PUMP":
            sensors.append(PoolBinarySensor(entry, controller, object))
    async_add_entities(sensors)


class PoolBinarySensor(PoolEntity, BinarySensorEntity):
    """Representation of a Pentair Binary Sensor."""

    @property
    def is_on(self):
        """Return true if sensor is on."""
        return self._poolObject.status == self._poolObject.onStatus
