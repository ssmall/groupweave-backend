"""
Module for modeling a game of Groupweave
"""
from abc import ABCMeta, abstractmethod, abstractproperty

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

    def register(self, playerToAdd):
        """
        :return: a CreatedGame with an updated list of players

        :raises: RuntimeError if the player has already joined the game
        """
        if playerToAdd in self.players:
            raise RuntimeError("{} has already joined the game!".format(playerToAdd))
        self._players.append(playerToAdd)
        event = PlayerJoined(playerToAdd.name)
        for playerToNotify in self.players + (self.host,):
            if playerToNotify is playerToAdd:
                continue
            playerToNotify.notify(event)
        return self

    def start(self):
        """
        :return: a WaitForSubmissionsGame
        """
        for player in self.players:
            player.notify(GameStarted())
        return WaitForSubmissionsGame(self.host, self.id, self.players)

class WaitForSubmissionsGame(Game):
    """
    A game in the WAIT_FOR_SUBMISSIONS state
    """

    def __init__(self, host, game_id, players):
        super(WaitForSubmissionsGame, self).__init__(host, game_id, players)
        self._prompts = {}

    def receive_prompt(self, prompt):
        """
        :param prompt: a events.Prompt submitted by a player
        :return: this WaitForSubmissionsGame
        """
        player_name = prompt["player"]
        if player_name in self.prompts:
            raise RuntimeError("{} has already submitted a prompt this round!".format(player_name))
        self._prompts[player_name] = prompt["prompt"]

        if len(self.prompts) == len(self.players):
            self.host.notify(NewPrompts(prompts=self.prompts.values()))
            return ChoosingGame(self.host, self.id, self.players)
        return self

    @property
    def prompts(self):
        return dict(self._prompts)


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

    __metaclass__ = ABCMeta

    @abstractmethod
    def join(self, game):
        pass

    @abstractmethod
    def notify(self, event):
        """
        Notify the player of a game event.
        :param event: the game Event that has occurred
        :return: anything returned by this method will be ignored
        """
        pass

    @abstractproperty
    def name(self):
        pass