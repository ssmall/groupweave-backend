"""
Handlers for calling into the game backend via AWS Lambda
"""
import json
import uuid

from aws import GameWrapperFactory, Host, Player

class ErrorHandler(object):
    """
    Context manager for wrapping errors in a way
    that provides consistent error messages
    """

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            raise RuntimeError("Server Error: " + str(exc_val))

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
    - queueUrl: the URL of the SQS queue for host notifications
    """
    with ErrorHandler():
        host = Host(event["name"], uuid.uuid4())
        with GameWrapperFactory().new_game(host) as game:
            host.join(game)
            return json.dumps({'gameId': game.id,
                               'hostToken': game.host.token.hex,
                               'queueUrl': game.host.queueUrl})


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
    with ErrorHandler():
        with GameWrapperFactory().load_game(event["gameId"]) as game:
            player = Player(event["name"], uuid.uuid4())
            player.join(game)
            return json.dumps({'playerToken': player.token.hex})


def start_game(event, context):
    """
    Called when the host wants to start an existing game.

    The event is expected to contain the following parameter(s):
    - gameId: the id of the game to start
    - token: the token that identifies the caller as the host

    Returns nothing if succesful, or an error if the game
    could not be started for some reason.
    """
    with ErrorHandler():
        with GameWrapperFactory().load_game(event["gameId"]) as game:
            host = game.host
            if event["token"] != host.token.hex:
                raise RuntimeError("Token mismatch; you are not authorized to perform this operation")
            game.start()


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
