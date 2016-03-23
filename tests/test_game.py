from unittest import TestCase

from events import PlayerJoined, GameStarted
from game import Game, Player, GameFactory
from mock import Mock

MOCK_GAME_ID = "ASDF"


class TestGame(TestCase):
    def setUp(self):
        id_generator = Mock()
        id_generator.new_id = Mock(return_value=MOCK_GAME_ID)
        self.game_factory = GameFactory(id_generator)
        self.host = self.create_player("Host")

    def test_game_creation(self):
        game = self.game_factory.new_game(self.host)
        self.assertEqual(game.id, MOCK_GAME_ID)
        self.assertIs(game.host, self.host)
        self.assertNotIn(self.host, game.players)

    def test_player_joins_game(self):
        name = "Jeb"
        new_player = self.create_player(name)

        game = self.create_game_with_player(new_player)

        self.assertIn(new_player, game.players)
        self.host.notify.assert_called_with(PlayerJoined(name))



    def test_cant_add_player_twice(self):
        new_player = self.create_player("Jeb")

        game = self.create_game_with_player(new_player)

        self.assertRaises(RuntimeError, game.register, new_player)

    def test_game_start(self):
        player_2 = self.create_player("Jeb")

        game = self.create_game_with_player(player_2)

        game.start()

        player_2.notify.assert_called_with(GameStarted(2))

    def test_player_submits_prompt(self):
        pass

    def create_player(self, name):
        new_player = Mock(spec=Player)
        new_player.name = name
        return new_player

    def create_game_with_player(self, new_player):
        game = self.game_factory.new_game(self.host)
        game.register(new_player)
        return game