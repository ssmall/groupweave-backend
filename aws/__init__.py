"""
Module for AWS-specific implementations of
game classes
"""

import game
from aws import dynamo, sqs
from aws.dynamo import GameIdGenerator
from game import GameFactory
from gameutil import GameReference


class BasePlayer(game.Player):
    def __init__(self, name, token):
        super(BasePlayer, self).__init__()
        self._name = name
        self.token = token
        self.queueUrl = None

    @property
    def name(self):
        return self._name

    def notify(self, event):
        sqs.send_message(self.queueUrl, event)

    def join(self, game):
        self.queueUrl = sqs.create_queue(game.id, self.token)


class Player(BasePlayer):
    def join(self, game):
        super(Player, self).join(game)
        game.register_player(self)


class Host(BasePlayer):
    """
    The host of a game
    """


class GameWrapperFactory(object):
    @staticmethod
    def new_game(host):
        game = GameFactory(GameIdGenerator()).new_game(host)
        dynamo.create_game(game)
        return GameWrapper(game)

    @staticmethod
    def load_game(game_id):
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
            pass  # Don't save the game state if an exception occurred
        self.save()
