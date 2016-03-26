from unittest import TestCase

from mock.mock import Mock

from gameutil import GameReference
from game import Game


class TestGameReference(TestCase):

    def test_member_access(self):
        method_return_value = "method_return_value"
        field_value = "field_value"
        game = Mock(spec=Game)
        game.method = Mock(return_value=method_return_value)
        game.field = field_value

        ref = GameReference(game)

        actual_method_return = ref.method()
        game.method.assert_any_call()
        self.assertEqual(actual_method_return, method_return_value)

        self.assertEqual(ref.field, field_value)

    def test_update_reference(self):
        initialGame = Mock(spec=Game, name="initialGame")
        nextGame = Mock(spec=Game, name="nextGame")
        initialGame.transition = Mock(return_value=nextGame)

        ref = GameReference(initialGame)

        ref.transition()

        initialGame.transition.assert_any_call()
        self.assertIs(ref.game, nextGame)
