import os
import time
from twisted.internet import reactor
from twisted.internet.endpoints import TCP4ClientEndpoint, connectProtocol

from cli import SERVER_PORT
from cli.client import CommandLineGroupweaveClientProtocol
from events import PlayerJoined, GameStarted, Prompt, StoryUpdate, Done


class Player(CommandLineGroupweaveClientProtocol):
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
        elif isinstance(event, StoryUpdate):
            self.story = event["story"]
            os.system('clear')
            print "The host has chosen!"
            if event["is_final_round"]:
                print "This is the final round! Make it count!"
            self.submitPrompt()
        elif isinstance(event, Done):
            self.story = event["story"]
            os.system('clear')
            print "That's all, folks! The winner is: {}".format(event["winner"])
            print "The final story is:\n{}".format(self.story)
            self.transport.loseConnection()
            reactor.stop()

    def submitPrompt(self):
        print "The story so far:\n\n{}\n\n".format(self.story)
        prompt = raw_input("Please type a sentence or phrase to continue the story:\n")
        self.send(Prompt(prompt, self.name))
        print "Prompt submitted! Please wait while other players submit theirs"


if __name__ == "__main__":
    point = TCP4ClientEndpoint(reactor, "localhost", SERVER_PORT)
    d = connectProtocol(point, Player())
    reactor.run()
