import logging
from typing import Any, Callable, Dict, List, Optional

from homeassistant.helpers.entity import Entity
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.typing import HomeAssistantType

from homeassistant.const import (
    DEVICE_CLASS_TEMPERATURE,
    TEMP_FAHRENHEIT,
    DEVICE_CLASS_ENERGY,
    POWER_WATT
)

from . import PoolEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry: ConfigEntry, async_add_entities):
    """Load pool sensors based on a config entry."""

    controller = hass.data[DOMAIN][entry.entry_id].controller

    sensors = []

    for object in controller.model.objectList:
        if object.objtype == 'SENSE':
            sensors.append(PoolSensor(entry, controller, object,
                                      device_class=DEVICE_CLASS_TEMPERATURE,
                                      unit_of_measurement=TEMP_FAHRENHEIT,
                                      attribute_key='PROBE'))
        elif object.objtype == 'PUMP':
            if object['PWR']:
                sensors.append(PoolSensor(entry, controller, object,
                                          device_class=DEVICE_CLASS_ENERGY,
                                          unit_of_measurement=POWER_WATT,
                                          attribute_key='PWR',
                                          name_suffix='power',
                                          rounding_factor=25))
        elif object.objtype == 'BODY':
            sensors.append(PoolSensor(entry, controller, object,
                                      device_class=DEVICE_CLASS_TEMPERATURE,
                                      unit_of_measurement=TEMP_FAHRENHEIT,
                                      attribute_key='LSTTMP',
                                      name_suffix='last temp'))
            sensors.append(PoolSensor(entry, controller, object,
                                      device_class=DEVICE_CLASS_TEMPERATURE,
                                      unit_of_measurement=TEMP_FAHRENHEIT,
                                      attribute_key='LOTMP',
                                      name_suffix='desired temp'))
    async_add_entities(sensors)


class PoolSensor(PoolEntity):
    """Representation of an Pentair sensor."""

    def __init__(self, entry: ConfigEntry, controller, poolObject,
                 device_class: str,
                 unit_of_measurement: str,
                 attribute_key: str,
                 name_suffix='',
                 rounding_factor: int = 0,
                 **kwargs
                 ):
        super().__init__(entry, controller, poolObject, **kwargs)
        self._attribute_key = attribute_key
        self._name_suffix = name_suffix
        self._device_class = device_class
        self._unit_of_measurement = unit_of_measurement
        self._rounding_factor = rounding_factor

    @property
    def name(self):
        """Return the name of the entity."""
        name = super().name
        if self._name_suffix:
            name += ' ' + self._name_suffix
        return name

    @property
    def unique_id(self):
        """Return a unique ID."""
        return super().unique_id + self._attribute_key

    @property
    def device_class(self) -> Optional[str]:
        """Return the class of this device, from component DEVICE_CLASSES."""
        self._device_class

    @property
    def state(self):
        """ Return the state of the sensor. """

        value = int(self._poolObject[self._attribute_key])

        # some sensors, like variable speed pumps, can vary constantly
        # so rounding their value to a nearest multiplier of 'rounding'
        # smoothes the curve and limits the number of updates in the log

        if self._rounding_factor:
            value = int(round(value/self._rounding_factor)*self._rounding_factor)

        return value

    @property
    def unit_of_measurement(self) -> Optional[str]:
        """Return the unit of measurement of this entity, if any."""
        return self._unit_of_measurement
