"""Pentair IntelliCenter Integration."""
import asyncio
import logging
from typing import Any, Dict, Optional

from homeassistant.components.binary_sensor import DOMAIN as BINARY_SENSOR_DOMAIN
from homeassistant.components.light import DOMAIN as LIGHT_DOMAIN
from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN
from homeassistant.components.water_heater import DOMAIN as WATER_HEATER_DOMAIN
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, EVENT_HOMEASSISTANT_STOP
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import dispatcher
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN
from .pyintellicenter import ConnectionHandler, ModelController, PoolModel

_LOGGER = logging.getLogger(__name__)

# here is the list of platforms we support
PLATFORMS = [
    LIGHT_DOMAIN,
    SENSOR_DOMAIN,
    SWITCH_DOMAIN,
    BINARY_SENSOR_DOMAIN,
    WATER_HEATER_DOMAIN,
]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Pentair IntelliCenter Integration."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up IntelliCenter integration from a config entry."""

    # we are only interested in a subset of all objects
    def filterFunc(object):
        """Return true for the objects we care about."""
        return object.status and object.objtype in [
            "BODY",
            "SENSE",
            "PUMP",
            "HEATER",
            "CIRCUIT",
        ]

    model = PoolModel(filterFunc)

    controller = ModelController(entry.data[CONF_HOST], model, loop=hass.loop)

    class Handler(ConnectionHandler):

        UPDATE_SIGNAL = DOMAIN + "_UPDATE_" + entry.entry_id

        def started(self, controller):

            _LOGGER.info(f"connected to system: '{controller.systemInfo.propName}'")

            for object in controller.model:
                _LOGGER.debug(f"   loaded {object}")

            async def setup_platforms():
                """Set up platforms."""
                await asyncio.gather(
                    *[
                        hass.config_entries.async_forward_entry_setup(entry, platform)
                        for platform in PLATFORMS
                    ]
                )

            hass.async_create_task(setup_platforms())

        @callback
        def reconnected(self, controller):
            """Handle reconnection from the Pentair system."""
            _LOGGER.info(f"reconnected to system: '{controller.systemInfo.propName}'")
            dispatcher.async_dispatcher_send(
                hass, self.UPDATE_SIGNAL, controller.model.objectList
            )

        @callback
        def disconnected(self, controller, exc):
            """Handle updates from the Pentair system."""
            _LOGGER.info(
                f"disconnected from system: '{controller.systemInfo.propName}'"
            )
            dispatcher.async_dispatcher_send(
                hass, DOMAIN + "_DISCONNECT_" + entry.entry_id
            )

        @callback
        def updated(self, controller, changes):
            """Handle updates from the Pentair system."""
            for object in changes:
                _LOGGER.debug(f"received update for {object}")
            dispatcher.async_dispatcher_send(hass, self.UPDATE_SIGNAL, changes)

    try:

        handler = Handler(controller)

        await handler.start()

        hass.data.setdefault(DOMAIN, {})

        hass.data[DOMAIN][entry.entry_id] = handler

        # subscribe to Home Assistant STOP event to do some cleanup

        async def on_hass_stop(event):
            """Stop push updates when hass stops."""
            handler.stop()

        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, on_hass_stop)

        return True
    except ConnectionRefusedError as err:
        raise ConfigEntryNotReady from err


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload IntelliCenter config entry."""

    # Unload entities for this entry/device.

    all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS
            ]
        )
    )

    # Cleanup
    handler = hass.data[DOMAIN].pop(entry.entry_id, None)

    _LOGGER.info(f"unloading integration {entry.entry_id}")
    if handler:
        handler.stop()

    # if it was the last instance of this integration, clear up the DOMAIN entry
    if not hass.data[DOMAIN]:
        del hass.data[DOMAIN]

    return True


class PoolEntity(Entity):
    """Representation of an Pool entity linked to an pool object."""

    def __init__(self, entry: ConfigEntry, controller, poolObject):
        """Initialize a Pool entity."""
        self._entry_id = entry.entry_id
        self._controller = controller
        self._poolObject = poolObject
        self._available = True
        self._extraStateAttributes = []

        _LOGGER.debug(f"mapping {poolObject}")

    async def async_added_to_hass(self):
        """Entity is added to Home Assistant."""
        self.async_on_remove(
            dispatcher.async_dispatcher_connect(
                self.hass, DOMAIN + "_UPDATE_" + self._entry_id, self._update_callback
            )
        )

        self.async_on_remove(
            dispatcher.async_dispatcher_connect(
                self.hass,
                DOMAIN + "_DISCONNECT_" + self._entry_id,
                self._disconnect_callback,
            )
        )

    async def async_will_remove_from_hass(self) -> None:
        """Entity is removed from Home Assistant."""
        _LOGGER.debug(f"removing entity: {self.unique_id}")

    @property
    def available(self):
        """Return True is the entity is available."""
        return self._available

    @property
    def name(self):
        """Return the name of the entity."""
        return self._poolObject.sname

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._entry_id + self._poolObject.objnam

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    @property
    def device_info(self):
        """Return the device info."""

        systemInfo = self._controller.systemInfo

        return {
            "identifiers": {(DOMAIN, self._entry_id)},
            "manufacturer": "Pentair",
            "model": "IntelliCenter",
            "name": systemInfo.propName,
            "sw_version": systemInfo.swVersion,
        }

    @property
    def device_state_attributes(self) -> Optional[Dict[str, Any]]:
        """Return the state attributes of the entity."""

        object = self._poolObject

        objectType = object.objtype
        if object.subtype:
            objectType += f"/{object.subtype}"

        attributes = {"OBJNAM": object.objnam, "OBJTYPE": objectType}

        if object.status:
            attributes["Status"] = object.status

        for attribute in self._extraStateAttributes:
            if object[attribute]:
                attributes[attribute] = object[attribute]

        return attributes

    def requestChanges(self, changes: dict) -> None:
        """Request changes as key:value pairs to the associated Pool object."""
        # since we don't care about waiting for the response we set waitForResponse to False
        # whatever changes were requested will be reflected as an update if successful
        # (also I found out there is no event loop in that thread for a Future would fail)
        self._controller.requestChanges(
            self._poolObject.objnam, changes, waitForResponse=False
        )

    @callback
    def _update_callback(self, changes):
        """Update the entity if its underlying pool object has changed."""
        for object in changes:
            if object.objnam == self._poolObject.objnam:
                self._available = True
                self.async_write_ha_state()

    @callback
    def _disconnect_callback(self):
        """Mark the entity as unavailable after being disconnected from the server."""
        self._available = False
        self.async_write_ha_state()
