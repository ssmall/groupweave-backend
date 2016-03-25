"""
Command line runner for the Groupweave backend,
to be used for local testing
"""
import sys

import time
from twisted.internet import reactor
from twisted.internet.endpoints import TCP4ServerEndpoint
from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineReceiver

from cli import SERVER_PORT
from events import Event, PlayerJoined
import game


class Host(game.Player):
    def __init__(self, num_players):
        self.total_players = num_players
        self.connected_players = 0
        self.game = None

    def name(self):
        return "Host"

    def notify(self, event):
        if isinstance(event, PlayerJoined):
            print "{} joined the game!".format(event["player_name"])
            self.connected_players += 1
            if self.connected_players == self.total_players:
                self.game.start()

    def join(self, game):
        self.game = game


class Player(game.Player):
    def __init__(self, name, protocol):
        self._protocol = protocol
        self._name = name

    @property
    def name(self):
        return self._name

    def notify(self, event):
        self._protocol.sendLine(event.toJson())

    def join(self, game):
        game.register(self)


class CommandLineGroupweaveBackend(LineReceiver):
    """
    Run a game of Groupweave from the command line
    as a TCP server
    """

    def __init__(self, game):
        self.game = game
        self.player = None

    def connectionMade(self):
        self.player = Player("Player {}".format(len(self.game.players)), self)
        self.player.notify(Event("YourNameIs", name=self.player.name))
        try:
            self.player.join(self.game)
        except RuntimeError:
            print >> sys.stderr, "Rejecting new connection because game has already started"
            self.transport.loseConnection()
            return

    def lineReceived(self, line):
        pass

    def connectionLost(self, reason):
        self.factory.removeClient(self)


class DummyIdFactory(object):
    def new_id(self):
        return "0001"


class CommandLineGroupweaveFactory(Factory):
    def __init__(self, num_players):
        self.host = Host(num_players)
        self.game = game.GameFactory(DummyIdFactory()).new_game(self.host)
        self.host.join(self.game)
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
        protocol = CommandLineGroupweaveBackend(self.game)
        self.clients.append(protocol)
        return protocol

    @property
    def numClients(self):
        return len(self.clients)

    def removeClient(self, client):
        self.clients.remove(client)

    def sendToPlayers(self, fromClient, event):
        for client in self.clients:
            if client is not fromClient:
                client.sendMessage(event.toJson())


if __name__ == "__main__":
    endpoint = TCP4ServerEndpoint(reactor, SERVER_PORT)
    endpoint.listen(CommandLineGroupweaveFactory(int(raw_input("How many players? "))))
    reactor.run()
