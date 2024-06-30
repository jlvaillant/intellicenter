"""Protocol for communicating with a Pentair system."""

import asyncio
import time
import json
import logging
from queue import SimpleQueue

_LOGGER = logging.getLogger(__name__)
# _LOGGER.setLevel(logging.DEBUG)

# ---------------------------------------------------------------------------


class ICProtocol(asyncio.Protocol):
    """The ICProtocol handles the low level protocol with a Pentair system.

    In particular, it takes care of the following:
    - generating unique msg ids for outgoing requests
    - receiving data from the transport and combining it into a proper json object
    - managing a 'only-one-request-out-one-the-wire' policy
    this is more a "works better that way" thand a real requirement as far as know
    """

    def __init__(self, controller):
        """Initialize a protocol for a IntelliCenter system."""

        self._controller = controller

        self._transport = None

        # counter used to generate messageIDs
        self._msgID = 1

        # buffer used to accumulate data received before splitting into lines
        self._lineBuffer = ""

        # state variable and queue for flow control
        # see sendRequest and responseReceived for details
        self._out_pending = 0
        self._out_queue = SimpleQueue()

    def connection_made(self, transport):
        """Handle the callback for a successful connection."""

        self._transport = transport
        self._msgID = 1

        # and notify our controller that we are ready!
        self._controller.connection_made(self, transport)

    def connection_lost(self, exc):
        """Handle the callback for connection lost."""

        self._controller.connection_lost(exc)

    def data_received(self, data) -> None:
        """Handle the callback for data received."""

        data = data.decode()
        _LOGGER.debug(f"PROTOCOL: received from transport: {data}")

        # "packets" from Pentair are organized by lines
        # so wait until at least a full line is received
        self._lineBuffer += data

        if not self._lineBuffer.endswith("\r\n"):
            return

        # there might have been more than one "packet" in our current buffer
        # so let's split them

        lines = str.split(self._lineBuffer, "\r\n")
        self._lineBuffer = ""

        for line in lines:
            if line:
                # and process each line individually
                self.processMessage(line)

    def sendCmd(self, cmd: str, extra: dict = None) -> str:
        """Send a command and return a generated msg id."""
        msg_id = str(self._msgID)
        dict = {"messageID": msg_id, "command": cmd}
        if extra:
            dict.update(extra)
        self._msgID = self._msgID + 1
        packet = json.dumps(dict)
        self.sendRequest(packet)

        return str(msg_id)

    def _writeToTransport(self, request):
        _LOGGER.debug(
            f"PROTOCOL: writing to transport: (size {len(request)}): {request}"
        )
        self._transport.write(request.encode())

    def sendRequest(self, request: str) -> None:
        """Either send the request to the wire or queue it for later."""

        # IntelliCenter seems to struggle to parse requests coming too fast
        # so we throttle back to one request on the wire at a time
        # see responseReceived() for the other side of the flow control

        if self._out_pending == 0:
            # nothing is progress, we can transmit the packet
            # and count the new request as pending
            self._out_pending += 1
            self._writeToTransport(request) # !!! We can get a responseReceived here, which will not see the incremented _out_pending, and do the wrong thing!
        else:
            # there is already something on the wire, let's queue the request
            first_pending = self._out_pending == 1
            # and count the new request as pending
            self._out_pending += 1
            self._out_queue.put(request)
            _LOGGER.error(f"PROTOCOL: queuing request {request}; {self._out_pending} messages pending")
            if first_pending:
                self._out_pending_since = time.time()
                self._out_pending_first = request
            elif time.time() - self._out_pending_since > 60:
                # we have been waiting for a minute for the last response
                # we assume the connection went bad and abort
                # unfortunately, some messages will have been lost
                _LOGGER.error(f"PROTOCOL: waited for response for {self._out_pending_first} for one minute, closing connection; {self._out_pending + 1} messages lost")
                self._lineBuffer = ""
                self._out_pending = 0
                self._out_queue = SimpleQueue()
                self._transport.close()
                return

    def responseReceived(self) -> None:
        """Handle the flow control part of a received rsponse."""

        # we know that a response has been received
        # so, if we have a pending request in the queue
        # we can write it to our transport

        if not self._out_queue.empty():
            request = self._out_queue.get()
            _LOGGER.error(f"PROTOCOL: dequeuing request {request}; {self._out_pending - 1} messages pending")
            self._writeToTransport(request)
        # no matter what, we have now one less request pending
        if self._out_pending:
            self._out_pending -= 1

    def processMessage(self, message: str) -> None:
        """Process a given message from IntelliCenter."""

        _LOGGER.debug(f"PROTOCOL: processMessage {message}")

        # a number of issues could be happening in this code section
        # let's wrap the whole thing in a broad catch statement

        try:
            # the message is excepted to be a JSON object

            msg = json.loads(message)

            # with a minimum of a messageID and a command
            # NOTE: there seems to be a bug in IntelliCenter where
            # the message_id is different from the one matching the request
            # if an error occurred.. therefore the message_id is not really used

            msg_id = msg["messageID"]
            command = msg["command"]
            response = msg.get("response")

            # the response field is only present when the message is a response to
            # a request (as opposed to a 'notification')
            # if so, we also not that a response was received
            if response:
                self.responseReceived()

            # let's pass our message back to the controller for handling its semantic...
            self._controller.receivedMessage(msg_id, command, response, msg)

        except Exception as err:
            _LOGGER.error(f"PROTOCOL: exception while receiving message {err}")
