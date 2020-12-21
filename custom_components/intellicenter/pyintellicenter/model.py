"""Model class for storing a Pentair system."""

import logging
from typing import List

_LOGGER = logging.getLogger(__name__)

# ---------------------------------------------------------------------------

# cSpell:disable

ALL_KNOWN_ATTRIBUTES = [
    "ACT",
    "ADDRESS",
    "AVAIL",
    "BODY",
    "BOOST",
    "CHILD",
    "CIRCUIT",
    "CITY",
    "CLK24A",
    "COUNTRY",
    "DAY",
    "DLSTIM",
    "DNTSTP",
    "EMAIL",
    "EMAIL2",
    "FEATR",
    "GPM",
    "HEATER",
    "HEATING",
    "HITMP",
    "HTMODE",
    "HTSRC",
    "LIMIT",
    "LISTORD",
    "LOCX",
    "LOCY",
    "LOTMP",
    "LSTTMP",
    "MANHT",
    "MANUAL",
    "MIN",
    "MODE",
    "NAME",
    "OBJTYP",
    "OFFSET",
    "PARENT",
    "PASSWRD",
    "PHONE",
    "PHONE2",
    "PROBE",
    "PROPNAME",
    "PWR",
    "RLY",
    "RPM",
    "SELECT",
    "SERVICE",
    "SET",
    "SHOMNU",
    "SINGLE",
    "SNAME",
    "SPEED",
    "SRIS",
    "SSET",
    "START",
    "STATE",
    "STATUS",
    "STOP",
    "SUBTYP",
    "SWIM",
    "SYNC",
    "TEMPNC",
    "TIME",
    "TIMOUT",
    "TIMZON",
    "USAGE",
    "USE",
    "VACFLO",
    "VACTIM",
    "VALVE",
    "VER",
    "VOL",
    "ZIP",
]
# cSpell:enable


class PoolObject:
    """Representation of an object in the Pentair system."""

    def __init__(self, objnam, params):
        """Initialize."""
        self._objnam = objnam
        self._objtyp = params.pop("OBJTYP")
        self._subtyp = params.pop("SUBTYP", None)
        self._properties = params

    @property
    def objnam(self):
        """Return the id of the object (OBJNAM)."""
        return self._objnam

    @property
    def sname(self):
        """Return the friendly name (SNAME)."""
        return self._properties.get("SNAME")

    @property
    def objtype(self):
        """Return the object type."""
        return self._objtyp

    @property
    def subtype(self):
        """Return the object subtype."""
        return self._subtyp

    @property
    def status(self):
        """Return the object status."""
        return self._properties.get("STATUS")

    @property
    def offStatus(self):
        """Return the value of an OFF status."""
        return "4" if self.objtype == "PUMP" else "OFF"

    @property
    def onStatus(self):
        """Return the value of an ON status."""
        return "10" if self.objtype == "PUMP" else "ON"

    @property
    def isALight(self):
        """Return True is the object is a light."""
        return self.objtype == "CIRCUIT" and self.subtype in [
            "LITSHO",
            "LIGHT",
            "INTELLI",
            "GLOW",
            "GLOWT",
            "DIMMER",
        ]

    @property
    def isFeatured(self):
        """Return True is the object is Featured."""
        return self["FEATR"] == "ON"

    def __getitem__(self, key):
        """Return the value for attribure 'key'."""
        return self._properties.get(key)

    def __str__(self):
        """Return a friendly string representation."""
        str = f"{self.objnam} "
        str += (
            f"({self.objtype}/{self.subtype}):"
            if self.subtype
            else f"({self.objtype}):"
        )
        for (key, value) in self._properties.items():
            str += f" {key}: {value}"
        return str

    @property
    def attributes(self):
        """Return the list of attributes for this object."""
        return list(self._properties.keys())

    def update(self, updates):
        """Update the object from a set of key/value pairs, return true is the object HAS changed."""

        changed = False

        for (key, value) in updates.items():
            if key in self._properties:
                if self._properties[key] == value:
                    # ignore unchanged existing value
                    continue
            self._properties[key] = value
            changed = True

        return changed


# ---------------------------------------------------------------------------


class PoolModel:
    """Representation of a subset of the underlying Pentair system."""

    def __init__(self, filterFunc=lambda object: True):
        """Initialize."""
        self._objects = {}
        self._system = None
        self._filterFunc = filterFunc

    @property
    def objectList(self):
        """Return the list of objects contained in the model."""
        return self._objects.values()

    @property
    def numObjects(self):
        """Return the number of objects contained in the model."""
        return len(self._objects)

    def __iter__(self):
        """Allow iteration over all values."""
        return iter(self._objects.values())

    def __getitem__(self, key):
        """Return an object based on its objnam."""
        return self._objects.get(key)

    def getByType(self, type: str, subtype: str = None) -> List[PoolObject]:
        """Return all the object which match the type and the optional subtype.

        examples:
            getByType('BODY') will return the object of type 'BODY'
            getByType('BODY','SPA') will only return the Spa
        """
        return list(
            filter(
                lambda object: object.objtype == type
                and (not subtype or object.subtype == subtype),
                self,
            )
        )

    def addObject(self, objnam, params):
        """Add a new object to the model based on its name and its initial values."""
        # because the controller may be started more than once
        # we don't override existing objects
        if not self._objects.get(objnam):
            object = PoolObject(objnam, self.filterOutAttributes(params))
            if self._filterFunc(object):
                self._objects[objnam] = object
            else:
                _LOGGER.debug(f"not adding object to model: {object}")

    # def buildTrackingQuery(self):
    #     query = []
    #     for object in self.objectList:
    #         attributes = object.attributes
    #         if attributes:
    #             query.append({"objnam": object.objnam, "keys": attributes})
    #     return query

    def processUpdates(self, updateList):
        """Update the state of the objects in the model."""
        updatedList = []
        for update in updateList:
            objnam = update["objnam"]
            object = self._objects.get(objnam)
            if object:
                if object.update(update["params"]):
                    updatedList.append(object)
        return updatedList

    @staticmethod
    def filterOutAttributes(params):
        """Filter out undefined attributes."""
        # Pentair returns value equals to the parameter when it
        # does not have a value for it. No point in keeping these
        return {k: v for k, v in params.items() if k != v}
