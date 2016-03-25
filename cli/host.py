import os

from twisted.internet import reactor
from twisted.internet.endpoints import TCP4ClientEndpoint, connectProtocol

from cli import SERVER_PORT
from cli.client import CommandLineGroupweaveClientProtocol
from events import PlayerJoined, StartGame, NewPrompts, ChoosePrompt


class Host(CommandLineGroupweaveClientProtocol):

    def __init__(self, total_players):
        super(Host, self).__init__()
        self.total_players = total_players
        self.num_players = 0

    def handleEvent(self, event):
        if isinstance(event, PlayerJoined):
            self.num_players += 1
            if self.num_players == self.total_players:
                print "Starting game!"
                self.send(StartGame())
        if isinstance(event, NewPrompts):
            choices = {(i+1): prompt for i, prompt in enumerate(event["prompts"])}
            print "Prompts received (choose one):"
            for i, prompt in choices.iteritems():
                print "{}. {}".format(i, prompt)
            choice = choices[int(raw_input("> "))]
            self.send(ChoosePrompt(choice))
            self.story = "{} {}".format(self.story, choice) if self.story else choice
            os.system('clear')
            print "The Story So Far:\n{}".format(self.story)



if __name__ == "__main__":
    point = TCP4ClientEndpoint(reactor, "localhost", SERVER_PORT)
    d = connectProtocol(point, Host(int(raw_input("How many players (not including you)? "))))
    reactor.run()