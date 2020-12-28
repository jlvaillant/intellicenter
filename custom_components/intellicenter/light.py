"""Pentair Intellicenter lights."""

from functools import reduce
import logging
from typing import Any, Dict

from homeassistant.components.light import ATTR_EFFECT, SUPPORT_EFFECT, LightEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback
from homeassistant.helpers.typing import HomeAssistantType

from . import PoolEntity
from .const import DOMAIN
from .pyintellicenter import ModelController, PoolObject

_LOGGER = logging.getLogger(__name__)

LIGHTS_EFFECTS = {
    "PARTY": "Party Mode",
    "CARIB": "Caribbean",
    "SSET": "Sunset",
    "ROMAN": "Romance",
    "AMERCA": "American",
    "ROYAL": "Royal",
    "WHITER": "White",
    "REDR": "Red",
    "BLUER": "Blue",
    "GREENR": "Green",
    "MAGNTAR": "Magenta",
}


async def async_setup_entry(
    hass: HomeAssistantType, entry: ConfigEntry, async_add_entities
):
    """Load pool lights based on a config entry."""

    controller: ModelController = hass.data[DOMAIN][entry.entry_id].controller

    lights = []

    object: PoolObject
    for object in controller.model.objectList:
        if object.isALight:
            lights.append(
                PoolLight(
                    entry,
                    controller,
                    object,
                    LIGHTS_EFFECTS if object.supportColorEffects else None,
                )
            )
        elif object.isALightShow:

            supportColorEffects = reduce(
                lambda x, y: x and y,
                map(
                    lambda obj: controller.model[obj["CIRCUIT"]].supportColorEffects,
                    controller.model.getChildren(object),
                ),
                True,
            )
            lights.append(
                PoolLight(
                    entry,
                    controller,
                    object,
                    LIGHTS_EFFECTS if supportColorEffects else None,
                )
            )

    async_add_entities(lights)


class PoolLight(PoolEntity, LightEntity):
    """Representation of an Pentair light."""

    def __init__(
        self,
        entry: ConfigEntry,
        controller: ModelController,
        poolObject: PoolObject,
        colorEffects: dict = None,
    ):
        """Initialize."""
        super().__init__(entry, controller, poolObject)
        # USE appears to contain extra info like color...
        self._extraStateAttributes = ["USE"]

        self._features = 0

        self._lightEffects = colorEffects
        self._reversedLightEffects = (
            dict(map(reversed, colorEffects.items())) if colorEffects else None
        )

        if self._lightEffects:
            self._features |= SUPPORT_EFFECT

    @property
    def supported_features(self) -> int:
        """Return supported features."""
        return self._features

    @property
    def effect_list(self) -> list:
        """Return the list of supported effects."""
        return list(self._reversedLightEffects.keys())

    @property
    def effect(self) -> str:
        """Return the current effect."""
        return self._lightEffects.get(self._poolObject["USE"])

    @property
    def is_on(self) -> bool:
        """Return the state of the light."""
        return self._poolObject.status == self._poolObject.onStatus

    def turn_off(self, **kwargs: Any) -> None:
        """Turn off the light."""
        self.requestChanges({"STATUS": "OFF"})

    def turn_on(self, **kwargs: Any) -> None:
        """Turn on the light."""

        changes = {"STATUS": self._poolObject.onStatus}

        if ATTR_EFFECT in kwargs:
            effect = kwargs[ATTR_EFFECT]
            new_use = self._reversedLightEffects.get(effect)
            if new_use:
                changes["ACT"] = new_use

        self.requestChanges(changes)

    @callback
    def _update_callback(self, updates: Dict[str, PoolObject]):
        """Update the entity if its underlying pool object has changed."""

        if self._poolObject.objnam in updates:
            self._available = True
            _LOGGER.debug(f"updating {self} from {self._poolObject}")
            self.async_write_ha_state()
