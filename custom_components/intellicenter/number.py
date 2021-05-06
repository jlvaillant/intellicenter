"""Pentair Intellicenter numbers."""

import logging
from typing import Optional

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.typing import HomeAssistantType

from . import PoolEntity
from .const import CONST_RPM, DOMAIN
from .pyintellicenter import (
    CHEM_TYPE,
    PRIM_ATTR,
    PUMP_TYPE,
    RPM_ATTR,
    SALT_ATTR,
    SPEED_ATTR,
    ModelController,
    PoolObject,
)

_LOGGER = logging.getLogger(__name__)

# -------------------------------------------------------------------------------------


async def async_setup_entry(
    hass: HomeAssistantType, entry: ConfigEntry, async_add_entities
):
    """Load pool numbers based on a config entry."""

    controller: ModelController = hass.data[DOMAIN][entry.entry_id].controller

    numbers = []

    object: PoolObject
    for object in controller.model.objectList:
        if object.objtype == PUMP_TYPE:
            numbers.append(
              PoolNumber(
                entry,
                controller,
                object,
                unit_of_measurement=CONST_RPM,
                attribute_key=RPM_ATTR,
                set_attribute_key=SPEED_ATTR,
                set_obj_name="p0101", # TODO: don't hardcode this
                name="+ rpm"
              )
            )
        elif object.objtype == CHEM_TYPE:
            if object.subtype == "ICHLOR":
                if SALT_ATTR in object.attributes:
                    numbers.append(
                        PoolNumber(
                            entry,
                            controller,
                            object,
                            attribute_key=PRIM_ATTR,
                            name="+ (Salt)",
                        )
                    )
    async_add_entities(numbers)


# -------------------------------------------------------------------------------------


class PoolNumber(PoolEntity, NumberEntity):
    """Representation of an Pentair number."""

    def __init__(
        self,
        entry: ConfigEntry,
        controller: ModelController,
        poolObject: PoolObject,
        unit_of_measurement: str = None,
        set_attribute_key: str = None,
        set_obj_name: str = None,
        **kwargs,
    ):
        """Initialize."""
        super().__init__(entry, controller, poolObject, **kwargs)
        self._set_attribute_key = set_attribute_key
        self._set_obj_name = set_obj_name
        self._unit_of_measurement = unit_of_measurement

    @property
    def unit_of_measurement(self) -> Optional[str]:
        """Return the unit of measurement of this entity, if any."""
        return self._unit_of_measurement

    @property
    def value(self) -> bool:
        """Return the current value."""
        return self._poolObject[self._attribute_key]

    def set_value(self, value: float) -> None:
        """Update the current value."""

        key = self._set_attribute_key if self._set_attribute_key else self._attribute_key
        changes = {key: str(int(value))}
        obj = self._set_obj_name if self._set_obj_name else self._poolObject.objnam
        self._controller.requestChanges(
            obj, changes, waitForResponse=False
        )
