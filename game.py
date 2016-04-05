"""
Module for modeling a game of Groupweave
"""
from abc import ABCMeta, abstractmethod, abstractproperty

from events import *

TOTAL_ROUNDS = 10


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

    def __init__(self, host, game_id, players, story="", current_round=1, spectators=[]):
        self._current_round = current_round
        self._players = players
        self._host = host
        self._id = game_id
        self._story = story
        self._spectators = spectators

    @property
    def host(self):
        return self._host

    @property
    def id(self):
        return self._id

    @property
    def players(self):
        return tuple(self._players)

    @property
    def spectators(self):
        return tuple(self._spectators)

    @property
    def story(self):
        return self._story

    @property
    def round_number(self):
        return self._current_round

    def notify_players(self, notification):
        for player in self.players:
            player.notify(notification)

    def notify_spectators(self, notification):
        for spectator in self._spectators:
            spectator.notify(notification)


class CreatedGame(Game):
    """
    A game in the CREATED state
    """

    def register_player(self, player_to_add):
        """
        :return: a CreatedGame with an updated list of players

        :raises: RuntimeError if the player has already joined the game
        """
        if player_to_add in self.players + self.spectators:
            raise RuntimeError("{} has already joined the game!".format(player_to_add))
        self._players.append(player_to_add)
        event = PlayerJoined(player_to_add.name)
        for playerToNotify in self.players + (self.host,):
            if playerToNotify is player_to_add:
                continue
            playerToNotify.notify(event)
        return self

    def register_spectator(self, spectator_to_add):
        """
        :return: a CreatedGame with an updated list of spectators

        :raises: RuntimeError if the spectator has already joined the game
        """
        if spectator_to_add in self.spectators + self.players:
            raise RuntimeError("{} has already joined the game!".format(spectator_to_add))
        self._spectators.append(spectator_to_add)
        return self

    def start(self):
        """
        :return: a WaitForSubmissionsGame
        """
        game_started = GameStarted()
        self.notify_players(game_started)
        self.notify_spectators(game_started)
        return WaitForSubmissionsGame(self.host, self.id, self.players, "", 1, self.spectators)


class WaitForSubmissionsGame(Game):
    """
    A game in the WAIT_FOR_SUBMISSIONS state
    """

    def __init__(self, host, game_id, players, story, current_round, spectators):
        super(WaitForSubmissionsGame, self).__init__(host, game_id, players, story, current_round, spectators)
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
            prompts_event = NewPrompts(prompts=self.prompts.values())
            self.host.notify(prompts_event)
            self.notify_spectators(prompts_event)
            return ChoosingGame(self.host, self.id, self.players, self.story, self.round_number)
        return self

    @property
    def prompts(self):
        return dict(self._prompts)


class ChoosingGame(Game):
    """
    A game in the CHOOSING state
    """

    def choose_prompt(self, choice):
        updated_story = "{} {}".format(self.story, choice['choice'])

        if self.round_number == TOTAL_ROUNDS:
            doneEvent = Done(winner="Everybody!", story=updated_story)
            self.notify_players(doneEvent)
            self.notify_spectators(doneEvent)
            self.host.notify(doneEvent)
            return CompleteGame(self.host, self.id, self.players, updated_story, TOTAL_ROUNDS)
        else:
            is_final_round = self.round_number == (TOTAL_ROUNDS - 1)
            notification = StoryUpdate(updated_story, is_final_round=is_final_round)
            self.notify_players(notification)
            self.notify_spectators(notification)
            return WaitForSubmissionsGame(self.host, self.id,
                                          self.players, updated_story,
                                          self.round_number + 1, self.spectators)


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
