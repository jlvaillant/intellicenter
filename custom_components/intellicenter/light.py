import logging
from typing import Any, Callable, Dict, List, Optional

from homeassistant.components.light import LightEntity, SUPPORT_EFFECT, ATTR_EFFECT
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
            lights.append(PoolLight(entry, controller, object))
    async_add_entities(lights)

LIGHTS_EFFECTS_BY_TYPE = {
    'INTELLI': {
        'PARTY': 'Party Mode',  'CARIB': 'Caribbean', 'SSET': 'Sunset', 'ROMAN': 'Romance', 'AMERCA': 'American',
        'ROYAL': 'Royal', 'WHITER': 'White', 'REDR': 'Red', 'BLUER': 'Blue', 'GREENR': 'Green', 'MAGNTAR': 'Magenta'
    }}

class PoolLight(PoolEntity, LightEntity):
    """Representation of an Pentair light."""

    def __init__(self, entry: ConfigEntry, controller, poolObject):
        super().__init__(entry, controller, poolObject)
        # USE appears to contain extra info like color...
        self._extraStateAttributes = ['USE']

        self._features = 0

        self._lightEffects = LIGHTS_EFFECTS_BY_TYPE.get(poolObject.subtype,{})
        self._reversedLightEffects = dict(map(reversed,self._lightEffects.items()))

        if self._lightEffects:
            self._features |= SUPPORT_EFFECT

    @property
    def supported_features(self) -> int:
        """Flag supported features."""
        return self._features

    @property
    def effect_list(self) -> list:
        """Return the list of supported effects."""
        return list(self._reversedLightEffects.keys())

    @property
    def effect(self) -> str:
        """Return the current effect."""
        return self._lightEffects.get(self._poolObject['USE'])

    @property
    def is_on(self) -> bool:
        """Return the state of the light."""
        return self._poolObject.status == self._poolObject.onStatus

    def turn_off(self, **kwargs: Any) -> None:
        """Turn off the light."""
        self.requestChanges({'STATUS': 'OFF'})

    def turn_on(self, **kwargs: Any) -> None:
        """Turn on the light."""
 
        changes = {'STATUS': self._poolObject.onStatus}

        if ATTR_EFFECT in kwargs:
            effect = kwargs[ATTR_EFFECT]
            new_use = self._reversedLightEffects.get(effect)
            if new_use:
                changes['ACT'] = new_use
        
        self.requestChanges(changes)
