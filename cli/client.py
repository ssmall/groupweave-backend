"""
Command-line Groupweave client
Used for testing game logic locally
"""
import os

import time
from twisted.internet import reactor
from twisted.internet.endpoints import TCP4ClientEndpoint, connectProtocol
from twisted.protocols.basic import LineReceiver

from cli import SERVER_PORT
from events import from_json, GameStarted, Prompt, PlayerJoined


class CommandLineGroupweaveProtocol(LineReceiver):
    def __init__(self):
        self.story = ""
        self.name = None

    def lineReceived(self, line):
        event = from_json(line)
        self.handleEvent(event)

    def send(self, event):
        self.sendLine(event.toJson())

    def handleEvent(self, event):
        if event.type == "YourNameIs":
            print "You are {}".format(event["name"])
            self.name = event["name"]
        elif isinstance(event, PlayerJoined):
            print "{} has joined the game!".format(event["player_name"])
        elif isinstance(event, GameStarted):
            print "The game is starting!"
            time.sleep(3)
            os.system('clear')
            self.submitPrompt()

    def submitPrompt(self):
        print "The story so far:\n\n{}\n\n".format(self.story)
        prompt = raw_input("Please type a sentence or phrase to continue the story:\n")
        self.sendLine(Prompt(prompt, self.name).toJson())


if __name__ == "__main__":
    point = TCP4ClientEndpoint(reactor, "localhost", SERVER_PORT)
    d = connectProtocol(point, CommandLineGroupweaveProtocol())
    reactor.run()
