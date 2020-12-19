import asyncio
import logging
from queue import SimpleQueue
import json

_LOGGER = logging.getLogger(__name__)
#_LOGGER.setLevel(logging.DEBUG)

# ---------------------------------------------------------------------------
# the IntelliCenter protocol (ICProtocol for short) takes care of the following:
# - generating unique msg ids for outgoing requests
# - receiving data from the transport and combining it into a proper json object
# - managing a 'only-one-request-out-one-the-wire' policy
#   this is more a "works better that way" thand a real requirement as far as know
# - sending regular (every 10s) 'ping' requests and closing the connection if 'pong'
#   replies are not received fast enough (we allow 2 outstanding which is generous)
# ---------------------------------------------------------------------------

class ICProtocol(asyncio.Protocol):

    def __init__(self, controller):
        """ initialization of a protocol for a IntelliCenter system """

        self._controller = controller

        self._transport = None

        # counter used to generate messageIDs
        self._msgID = 1

        # buffer used to accumulate data received before spliting into lines
        self._lineBuffer = ''

        # state variable and queue for flow control
        # see sendRequest and responseReceived for details
        self._out_pending = 0
        self._out_queue = SimpleQueue()

        # the coroutine for sending regular 'ping' to IntelliCenter
        self._heartbeat = None
        # and the number of unacknowledgged ping issued
        self._num_unacked_pings = 0

    def connection_made(self, transport):
        """ asyncio callback for a successful connection. """

        self._transport = transport
        self._msgID = 1

        # start a task to send 'ping' every 30s
        self._heartbeat = asyncio.create_task(self.heartbeat())

        # and notify our controller that we are ready!
        self._controller.connection_made(self,transport)

    def connection_lost(self, exc):
        """ asyncio callback for connection lost. """

        if self._heartbeat:
            self._heartbeat.cancel()
            self._heartbeat = None

        self._controller.connection_lost(exc)

    def data_received(self, data) -> None:
        """ asyncio callback for receiving data """

        data = data.decode()
        _LOGGER.debug(f"PROTOCOL: received from transport: {data}")

        # "packets" from Pentair are organized by lines
        # so wait until at least a full line is received
        self._lineBuffer += data

        if not self._lineBuffer.endswith('\r\n'):
            return
        
        # there might have been more than one "packet" in our current buffer
        # so let's split them

        lines = str.split(self._lineBuffer, '\r\n')
        self._lineBuffer = ''

        for line in lines:
            if line:
                # and process each line individually
                self.processMessage(line)


    def sendCmd(self, cmd: str, extra: dict =None) -> str:
        """ sends the command and generate a unique msg id """
        msg_id = str(self._msgID)
        dict = {'messageID': msg_id, 'command': cmd}
        if extra:
            dict.update(extra)
        self._msgID = self._msgID + 1
        packet = json.dumps(dict)
        self.sendRequest(packet)

        return str(msg_id)

    def _writeToTransport(self, request):
        _LOGGER.debug(f"PROTOCOL: writing to transport: (size {len(request)}): {request}")
        self._transport.write(request.encode())
        self._transport.write('\r\n'.encode())      

    def sendRequest(self,request: str) -> None:
        """ either send the request to the wire or queue it for later """

        # IntelliCenter seems to struggle to parse requests coming too fast
        # so we throttle back to one request on the wire at a time
        # see responseReceived() for the other side of the flow control

        if self._out_pending == 0:
            # nothing is progress, we can transmit the packet
            self._writeToTransport(request)    
        else:
            # there is already something on the wire, let's queue the request
            self._out_queue.put(request)

        # and count the new request as pending
        self._out_pending += 1


    def responseReceived(self) -> None:
        """ other side of the flow control of requests """

        # we know that a response has been received
        # so, if we have a pending request in the queue
        # we can write it to our transport
        if not self._out_queue.empty():
            request = self._out_queue.get()
            self._writeToTransport(request)
        # no matter what, we have now one less request pending
        if self._out_pending:
            self._out_pending -= 1
       

    def processMessage(self, message: str) -> None:
        """ this handles a given message from IntelliCenter """

        _LOGGER.debug(f"PROTOCOL: processMessage {message}")

        # if message is 'pong', response for a previous 'ping'
        # do nothing except noting a response was received
        if (message == 'pong'):
            self.responseReceived()
            self._num_unacked_pings -= 1
            _LOGGER.debug("ping acknowledged")
            return

        # a number of issues could be happening in this code section
        # let's wrap the whole thing in a broad catch statement

        try:
            # the message is excepted to be a JSON object

            msg = json.loads(message)

            # with a minimum of a messageID and a command
            # NOTE: there seems to be a bug in IntelliCenter where
            # the message_id is different from the one matching the request
            # if an error occurred.. therefore the message_id is not really used

            msg_id = msg['messageID']
            command = msg['command']
            response = msg.get('response')

            # the response field is only present when the message is a response to
            # a request (as opposed to a 'notification')
            # if so, we also not that a response was received
            if response:
                self.responseReceived()
            
            # let's pass our message back to the controller for handling its semantic...
            self._controller.receivedMessage(msg_id, command, response, msg)

        except Exception as err:
            _LOGGER.error("PROTOCOL: exception while receiving message {err}")

    async def heartbeat(self):
        """ send a ping every 10s to keep and check that the connection is alive """

        while self._num_unacked_pings < 2:
            # we sleep first as there is no need for an immediate ping upon connection
            await asyncio.sleep(10)
            _LOGGER.debug("PROTOCOL: sending ping")
            self.sendRequest('ping')
            self._num_unacked_pings += 1

        # if we already have sent 2 pings without a pong
        # we assume the connection went dead and abort
        _LOGGER.error("PROTOCOL: heartbeat missed, closing connection")
        self._transport.close()
