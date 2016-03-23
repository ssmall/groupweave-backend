"""
Module for modeling a game of Groupweave
"""
from enum import Enum

from events import *

GameStates = Enum('CREATED', 'WAIT_FOR_SUBMISSIONS', 'CHOOSING', 'GAME_COMPLETE')

class GameFactory(object):
    """
    Factory for creating a new game
    """

    def __init__(self, id_generator):
        self.id_generator = id_generator

    def new_game(self, host):
        """
        :return: a new CreatedGame
        """
        return CreatedGame(host, self.id_generator.new_id(), [])


class Game(object):
    """
    Base class for a single game of Groupweave.

    Every (non-property) method of a Game should do
    at least one of two things:

        * trigger an event notification
        * trigger a game state transition

    As such, every such method must return a Game as
    a result, representing the state of the Game after
    calling the method.
    """

    def __init__(self, host, game_id, players):
        self._players = players
        self._host = host
        self._id = game_id

    @property
    def host(self):
        return self._host

    @property
    def id(self):
        return self._id

    @property
    def players(self):
        return tuple(self._players)


class CreatedGame(Game):
    """
    A game in the CREATED state
    """

    def register(self, player):
        """
        :return: a CreatedGame with an updated list of players

        :raises: RuntimeError if the player has already joined the game
        """
        if player in self.players:
            raise RuntimeError("{} has already joined the game!".format(player))
        self._players.append(player)
        self.host.notify(PlayerJoined(player.name))
        return self

    def start(self):
        """
        :return: a WaitForSubmissionsGame
        """
        for player in self.players:
            player.notify(GameStarted(len(self.players) + 1))
        return WaitForSubmissionsGame(self.host, self.id, self.players)

class WaitForSubmissionsGame(Game):
    """
    A game in the WAIT_FOR_SUBMISSIONS state
    """

class ChoosingGame(Game):
    """
    A game in the CHOOSING state
    """

class CompleteGame(Game):
    """
    A game in the COMPLETE state
    """


class Player(object):
    """
    A single player in a game of Groupweave
    """

    def join(self, game):
        pass

    def notify(self, event):
        pass

    @property
    def name(self):
        pass