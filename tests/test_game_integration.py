"""
Integration test for the game logic,
simulating a full game played with a host
and two players.
"""
from unittest import TestCase

from mock import Mock

from events import Prompt, ChoosePrompt
from game import GameFactory, Player, TOTAL_ROUNDS, CompleteGame


class TestGameIntegration(TestCase):

    def test_gameplay(self):
        host = Mock(spec=Player)
        player1 = Mock(spec=Player)
        player1.name = "Jeb"
        player2 = Mock(spec=Player)
        player2.name = "Zedd"
        game = GameFactory(Mock(new_id=Mock(return_value="0000"))).new_game(host)

        game.register_player(player1)
        game.register_player(player2)

        game = game.start()

        expected_story = ""

        first_player_prompt = "First player prompt"
        second_player_prompt = "Second player prompt"
        for i in range(0, TOTAL_ROUNDS):
            game = game.receive_prompt(Prompt(first_player_prompt, player1.name))
            game = game.receive_prompt(Prompt(second_player_prompt, player2.name))
            choice = first_player_prompt if i % 2 == 0 else second_player_prompt
            expected_story = "{} {}".format(expected_story, choice)
            game = game.choose_prompt(ChoosePrompt(choice))

        self.assertIs(type(game), CompleteGame)
        self.assertEqual(game.story, expected_story)
