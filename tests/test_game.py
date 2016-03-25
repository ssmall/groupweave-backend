from unittest import TestCase

from events import PlayerJoined, GameStarted, Prompt, NewPrompts
from game import Player, GameFactory, WaitForSubmissionsGame, ChoosingGame
from mock import Mock

MOCK_GAME_ID = "ASDF"


class TestGame(TestCase):
    def setUp(self):
        id_generator = Mock()
        id_generator.new_id = Mock(return_value=MOCK_GAME_ID)
        self.game_factory = GameFactory(id_generator)
        self.host = self.create_player("Host")
        self.player = self.create_player("Jeb")

    def test_game_creation(self):
        game = self.game_factory.new_game(self.host)
        self.assertEqual(game.id, MOCK_GAME_ID)
        self.assertIs(game.host, self.host)
        self.assertNotIn(self.host, game.players)

    def test_player_joins_game(self):
        game = self.create_game_with_player(self.player)

        self.assertIn(self.player, game.players)
        self.host.notify.assert_called_with(PlayerJoined(self.player.name))

        second_player_name = "Zedd"
        game.register(self.create_player(second_player_name))
        self.host.notify.assert_called_with(PlayerJoined(second_player_name))
        self.player.notify.assert_called_with(PlayerJoined(second_player_name))

    def test_cant_add_player_twice(self):
        game = self.create_game_with_player(self.player)

        self.assertRaises(RuntimeError, game.register, self.player)

    def test_game_start(self):
        game = self.create_game_with_player(self.player)

        game.start()

        self.player.notify.assert_called_with(GameStarted())

    def test_player_submits_prompt(self):
        game = WaitForSubmissionsGame(self.host, MOCK_GAME_ID, [self.player])

        prompt = "This is a prompt"
        game.receive_prompt(Prompt(prompt, self.player))

        self.assertDictContainsSubset({self.player.name: prompt}, game.prompts)

    def test_cannot_submit_prompt_twice(self):
        game = WaitForSubmissionsGame(self.host, MOCK_GAME_ID, [self.player])

        game.receive_prompt(Prompt("First prompt", self.player))

        self.assertRaises(RuntimeError, game.receive_prompt, Prompt("Second prompt", self.player))

    def test_all_prompts_received(self):
        second_player = self.create_player("Zedd")
        game = WaitForSubmissionsGame(self.host, MOCK_GAME_ID, [self.player, second_player])

        first_player_prompt = "First player prompt"
        game = game.receive_prompt(Prompt(first_player_prompt, self.player))

        self.assertIs(type(game), WaitForSubmissionsGame)
        self.host.notify.assert_not_called()

        second_player_prompt = "Second player prompt"
        resultGame = game.receive_prompt(Prompt(second_player_prompt, second_player))

        self.assertIs(type(resultGame), ChoosingGame)
        self.host.notify.assert_called_with(NewPrompts(prompts=[first_player_prompt, second_player_prompt]))

    def create_player(self, name):
        new_player = Mock(spec=Player)
        new_player.name = name
        return new_player

    def create_game_with_player(self, new_player):
        game = self.game_factory.new_game(self.host)
        game.register(new_player)
        return game
