"""
Command line runner for the Groupweave backend,
to be used for local testing
"""
import sys

from twisted.internet import reactor
from twisted.internet.endpoints import TCP4ServerEndpoint
from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineReceiver

import game
from cli import SERVER_PORT
from events import Event, Prompt, from_json, StartGame, ChoosePrompt
from gameutil import GameReference


class CommandLineGroupweaveBackend(LineReceiver):
    """
    Run a game of Groupweave from the command line
    as a TCP server
    """

    def __init__(self, factory, game):
        self.game = game
        self.factory = factory
        self.player = None

    def attachPlayer(self, player):
        self.player = player

    def connectionMade(self):
        self.player.notify(Event("YourNameIs", name=self.player.name))
        try:
            self.player.join(self.game)
        except RuntimeError:
            print >> sys.stderr, "Rejecting new connection because game has already started"
            self.transport.loseConnection()
            return

    def dataReceived(self, data):
        print "[raw data] {}".format(data)
        LineReceiver.dataReceived(self, data)

    def lineReceived(self, line):
        event = from_json(line)
        self.factory.handleEvent(event)

    def connectionLost(self, reason):
        self.factory.removeClient(self)


class Player(game.Player):
    def __init__(self, name, protocol):
        self._name = name
        self._protocol = protocol

    @property
    def name(self):
        return self._name

    def notify(self, event):
        self._protocol.sendLine(event.toJson())

    def join(self, game):
        game.register(self)


class Host(Player):
    def join(self, game):
        pass


class DummyIdFactory(object):
    def new_id(self):
        return "0001"


class CommandLineGroupweaveFactory(Factory):
    def __init__(self):
        self.game = None
        self.clients = []

    def startFactory(self):
        print "Starting up Groupweave server"
        Factory.startFactory(self)

    def stopFactory(self):
        print "Stopping Groupweave server"
        for client in self.clients:
            client.sendMessage("Server is shutting down!")
            client.transport.loseConnection()
        Factory.stopFactory(self)

    def buildProtocol(self, addr):
        protocol = CommandLineGroupweaveBackend(self, self.game)
        if self.numClients == 0:
            print "Host connected!"
            host = Host("Host", protocol)
            protocol.attachPlayer(host)
            self.game = GameReference(game.GameFactory(DummyIdFactory()).new_game(host))
        else:
            print "Player connected!"
            player_name = "Player {}".format(len(self.game.players))
            player = Player(player_name, protocol)
            protocol.attachPlayer(player)
        self.clients.append(protocol)
        return protocol

    def handleEvent(self, event):
        if isinstance(event, StartGame):
            self.game.start()
        elif isinstance(event, Prompt):
            self.game.receive_prompt(event)
        elif isinstance(event, ChoosePrompt):
            self.game.choose_prompt(event)
        else:
            print "Unhandled event received: {}".format(event)

    @property
    def numClients(self):
        return len(self.clients)

    def removeClient(self, client):
        self.clients.remove(client)


if __name__ == "__main__":
    endpoint = TCP4ServerEndpoint(reactor, SERVER_PORT)
    endpoint.listen(CommandLineGroupweaveFactory())
    reactor.run()
