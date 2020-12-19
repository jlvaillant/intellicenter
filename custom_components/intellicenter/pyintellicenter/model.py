import logging
from typing import Any, Callable, Dict, List, Optional

_LOGGER = logging.getLogger(__name__)

# ---------------------------------------------------------------------------

ALL_KNOWN_ATTRIBUTES = [
    'OBJTYP', 'SUBTYP', 'STATUS', 'SNAME', 'HITMP', 'MANHT', 'LOCY', 'LOTMP',
    'AVAIL', 'HEATING', 'OFFSET', 'STOP', 'SSET', 'ZIP', 'STATE', 'VER', 'VACTIM',
    'TEMPNC', 'CITY', 'SERVICE', 'ADDRESS', 'PROPNAME', 'PHONE', 'EMAIL2', 'DAY', 'VALVE',
    'HTMODE', 'MODE', 'COUNTRY', 'TIMZON', 'NAME', 'VOL', 'DLSTIM', 'SELECT',
    'LOCX', 'HTSRC', 'PHONE2', 'LSTTMP', 'SRIS', 'HEATER', 'START', 'MIN', 'VACFLO',
    'EMAIL', 'CLK24A', 'PROBE', 'SPEED', 'PWR', 'GPM', 'RPM', 'BOOST', 'USE', 'ACT', 'FEATR',
    'DAY', 'SINGLE', 'TIME', 'TIMOUT', 'CIRCUIT', 'PASSWRD', 'SHOMNU', 'LIMIT', 'LISTORD',
    'MANUAL', 'PARENT', 'CHILD', 'DNTSTP', 'RLY', 'SYNC', 'SET', 'SWIM', 'USAGE', 'BODY'
]

class PoolObject:

    def __init__(self, objnam, params):
        self._objnam = objnam
        self._objtyp = params.pop('OBJTYP')
        self._subtyp = params.pop('SUBTYP',None)
        self._properties = params

    @property
    def objnam(self):
        return self._objnam
        
    @property
    def sname(self):
        return self._properties.get('SNAME')

    @property
    def objtype(self):
        return self._objtyp

    @property
    def subtype(self):
        return self._subtyp

    @property
    def status(self):
        return self._properties.get('STATUS')

    @property
    def offStatus(self):
        return '4' if self.objtype == 'PUMP' else 'OFF'

    @property
    def onStatus(self):
        return '10' if self.objtype == 'PUMP' else 'ON'

    @property
    def isALight(self):
        return (self.objtype == 'CIRCUIT' and 
                self.subtype in ['LITSHO', 'LIGHT', 'INTELLI', 'GLOW', 'GLOWT', 'DIMMER'])
    
    @property
    def isFeatured(self):
        return self['FEATR'] == 'ON'

    def __getitem__(self, key):
        return self._properties.get(key)

    def __str__(self):
        str = f'{self.objnam} '
        str += f"({self.objtype}/{self.subtype}):" if self.subtype else f"({self.objtype}):"
        for (key,value) in self._properties.items():
            str += f" {key}: {value}"
        return str

    @property
    def attributes(self):
        return list(self._properties.keys())

    def update(self, updates):
        """ update the object from a set of key/value pairs, return true is the object HAS changed"""

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
    def __init__(self, filterFunc = lambda object: True):
        self._objects = {}
        self._system = None
        self._filterFunc = filterFunc

    @property
    def objectList(self):
        return self._objects.values()

    @property
    def numObjects(self):
        return len(self._objects)

    def __iter__(self):
        return iter(self._objects.values())

    def __getitem__(self, key):
        return self._objects.get(key)

    def getByType(self, type: str, subtype: str = None) -> List[PoolObject]:
        """ 
        returns all the object which match the type and the optional subtype 
        examples:
            getByType('BODY') will return the object of type 'BODY'
            getByType('BODY','SPA') will only return the Spa
        """
        return list(filter(lambda object: object.objtype == type
                           and (not subtype or object.subtype == subtype), self))


    def addObject(self, objnam, params):
        # because the controller may be started more than once
        # we don't override existing objects
        if not self._objects.get(objnam):
            object = PoolObject(objnam, self.pruneParams(params))
            if self._filterFunc(object):
                self._objects[objnam] = object
            else:
                _LOGGER.debug(f"not adding object to model: {object}")

    def buildTrackingQuery(self):
        query = []
        for object in self.objectList:
            attributes = object.attributes
            if (attributes):
                query.append(
                    {'objnam': object.objnam, 'keys': attributes})
        return query

    def processUpdates(self, updateList):
        updatedList = []
        for update in updateList:
            objnam = update['objnam']
            object = self._objects.get(objnam)
            if (object):
                if object.update(update['params']):
                    updatedList.append(object)
        return updatedList

    @staticmethod
    def pruneParams(params):
        return dict((k,v) for k,v in params.items() if k != v)

