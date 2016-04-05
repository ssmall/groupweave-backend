"""
Module for modeling a game of Groupweave
"""
from abc import ABCMeta, abstractmethod, abstractproperty

from events import *

TOTAL_ROUNDS = 10


class NotificationManager(object):
    """
    Handles PubSub style of notification for events
    """

    def __init__(self):
        super(NotificationManager, self).__init__()
        self._registry = {}

    def subscribe(self, player, *event_types):
        """
        Subscribe the given player to the given type of event
        :param player: the Player to subscribe
        :param event_types: one or more events.Event types to which this player subscribes
        """
        for event_type in event_types:
            if event_type in self._registry.keys():
                self._registry[event_type].append(player)
            else:
                self._registry[event_type] = [player]

    def publish(self, event):
        """
        Publish an event, notify all players who are subscribed to that event type
        :param event: the events.Event instance to publish
        """
        for player in self._registry[type(event)]:
            player.notify(event)


class GameFactory(object):
    """
    Factory for creating a new game
    """

    def __init__(self, id_generator, notification_manager=NotificationManager()):
        self.id_generator = id_generator
        self.notification_manager = notification_manager

    def new_game(self, host):
        """
        :return: a new CreatedGame
        """
        self.notification_manager.subscribe(host, PlayerJoined, NewPrompts, Done)
        return CreatedGame(host, self.id_generator.new_id(), self.notification_manager)


def copy_value(override_value, copy_from, attr_name):
    """
    Copy the value of the named attribute from 'copy_from' iff 'override_value' is None
    """
    if override_value is not None:
        return override_value
    if copy_from is None:
        raise ValueError("Could not copy attribute {} from {}".format(attr_name, copy_from))
    val = getattr(copy_from, attr_name, None)
    if val is None:
        raise ValueError("Could not get a value for {}".format(attr_name))
    return val


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

    def __init__(self, host=None, game_id=None, players=None, story=None,
                 current_round=None, spectators=None, notification_manager=None,
                 copy_from=None):
        self._current_round = copy_value(current_round, copy_from, "_current_round")
        self._players = copy_value(players, copy_from, "_players")
        self._host = copy_value(host, copy_from, "_host")
        self._id = copy_value(game_id, copy_from, "_id")
        self._story = copy_value(story, copy_from, "_story")
        self._spectators = copy_value(spectators, copy_from, "_spectators")
        self._notification_manager = copy_value(notification_manager, copy_from, "_notification_manager")

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


class CreatedGame(Game):
    """
    A game in the CREATED state
    """

    def __init__(self, host, game_id, notfication_manager):
        super(CreatedGame, self).__init__(host=host, game_id=game_id, players=[],
                                          story="", current_round=1, spectators=[],
                                          notification_manager=notfication_manager)

    def register_player(self, player_to_add):
        """
        :return: a CreatedGame with an updated list of players

        :raises: RuntimeError if the player has already joined the game
        """
        if player_to_add in self.players + self.spectators:
            raise RuntimeError("{} has already joined the game!".format(player_to_add))
        self._players.append(player_to_add)
        event = PlayerJoined(player_to_add.name)
        self._notification_manager.publish(event)
        self._notification_manager.subscribe(player_to_add, PlayerJoined, GameStarted, StoryUpdate, Done)
        return self

    def register_spectator(self, spectator_to_add):
        """
        :return: a CreatedGame with an updated list of spectators

        :raises: RuntimeError if the spectator has already joined the game
        """
        if spectator_to_add in self.spectators + self.players:
            raise RuntimeError("{} has already joined the game!".format(spectator_to_add))
        self._spectators.append(spectator_to_add)
        self._notification_manager.subscribe(spectator_to_add, PlayerJoined, GameStarted, NewPrompts, StoryUpdate, Done)
        return self

    def start(self):
        """
        :return: a WaitForSubmissionsGame
        """
        self._notification_manager.publish(GameStarted())
        return WaitForSubmissionsGame(copy_from=self)


class WaitForSubmissionsGame(Game):
    """
    A game in the WAIT_FOR_SUBMISSIONS state
    """

    def __init__(self, *args, **kwargs):
        super(WaitForSubmissionsGame, self).__init__(*args, **kwargs)
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
            self._notification_manager.publish(NewPrompts(prompts=self.prompts.values()))
            return ChoosingGame(copy_from=self)
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
            self._notification_manager.publish(Done(winner="Everybody!", story=updated_story))
            return CompleteGame(copy_from=self, story=updated_story, current_round=TOTAL_ROUNDS)
        else:
            is_final_round = self.round_number == (TOTAL_ROUNDS - 1)
            self._notification_manager.publish(StoryUpdate(updated_story, is_final_round=is_final_round))
            return WaitForSubmissionsGame(copy_from=self, story=updated_story, current_round=self.round_number + 1)


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
