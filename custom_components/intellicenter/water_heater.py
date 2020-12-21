"""Pentair Intellicenter water heaters."""

import logging

from homeassistant.components.water_heater import (
    SUPPORT_OPERATION_MODE,
    SUPPORT_TARGET_TEMPERATURE,
    WaterHeaterEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_TEMPERATURE,
    STATE_IDLE,
    STATE_OFF,
    STATE_ON,
    TEMP_FAHRENHEIT,
)
from homeassistant.helpers.typing import HomeAssistantType

from . import PoolEntity
from .const import DOMAIN
from .pyintellicenter import ModelController, PoolObject

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistantType, entry: ConfigEntry, async_add_entities
):
    """Load pool sensors based on a config entry."""

    controller = hass.data[DOMAIN][entry.entry_id].controller

    # here we try to figure out which heater, if any, can be used for a given
    # body of water

    # first find all heaters
    heaters = [object for object in controller.model if object.objtype == "HEATER"]

    # then for each heater, find which bodies it handles
    body_to_heater_map = {}
    for heater in heaters:
        bodies = heater["BODY"].split(" ")
        for body_id in bodies:
            body_to_heater_map[body_id] = heater.objnam

    water_heaters = []

    for (body_id, heater_id) in body_to_heater_map.items():
        body = controller.model[body_id]
        if body:
            water_heaters.append(PoolWaterHeater(entry, controller, body, heater_id))

    async_add_entities(water_heaters)


class PoolWaterHeater(PoolEntity, WaterHeaterEntity):
    """Representation of a Pentair water heater."""

    def __init__(
        self,
        entry: ConfigEntry,
        controller: ModelController,
        poolObject: PoolObject,
        heater_id,
    ):
        """Initialize."""
        super().__init__(entry, controller, poolObject)
        self._heater_id = heater_id

    @property
    def name(self):
        """Return the name of the entity."""
        name = super().name
        return name + " heater"

    @property
    def unique_id(self):
        """Return a unique ID."""
        return super().unique_id + "LOTMP"

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return SUPPORT_TARGET_TEMPERATURE | SUPPORT_OPERATION_MODE

    @property
    def icon(self):
        """Return the entity icon."""
        return "mdi:thermometer"

    @property
    def temperature_unit(self):
        """Return the unit of measurement used by the platform."""
        return TEMP_FAHRENHEIT

    @property
    def min_temp(self):
        """Return the minimum value."""
        # this is totally arbitrary...
        return 40.0

    @property
    def max_temp(self):
        """Return the maximum temperature."""
        return float(self._poolObject["HITMP"])

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return float(self._poolObject["LSTTMP"])

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return float(self._poolObject["LOTMP"])

    def set_temperature(self, **kwargs):
        """Set new target temperatures."""
        target_temperature = kwargs.get(ATTR_TEMPERATURE)
        self.requestChanges({"LOTMP": str(int(target_temperature))})

    @property
    def current_operation(self):
        """Return current operation."""
        heater = self._poolObject["HEATER"]
        htmode = self._poolObject["HTMODE"]
        if heater == self._heater_id:
            return "heating" if htmode == "1" else STATE_IDLE
        return STATE_OFF

    @property
    def operation_list(self):
        """Return the list of available operation modes."""
        return [STATE_ON, STATE_OFF]

    def set_operation_mode(self, operation_mode):
        """Set new target operation mode."""
        value = self._heater_id if operation_mode == STATE_ON else "00000"
        self.requestChanges({"HEATER": value})
