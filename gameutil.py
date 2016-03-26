"""
Utility classes for working with game objects
"""

import game


class GameReference(object):
    """
    A necessary evil given that game state
    transitions happen in multiple places
    """

    def __init__(self, initialGame):
        self.game = initialGame

    def __getattr__(self, item):
        game_attr = getattr(self.game, item)
        if callable(game_attr):
            return MethodReference(self, game_attr)
        return game_attr


class MethodReference(object):
    def __init__(self, gameReference, originalMethod):
        self.gameReference = gameReference
        self.originalMethod = originalMethod

    def __call__(self, *args, **kwargs):
        return_val = self.originalMethod(*args, **kwargs)
        if issubclass(return_val.__class__, game.Game):
            self.gameReference.game = return_val
        return return_val
