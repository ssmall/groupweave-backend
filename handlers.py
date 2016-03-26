"""
Handlers for calling into the game backend via AWS Lambda
"""
import json
import uuid

from aws import GameWrapperFactory, Host

def create_game(event, context):
    """
    Called when somebody wants to create a new game.

    The event is expected to contain the following parameter:
    - name: the name of the player hosting the game

    Takes no parameters, and returns the following:
    - gameId: the unique four-letter ID of the new game
    - hostToken: token that identifies the caller as the host of the game
                  this token must be included in subsequent 'host' operations
                  to be considered authorized
    """
    host = Host(event["name"], uuid.uuid4())
    game_wrapper = GameWrapperFactory().new_game(host)
    return json.dumps({'gameId': game_wrapper.game.id,
                       'hostToken': game_wrapper.game.host.token.hex})

def join_game():
    """
    Called when somebody wants to join an existing game
    """
    pass

def start_game():
    """
    Called when the host wants to start an existing game
    """
    pass

def submit_prompt():
    """
    Called when a player submits a prompt for an existing game
    """
    pass

def choose_prompt():
    """
    Called when the host chooses a prompt for an existing game
    """
    pass

