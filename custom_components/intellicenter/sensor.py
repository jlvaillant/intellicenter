"""Pentair Intellicenter sensors."""

import logging
from typing import Optional

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfElectricPotential, UnitOfPower
from homeassistant.core import HomeAssistant

try:
    from homeassistant.const import UnitOfRatio

    PARTS_PER_MILLION = UnitOfRatio.PARTS_PER_MILLION
except ImportError:  # older Home Assistant releases without UnitOfRatio
    from homeassistant.const import (
        CONCENTRATION_PARTS_PER_MILLION as PARTS_PER_MILLION,
    )

from . import PoolEntity
from .const import CONST_GPM, CONST_RPM, DOMAIN
from .pyintellicenter import (
    BODY_TYPE,
    CHEM_TYPE,
    GPM_ATTR,
    LOTMP_ATTR,
    LSTTMP_ATTR,
    ORPTNK_ATTR,
    ORPVAL_ATTR,
    PHTNK_ATTR,
    PHVAL_ATTR,
    PUMP_TYPE,
    PWR_ATTR,
    QUALTY_ATTR,
    RPM_ATTR,
    SALT_ATTR,
    SENSE_TYPE,
    SOURCE_ATTR,
    ModelController,
    PoolObject,
)

_LOGGER = logging.getLogger(__name__)

# -------------------------------------------------------------------------------------


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
):
    """Load pool sensors based on a config entry."""

    controller: ModelController = hass.data[DOMAIN][entry.entry_id].controller

    sensors = []

    obj: PoolObject
    for obj in controller.model.objectList:
        if obj.objtype == SENSE_TYPE:
            sensors.append(
                PoolSensor(
                    entry,
                    controller,
                    obj,
                    device_class=SensorDeviceClass.TEMPERATURE,
                    attribute_key=SOURCE_ATTR,
                )
            )
        elif obj.objtype == PUMP_TYPE:
            if obj[PWR_ATTR]:
                sensors.append(
                    PoolSensor(
                        entry,
                        controller,
                        obj,
                        device_class=SensorDeviceClass.POWER,
                        unit_of_measurement=UnitOfPower.WATT,
                        attribute_key=PWR_ATTR,
                        name="+ power",
                        rounding_factor=25,
                    )
                )
            if obj[RPM_ATTR]:
                sensors.append(
                    PoolSensor(
                        entry,
                        controller,
                        obj,
                        device_class=None,
                        unit_of_measurement=CONST_RPM,
                        attribute_key=RPM_ATTR,
                        name="+ rpm",
                    )
                )
            if obj[GPM_ATTR]:
                sensors.append(
                    PoolSensor(
                        entry,
                        controller,
                        obj,
                        device_class=None,
                        unit_of_measurement=CONST_GPM,
                        attribute_key=GPM_ATTR,
                        name="+ gpm",
                    )
                )
        elif obj.objtype == BODY_TYPE:
            sensors.append(
                PoolSensor(
                    entry,
                    controller,
                    obj,
                    device_class=SensorDeviceClass.TEMPERATURE,
                    attribute_key=LSTTMP_ATTR,
                    name="+ last temp",
                )
            )
            sensors.append(
                PoolSensor(
                    entry,
                    controller,
                    obj,
                    device_class=SensorDeviceClass.TEMPERATURE,
                    attribute_key=LOTMP_ATTR,
                    name="+ desired temp",
                )
            )
        elif obj.objtype == CHEM_TYPE:
            if obj.subtype == "ICHEM":
                if PHVAL_ATTR in obj.attributes:
                    sensors.append(
                        PoolSensor(
                            entry,
                            controller,
                            obj,
                            device_class=None,
                            unit_of_measurement="pH",
                            attribute_key=PHVAL_ATTR,
                            name="+ (pH)",
                        )
                    )
                if ORPVAL_ATTR in obj.attributes:
                    sensors.append(
                        PoolSensor(
                            entry,
                            controller,
                            obj,
                            device_class=None,
                            unit_of_measurement=UnitOfElectricPotential.MILLIVOLT,
                            attribute_key=ORPVAL_ATTR,
                            name="+ (ORP)",
                        )
                    )
                if QUALTY_ATTR in obj.attributes:
                    sensors.append(
                        PoolSensor(
                            entry,
                            controller,
                            obj,
                            device_class=None,
                            attribute_key=QUALTY_ATTR,
                            name="+ (Water Quality)",
                        )
                    )
                if PHTNK_ATTR in obj.attributes:
                    sensors.append(
                        PoolSensor(
                            entry,
                            controller,
                            obj,
                            device_class=None,
                            attribute_key=PHTNK_ATTR,
                            name="+ (Ph Tank Level)",
                        )
                    )
                if ORPTNK_ATTR in obj.attributes:
                    sensors.append(
                        PoolSensor(
                            entry,
                            controller,
                            obj,
                            device_class=None,
                            attribute_key=ORPTNK_ATTR,
                            name="+ (ORP Tank Level)",
                        )
                    )
            elif obj.subtype == "ICHLOR":
                if SALT_ATTR in obj.attributes:
                    sensors.append(
                        PoolSensor(
                            entry,
                            controller,
                            obj,
                            device_class=None,
                            unit_of_measurement=PARTS_PER_MILLION,
                            attribute_key=SALT_ATTR,
                            name="+ (Salt)",
                        )
                    )
    async_add_entities(sensors)


# -------------------------------------------------------------------------------------


class PoolSensor(PoolEntity, SensorEntity):
    """Representation of an Pentair sensor."""

    def __init__(
        self,
        entry: ConfigEntry,
        controller: ModelController,
        poolObject: PoolObject,
        device_class: Optional[SensorDeviceClass],
        rounding_factor: int = 0,
        **kwargs,
    ):
        """Initialize."""
        super().__init__(entry, controller, poolObject, **kwargs)
        self._attr_device_class = device_class
        self._rounding_factor = rounding_factor
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def state(self) -> str:
        """Return the state of the sensor."""

        value = str(self._poolObject[self._attribute_key])

        # some sensors, like variable speed pumps, can vary constantly
        # so rounding their value to a nearest multiplier of 'rounding'
        # smoothes the curve and limits the number of updates in the log

        if self._rounding_factor:
            value = str(int(round(int(value) / self._rounding_factor) * self._rounding_factor))

        return value

    @property
    def native_unit_of_measurement(self) -> Optional[str]:
        """Return the unit of measurement of this entity, if any."""
        if self._attr_device_class == SensorDeviceClass.TEMPERATURE:
            return self.pentairTemperatureSettings()
        return self._attr_native_unit_of_measurement
