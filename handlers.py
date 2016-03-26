"""
Handlers for calling into the game backend via AWS Lambda
"""
import json
import uuid

from aws import GameWrapperFactory, Host, Player


def create_game(event, context):
    """
    Called when somebody wants to create a new game.

    The event is expected to contain the following parameter(s):
    - name: the name of the player hosting the game

    Returns the following:
    - gameId: the unique four-letter ID of the new game
    - hostToken: token that identifies the caller as the host of the game
                 this token must be included in subsequent operations
                 to identify the requester as the host
    """
    host = Host(event["name"], uuid.uuid4())
    game_wrapper = GameWrapperFactory().new_game(host)
    return json.dumps({'gameId': game_wrapper.game.id,
                       'hostToken': game_wrapper.game.host.token.hex})

def join_game(event, context):
    """
    Called when somebody wants to join an existing game.

    The event is expected to contain the following parameter(s):
    - name: the name of the player joining the game
    - gameId: the four-letter ID of the game to join

    Returns the following:
    - playerToken: token that identifies the caller as a player in the game
                   this token must be included in subsequent operations
                   in order to identify the requester as this player
    """
    with GameWrapperFactory().load_game(event["gameId"]) as game:
        player = Player(event["name"], uuid.uuid4())
        player.join(game)
        return json.dumps({'playerToken': player.token.hex})

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

