"""
Command-line Groupweave client
Used for testing game logic locally
"""

from abc import ABCMeta, abstractmethod

from twisted.protocols.basic import LineReceiver

from events import from_json


class CommandLineGroupweaveClientProtocol(LineReceiver, object):

    __metaclass__ = ABCMeta

    def __init__(self):
        self.story = ""
        self.name = None

    def lineReceived(self, line):
        event = from_json(line)
        self.handleEvent(event)

    def send(self, event):
        self.sendLine(event.toJson())

    @abstractmethod
    def handleEvent(self, event):
        pass
