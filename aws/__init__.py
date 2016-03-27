"""
Module for AWS-specific implementations of
game classes
"""

import game
from aws import dynamo, sqs
from aws.dynamo import GameIdGenerator
from game import CreatedGame, GameFactory
from gameutil import GameReference


class BasePlayer(game.Player):

    def __init__(self, name, token):
        super(BasePlayer, self).__init__()
        self._name = name
        self.token = token

    @property
    def name(self):
        return self._name

class Player(BasePlayer):
    def notify(self, event):
        pass

    def join(self, game):
        game.register(self)


class Host(BasePlayer):

    def __init__(self, name, token):
        super(Host, self).__init__(name, token)
        self.queueUrl = None

    def notify(self, event):
        sqs.send_message(self.queueUrl, event)

    def join(self, game):
        self.queueUrl = sqs.create_queue(game.id, self.token)


class GameWrapperFactory(object):
    def new_game(self, host):
        game = GameFactory(GameIdGenerator()).new_game(host)
        dynamo.create_game(game)
        return GameWrapper(game)

    def load_game(self, game_id):
        game = dynamo.load_game(game_id)
        return GameWrapper(game)


class GameWrapper(object):
    """
    Wrapper for a game that supports loading and saving
    game state from DynamoDB
    """

    def __init__(self, game):
        self.game = GameReference(game)

    def save(self):
        dynamo.save_game(self.game.game)


    def __enter__(self):
        return self.game

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            pass # Don't save the game state if an exception occurred
        self.save()

