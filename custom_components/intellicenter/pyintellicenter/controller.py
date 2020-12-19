from .protocol import ICProtocol
from .model import ALL_KNOWN_ATTRIBUTES

import logging
import traceback
import asyncio
from asyncio import Future
from hashlib import blake2b

from typing import Any, Callable, Dict, List, Optional

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.INFO)

class CommandError(Exception):
    def __init__(self, errorCode):
        self._errorCode = errorCode
    
    @property
    def errorCode(self):
        return self._errorCode

# -------------------------------------------------------------------------------------

class SystemInfo:
    def __init__(self, params):
        self._propName = params['PROPNAME']
        self._sw_version = params['VER']
        
        h = blake2b(digest_size=8)
        h.update(params['SNAME'].encode())
        self._unique_id = h.hexdigest()

    @property
    def propName(self):
        return self._propName

    @property
    def swVersion(self):
        return self._sw_version

    @property
    def uniqueID(self):
        return self._unique_id

# -------------------------------------------------------------------------------------

def prune(obj):
    if type(obj) is list:
        return [ prune(item) for item in obj ]
    elif type(obj) is dict:
        result = {}
        for (key,value) in obj.items():
            if key != value:
                result[key] = prune(value)
        return result
    return obj
    
class BaseController:
    def __init__(self, host, port=6681, loop=None):
        self._host = host
        self._port = port
        self._loop = loop

        self._transport = None
        self._protocol = None

        self._diconnectedCallback = None

        self._requests = {}

    @property
    def host(self):
        return self._host

    def connection_made(self,protocol,transport):
        _LOGGER.debug(f"Connection established to {self._host}")

    def connection_lost(self, exc):
        self.stop() # should that be a cleanup instead?
        if self._diconnectedCallback:
            self._diconnectedCallback(self, exc)

    async def start(self) -> None:
        self._transport, self._protocol = await self._loop.create_connection(
            lambda: ICProtocol(self),
            self._host, self._port)

        # we start by requesting a few attributes from the SYSTEM object
        # and therefore validate that the system connected is indeed a IntelliCenter
        msg = await self.sendCmd('GetParamList', {'condition': 'OBJTYP=SYSTEM',
            'objectList': [{'objnam': 'INCR', 'keys': ['SNAME', 'VER', 'PROPNAME']}]})

        self._systemInfo = SystemInfo(msg['objectList'][0]['params'])

    def stop(self):
        if self._transport:
            for request in self._requests.values():
                request.cancel()
            self._transport.close()
            self._transport = None
            self._protocol = None

    def sendCmd(self, cmd, extra=None, waitForResponse = True) -> Optional[Future]:
        """
            sends a command with optional extra parameters to the system
            if waitForResponse is True, a Future is created and returned
            so either call resp = await controller.sendCmd(cmd,extra)
            or controller.sendCmd(cmd,extra,waitForResponse=False)
        """

        _LOGGER.debug(f"CONTROLLER: sendCmd: {cmd} {extra} {waitForResponse}")
        future = Future() if waitForResponse else None

        if self._protocol:
            msg_id = self._protocol.sendCmd(cmd, extra)
            self._requests[msg_id] = future
        elif future:
            future.setException(Exception("controller disconnected"))

        return future

    def requestChanges(self, objnam: str, changes: dict, waitForResponse = True) -> Future:
        """ submits a change for a given object.  """
        return self.sendCmd("SETPARAMLIST",{"objectList":[{"objnam":objnam,"params":changes}]}, waitForResponse = waitForResponse)

    async def getAllObjects(self, attributeList: list = ALL_KNOWN_ATTRIBUTES):
        result = await self.sendCmd('GetParamList', {
            'condition': '',
            'objectList': [{'objnam': 'INCR', 'keys': attributeList}]
        })
        return prune(result['objectList'])

    async def getQuery(self, queryName: str, arguments : str = ''):
        result = await self.sendCmd('GetQuery', {'queryName':queryName,"arguments":arguments})
        return result['answer']

    def getCircuitNames(self):
        return self.getQuery('GetCircuitNames')

    async def getCircuitTypes(self):
        """ returns a dictionnary: key: circuit's SUBTYP , value: 'friendly' readable string """

        return { v['systemValue']: v['readableValue'] for v in await self.getQuery('GetCircuitTypes')}

    def getHardwareDefinition(self):
        return prune(self.getQuery('GetHardwareDefinition'))

    def getConfiguration(self):
        return self.getQuery('GetConfiguration')

    def receivedMessage(self, msg_id: str, command: str, response: str, msg: dict):
        """
            callback for a incoming message
            msd_id is the id of the incoming message
            response is the success (200) or error code or None (if this was a notification)
            msg is the while message as a dictionnary (parsing of the JSON object)
        """

        future = self._requests.pop(msg_id,0)

        # here future can be either:
        #  - 0 if there was no corresponding request matching this response
        #      like in the case of a notification
        #  - a future is the sender of the request wanted to get the results
        #  - None is the sender declined to wait for the response (in sendCmd)

        _LOGGER.debug(f"CONTROLLER: receivedMessage: {msg_id} {command} {response} {future}")
        
        if not future == 0:
            if future:
                if response == '200':
                    future.set_result(msg)
                else:
                    future.set_exception(CommandError(response))
            else:
                _LOGGER.debug(f"ignoring response for msg_id {msg_id}")
        elif response is None or response == '200':
            self.processMessage(command,msg)
        else:
            _LOGGER.warning(f"CONTROLLER: error {response} : {msg}")

    def processMessage(self, command: str, msg):
        """ place holder for handling notifications """
        pass

    @property
    def systemInfo(self):
        return self._systemInfo

# -------------------------------------------------------------------------------------

class ModelController(BaseController):
    def __init__(self, host, model, port=6681, loop=None,
                 connectionTimeout=10):
        super().__init__(host,port,loop)
        self._model = model
        self._connectionTimeout = connectionTimeout

        self._systemInitialized = False

        self._updatedCallback = None


    @property
    def model(self):
        return self._model

    def connection_made(self,protocol,transport):
        _LOGGER.info(f"Connection establishef to {self._host}")



    async def start(self):

        await super().start()

        # with the connection now established we first retrieve all the objects
        allObjects = await self.getAllObjects()

        _LOGGER.debug(f"objects received: {allObjects}")

        # and process that list into our model
        self.receivedSystemConfig(allObjects)

        _LOGGER.info(f"model now contains {self.model.numObjects} objects")

        try:
            # now that I have my object loaded in the model
            # build a query to monitors all their relevant attibutes

            query = []
            for object in self.model:
                attributes = object.attributes
                if (attributes):
                    query.append(
                        {'objnam': object.objnam, 'keys': attributes})
                # a query too large can choke the protocol...
                # we split them in maximum of 30 objects (arbitrary but seems to work)
                if len(query) >= 30:
                    msg = await self.sendCmd('RequestParamList', {"objectList": query})
                    self.receivedNotifyList(msg['objectList'])
                    query = []

            # and issue the remaining elements if any
            if (query):
                msg = await self.sendCmd('RequestParamList', {"objectList": query})
                self.receivedNotifyList(msg['objectList'])

        except Exception as err:
            traceback.print_exc()


    def receivedQueryResult(self, queryName: str, answer):
        """ handler for all the 'getQuery' responses """

        # none are used by default
        # see Pentair protocol documentation for details
        # GetHardwareDefinition, GetConfiguration

        pass

    def receivedNotifyList(self, changes):
        """ handle the notifications from IntelliCenter when tracked objects are modified """

        try:
            # apply the changes back to the model

            updatedList = self._model.processUpdates(changes)

            _LOGGER.debug(f"CONTROLLER: received NotifyList: {len(updatedList)} objects updated")

            if self._updatedCallback:
                    self._updatedCallback(self, updatedList)

        except Exception as err:
            _LOGGER.error("CONTROLLER: receivedNotifyList {err}")

    def receivedWriteParamList(self, changes):
        """ handler for response to a requested change to an object """

        # similar to the receivedNotifyList except
        try:
            # print(f"receivedWriteParamList {len(changes)} for {self._model.numObjects} objects")
            updatedList = self._model.processUpdates(changes)
            if self._updatedCallback:
                self._updatedCallback(self, updatedList)
        except Exception as err:
            _LOGGER.error("CONTROLLER: receivedWriteParamList {err}")

    def receivedSystemConfig(self,objectList):
        """ triggered by the response for the initial request for all objects """
        
        _LOGGER.debug(f"CONTROLLER: received SystemConfig for {len(objectList)} object(s)")

        for object in prune(objectList):
            try:
                self.model.addObject(object['objnam'], object['params'])
            except Exception as err:
                _LOGGER.error(f"problem creating object from {object}")
                # traceback.print_exc()


    def processMessage(self, command: str, msg):
        """asyncio callback for a incoming message."""

        _LOGGER.debug(f"CONTROLLER: received {command} response: {msg}")

        try:
            if (command == 'SendQuery'):
                self.receivedQueryResult(msg['queryName'], msg['answer'])
            elif (command == 'NotifyList'):
                self.receivedNotifyList(msg['objectList'])
            elif (command == 'WriteParamList'):
                self.receivedWriteParamList(msg['objectList'][0]['changes'])
            elif (command == 'SendParamList'):
                self.receivedSystemConfig(msg['objectList'])
            else:
                print(f"ignoring {command}")
        except Exception as err:
            _LOGGER.error(f"error {err} while processing {msg}")
            # traceback.print_exc()

# -------------------------------------------------------------------------------------

class ConnectionHandler:
    def __init__(self,controller, timeBetweenReconnects = 30):
        self._controller = controller

        self._starterTask = None
        self._stopped = False
        self._firstTime = True

        self._timeBetweenReconnects = timeBetweenReconnects

        controller._diconnectedCallback = self._diconnectedCallback

        if hasattr(controller,'_updatedCallback'):
            controller._updatedCallback = self.updated

    @property
    def controller(self):
        return self._controller

    async def start(self):
        if not self._starterTask:
            self._starterTask = asyncio.create_task(self._starter())
    
    def _next_delay(self, currentDelay: int) -> int:
        """
            used to compute the delay before the next reconnection attempt
            default is exponential backoff with a 1.5 factor
        """
        return int(currentDelay * 1.5)

    async def _starter(self,initialDelay = 0):

        started = False
        delay = self._timeBetweenReconnects
        while not started:
            try:
                if initialDelay:
                    self.retrying(delay)
                    await asyncio.sleep(initialDelay)
                _LOGGER.debug(f"trying to start controller")

                await self._controller.start()


                if self._firstTime:
                    self.started(self._controller)
                    self._firstTime = False
                else:
                    self.reconnected(self._controller)

                started = True
                self._starterTask = None
            except Exception as err:
                _LOGGER.error(f"cannot start: {err}")
                self.retrying(delay)
                await asyncio.sleep(delay)
                delay = self._next_delay(delay)

    def stop(self):
        _LOGGER.debug(f"terminating connection to {self._controller.host}")
        self._stopped = True
        if self._starterTask:
            self._starterTask.cancel()
            self._starterTask = None
        self._controller.stop()

    def _diconnectedCallback(self, controller, err):
        self.disconnected(controller,err)
        if not self._stopped:
            _LOGGER.error(f"system disconnected  from {self._controller.host} {err if err else ''}")
            self._starterTask = asyncio.create_task(self._starter(self._timeBetweenReconnects))
 
    def started(self, controller):
        """
            invoked only the first time the controller is started
            further reconnections will trigger reconnected method instead
        """
        pass

    def retrying(self, delay):
        """ just a friendly way to indicate we will retry connection in {delay} seconds """
        _LOGGER.info(f"will attempt to reconnect in {delay}s")

    def updated(self, controller, changes):
        """
            invoked when our system has been modified
            only invoked if the controller has a _updatedCallback attribute
            changes is expected to contain the list of modified objects
        """
        pass

    def disconnected(self,controller,exc):
        """
            invoked when the controller as been disconnected
            exc will contain the underlying exception except if
            the hearbeat has been missed, in this case exc is None
        """
        pass

    def reconnected(self, controller):
        """
            invoked when the controller as been reconnected
            only occurs if the controller was connected before
        """
        pass
