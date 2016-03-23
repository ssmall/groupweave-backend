"""
Events that are used to communicate game state
between the host and the players
"""

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
        print "{}{}".format(self.type, self._properties)

    def __eq__(self, other):
        return (isinstance(other, self.__class__)
                and (other.type == self.type)
                and (other._properties == self._properties))


class PlayerJoined(Event):
    """
    Event that is triggered when a player joins the game
    """

    def __init__(self, new_player_name):
        super(PlayerJoined, self).__init__(self.__class__.__name__, player=new_player_name)


class GameStarted(Event):
    """
    Event that is triggered when the game starts
    """

    def __init__(self, num_players):
        super(GameStarted, self).__init__(self.__class__.__name__, num_players=num_players)


class Prompt(Event):
    """
    Event that is triggered when a player submits a new prompt
    """

    def __init__(self, prompt, player):
        super(Prompt, self).__init__(self.__class__.__name__, prompt=prompt, player=player)


class StoryUpdate(Event):
    """
    Event that is triggered when the host chooses a prompt to continue the story
    """

    def __init__(self, new_story, is_final_round=False):
        super(StoryUpdate, self).__init__(self.__class__.__name__, story=new_story, final_round=is_final_round)


class Done(Event):
    """
    Event that signifies the end of the game
    """

    def __init__(self, winning_player, final_story):
        super(Done, self).__init__(self.__class__.__name__, winner=winning_player, story=final_story)