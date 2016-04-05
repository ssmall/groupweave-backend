"""
Handlers for calling into the game backend via AWS Lambda
"""
import json
import uuid

import sys

from aws import GameWrapperFactory, Host, Player, dynamo, sqs, Spectator
from events import Prompt, ChoosePrompt


class AuthorizationError(StandardError):
    """
    An error that signifies an unauthorized call to a handler.
    That is, the caller does not have the proper permissions
    to perform the game action specified by the handler.
    """

    def __init__(self, action, caller):
        super(AuthorizationError, self).__init__("{} is not authorized to perform action '{}'".format(caller, action))


class ErrorHandler(object):
    """
    Context manager for wrapping errors in a way
    that provides consistent error messages
    """

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is AuthorizationError:
            raise RuntimeError("Authorization Error: {}".format(exc_val))
        elif exc_type is not None:
            print >> sys.stderr, exc_tb
            raise RuntimeError("Server Error: {}".format(exc_val))
        else:
            pass


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
        with GameWrapperFactory.new_game(host) as game:
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
    - queueUrl: the URL of the SQS queue for player notifications
    """
    with ErrorHandler():
        with GameWrapperFactory.load_game(event["gameId"]) as game:
            player = Player(event["name"], uuid.uuid4())
            player.join(game)
            return json.dumps({'playerToken': player.token.hex,
                               'queueUrl': player.queueUrl})


def spectate_game(event, context):
    """
    Called when somebody wants to spectate an existing game.

    The event is expected to contain the following parameter(s):
    - gamedId: the four-letter ID of the game to spectate

    Returns the following:
    - queueUrl: the URL of the SQS queue for spectator notifications
    """
    with ErrorHandler():
        with GameWrapperFactory.load_game(event["gameId"]) as game:
            spectator = Spectator(uuid.uuid4())
            spectator.join(game)
            return json.dumps({'queueUrl': spectator.queueUrl})


def start_game(event, context):
    """
    Called when the host wants to start an existing game.

    The event is expected to contain the following parameter(s):
    - gameId: the id of the game to start
    - token: the token that identifies the caller as the host

    Returns nothing if successful, or an error if the game
    could not be started for some reason.
    """
    with ErrorHandler():
        with GameWrapperFactory.load_game(event["gameId"]) as game:
            host = game.host
            if event["token"] != host.token.hex:
                raise AuthorizationError("start_game", "player with token {}".format(event["token"]))
            game.start()


def submit_prompt(event, context):
    """
    Called when a player submits a prompt for an existing game.

    The event is expected to contain the following parameter(s):
    - gameId: the id of the game
    - token: the token identifying this player
    - prompt: the text of the prompt to be submitted

    Returns nothing if successful, or an error if the prompt could
    not be submitted.
    """
    with ErrorHandler():
        with GameWrapperFactory.load_game(event["gameId"]) as game:
            token_to_player = {player.token.hex: player for player in game.players}
            if event["token"] not in token_to_player.keys():
                raise AuthorizationError("submit_prompt", "player with token {}".format(event["token"]))
            game.receive_prompt(Prompt(event["prompt"], token_to_player[event["token"]].name))


def choose_prompt(event, context):
    """
    Called when the host chooses a prompt for an existing game.

    The event is expected to contain the following parameter(s):
    - gameId: the id of the game
    - token: the token identifying this player as the host
    - prompt: the host's chosen prompt

    Returns nothing if successful, or an error if the prompt could
    not be chosen
    """
    with ErrorHandler():
        with GameWrapperFactory.load_game(event["gameId"]) as game:
            host = game.host
            if event["token"] != host.token.hex:
                raise AuthorizationError('choose_prompt', "player with token {}".format(event["token"]))
            game.choose_prompt(ChoosePrompt(event["prompt"]))


def cleanup(event, context):
    """
    Called to clean up old game state.

    """
    removed_games = []
    removed_queues = []
    for game in dynamo.get_old_or_finished_games():
        removed_queues.append(sqs.delete_queue(game.host.queueUrl))
        for player in game.players:
            removed_queues.append(sqs.delete_queue(player.queueUrl))
        removed_games.append(dynamo.delete_game(game))
    return json.dumps({
        'removed_games': removed_games,
        'removed_queues': removed_queues
    })
