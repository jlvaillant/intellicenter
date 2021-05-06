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
    SPEED_ATTR,
    SALT_ATTR,
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
                # unit_of_measurement=CONST_RPM,
                attribute_key=SPEED_ATTR,
                name="+ rpm"
              )
            )
        # elif object.objtype == CHEM_TYPE:
        #     if object.subtype == "ICHLOR":
        #         if SALT_ATTR in object.attributes:
        #             numbers.append(
        #                 PoolNumber(
        #                     entry,
        #                     controller,
        #                     object,
        #                     attribute_key=PRIM_ATTR,
        #                     name="+ (Salt)",
        #                 )
        #             )
    async_add_entities(numbers)


# -------------------------------------------------------------------------------------


class PoolNumber(PoolEntity, NumberEntity):
    """Representation of an Pentair number."""

    @property
    def value(self) -> bool:
        """Return the current value."""
        return self._poolObject[self._attribute_key]

    def set_value(self, value: float) -> None:
        """Update the current value."""

        changes = {self._attribute_key: str(int(value))}
        # self.requestChanges(changes)
        self._controller.requestChanges(
            "p0101", changes, waitForResponse=False
        )
