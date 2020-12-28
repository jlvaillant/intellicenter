"""Pentair Intellicenter sensors."""

import logging
from typing import Optional

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    DEVICE_CLASS_ENERGY,
    DEVICE_CLASS_TEMPERATURE,
    POWER_WATT,
)
from homeassistant.helpers.typing import HomeAssistantType

from . import PoolEntity
from .const import CONST_GPM, CONST_RPM, DOMAIN
from .pyintellicenter import ModelController, PoolObject

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistantType, entry: ConfigEntry, async_add_entities
):
    """Load pool sensors based on a config entry."""

    controller: ModelController = hass.data[DOMAIN][entry.entry_id].controller

    sensors = []

    object: PoolObject
    for object in controller.model.objectList:
        if object.objtype == "SENSE":
            sensors.append(
                PoolSensor(
                    entry,
                    controller,
                    object,
                    device_class=DEVICE_CLASS_TEMPERATURE,
                    attribute_key="SOURCE",
                )
            )
        elif object.objtype == "PUMP":
            if object["PWR"]:
                sensors.append(
                    PoolSensor(
                        entry,
                        controller,
                        object,
                        device_class=DEVICE_CLASS_ENERGY,
                        unit_of_measurement=POWER_WATT,
                        attribute_key="PWR",
                        name_suffix="power",
                        rounding_factor=25,
                    )
                )
            if object["RPM"]:
                sensors.append(
                    PoolSensor(
                        entry,
                        controller,
                        object,
                        device_class=None,
                        unit_of_measurement=CONST_RPM,
                        attribute_key="RPM",
                        name_suffix="rpm",
                    )
                )
            if object["GPM"]:
                sensors.append(
                    PoolSensor(
                        entry,
                        controller,
                        object,
                        device_class=None,
                        unit_of_measurement=CONST_GPM,
                        attribute_key="GPM",
                        name_suffix="gpm",
                    )
                )
        elif object.objtype == "BODY":
            sensors.append(
                PoolSensor(
                    entry,
                    controller,
                    object,
                    device_class=DEVICE_CLASS_TEMPERATURE,
                    attribute_key="LSTTMP",
                    name_suffix="last temp",
                )
            )
            sensors.append(
                PoolSensor(
                    entry,
                    controller,
                    object,
                    device_class=DEVICE_CLASS_TEMPERATURE,
                    attribute_key="LOTMP",
                    name_suffix="desired temp",
                )
            )
    async_add_entities(sensors)


class PoolSensor(PoolEntity):
    """Representation of an Pentair sensor."""

    def __init__(
        self,
        entry: ConfigEntry,
        controller: ModelController,
        poolObject: PoolObject,
        device_class: str,
        unit_of_measurement: str = None,
        rounding_factor: int = 0,
        **kwargs,
    ):
        """Initialize."""
        super().__init__(entry, controller, poolObject, **kwargs)
        self._device_class = device_class
        self._unit_of_measurement = unit_of_measurement
        self._rounding_factor = rounding_factor

    @property
    def device_class(self) -> Optional[str]:
        """Return the class of this device, from component DEVICE_CLASSES."""
        self._device_class

    @property
    def state(self):
        """Return the state of the sensor."""

        value = int(self._poolObject[self._attribute_key])

        # some sensors, like variable speed pumps, can vary constantly
        # so rounding their value to a nearest multiplier of 'rounding'
        # smoothes the curve and limits the number of updates in the log

        if self._rounding_factor:
            value = int(round(value / self._rounding_factor) * self._rounding_factor)

        return value

    @property
    def unit_of_measurement(self) -> Optional[str]:
        """Return the unit of measurement of this entity, if any."""
        if self._device_class == DEVICE_CLASS_TEMPERATURE:
            return self.pentairTemperatureSettings()
        return self._unit_of_measurement
