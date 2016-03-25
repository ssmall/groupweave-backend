"""
Events that are used to communicate game state
between the host and the players
"""

import json


class Event(object):
    """
    Base class for in-game events
    """

    def __init__(self, event_type, **properties):
        self.type = event_type
        self._properties = properties

    def __getitem__(self, item):
        return self._properties[item]

    def __str__(self):
        return "{}{}".format(self.type, self._properties)

    def __eq__(self, other):
        return (isinstance(other, self.__class__)
                and (other.type == self.type)
                and (other._properties == self._properties))

    def toJson(self):
        """
        Serialize this Event to a string
        :return: a JSON string
        """
        return json.dumps({'type': self.type,
                           'properties': self._properties})


class PlayerJoined(Event):
    """
    Event that is triggered when a player joins the game
    """

    def __init__(self, player_name):
        super(PlayerJoined, self).__init__(self.__class__.__name__, player_name=player_name)

class StartGame(Event):
    """
    Event that is triggered when the host requests to start the game
    """

    def __init__(self):
        super(StartGame, self).__init__(self.__class__.__name__)


class GameStarted(Event):
    """
    Event that is triggered when the game starts
    """

    def __init__(self):
        super(GameStarted, self).__init__(self.__class__.__name__)


class Prompt(Event):
    """
    Event that is triggered when a player submits a new prompt
    """

    def __init__(self, prompt, player):
        super(Prompt, self).__init__(self.__class__.__name__, prompt=prompt, player=player)


class NewPrompts(Event):
    """
    Event that aggregates all new prompts for a round
    """

    def __init__(self, prompts):
        super(NewPrompts, self).__init__(self.__class__.__name__, prompts=prompts)

class ChoosePrompt(Event):
    """
    Event that indicates that the host has chosen a new prompt
    """

    def __init__(self, choice):
        super(ChoosePrompt, self).__init__(self.__class__.__name__, choice=choice)


class StoryUpdate(Event):
    """
    Event that is triggered when the host chooses a prompt to continue the story
    """

    def __init__(self, story, is_final_round=False):
        super(StoryUpdate, self).__init__(self.__class__.__name__, story=story, is_final_round=is_final_round)


class Done(Event):
    """
    Event that signifies the end of the game
    """

    def __init__(self, winner, story):
        super(Done, self).__init__(self.__class__.__name__, winner=winner, story=story)


_EVENT_SUBCLASSES = {name: cls for (name, cls) in [(cls.__name__, cls) for cls in Event.__subclasses__()]}


def from_json(str):
    """
    Deserializes a JSON string into an Event, attempting to construct
    an Event subclass of the appropriate type.
    """

    deserialized = json.loads(str)
    event_type = deserialized['type']
    event_properties = deserialized['properties']

    if event_type in _EVENT_SUBCLASSES:
        return _EVENT_SUBCLASSES[event_type](**event_properties)
    else:
        return Event(event_type, **event_properties)
