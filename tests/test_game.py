from unittest import TestCase

from events import PlayerJoined, GameStarted, Prompt, NewPrompts, StoryUpdate, ChoosePrompt, Done
from game import Player, GameFactory, WaitForSubmissionsGame, ChoosingGame, TOTAL_ROUNDS, CompleteGame
from mock import Mock

MOCK_GAME_ID = "ASDF"


class TestGame(TestCase):
    def setUp(self):
        id_generator = Mock()
        id_generator.new_id = Mock(return_value=MOCK_GAME_ID)
        self.game_factory = GameFactory(id_generator)
        self.host = self.create_player("Host")
        self.first_player = self.create_player("Jeb")
        self.second_player = self.create_player("Zedd")

    def test_game_creation(self):
        game = self.game_factory.new_game(self.host)
        self.assertEqual(game.id, MOCK_GAME_ID)
        self.assertIs(game.host, self.host)
        self.assertNotIn(self.host, game.players)

    def test_player_joins_game(self):
        game = self.create_game_with_player(self.first_player)

        self.assertIn(self.first_player, game.players)
        self.host.notify.assert_called_with(PlayerJoined(self.first_player.name))

        second_player_name = "Zedd"
        game.register(self.create_player(second_player_name))
        self.host.notify.assert_called_with(PlayerJoined(second_player_name))
        self.first_player.notify.assert_called_with(PlayerJoined(second_player_name))

    def test_cant_add_player_twice(self):
        game = self.create_game_with_player(self.first_player)

        self.assertRaises(RuntimeError, game.register, self.first_player)

    def test_game_start(self):
        game = self.create_game_with_player(self.first_player)

        game.start()

        self.first_player.notify.assert_called_with(GameStarted())

    def test_player_submits_prompt(self):
        game = WaitForSubmissionsGame(self.host, MOCK_GAME_ID, [self.first_player], "", 1)

        prompt = "This is a prompt"
        game.receive_prompt(Prompt(prompt, self.first_player.name))

        self.assertDictContainsSubset({self.first_player.name: prompt}, game.prompts)

    def test_cannot_submit_prompt_twice(self):
        game = WaitForSubmissionsGame(self.host, MOCK_GAME_ID, [self.first_player], "", 1)

        game.receive_prompt(Prompt("First prompt", self.first_player))

        self.assertRaises(RuntimeError, game.receive_prompt, Prompt("Second prompt", self.first_player))

    def test_all_prompts_received(self):
        game = WaitForSubmissionsGame(self.host, MOCK_GAME_ID, [self.first_player, self.second_player], "", 1)

        first_player_prompt = "First player prompt"
        game = game.receive_prompt(Prompt(first_player_prompt, self.first_player))

        self.assertIs(type(game), WaitForSubmissionsGame)
        self.host.notify.assert_not_called()

        second_player_prompt = "Second player prompt"
        resultGame = game.receive_prompt(Prompt(second_player_prompt, self.second_player.name))

        self.assertIs(type(resultGame), ChoosingGame)
        self.host.notify.assert_called_with(NewPrompts(prompts=[first_player_prompt, second_player_prompt]))

    def test_host_chooses_prompt(self):
        story_so_far = "This is the story so far."
        game = ChoosingGame(self.host, MOCK_GAME_ID, [self.first_player, self.second_player], story_so_far)

        choice = "This is the next part of the story."
        updated_story = "{} {}".format(story_so_far, choice)
        result_game = game.choose_prompt(ChoosePrompt(choice))

        self.first_player.notify.assert_called_with(StoryUpdate(updated_story))
        self.second_player.notify.assert_called_with(StoryUpdate(updated_story))
        self.assertIs(type(result_game), WaitForSubmissionsGame)
        self.assertEqual(result_game.story, updated_story)

    def test_final_round_notifications(self):
        story_so_far = "The story so far."
        game = ChoosingGame(self.host, MOCK_GAME_ID, [self.first_player], story_so_far, TOTAL_ROUNDS - 1)

        chosen_prompt = "Chosen prompt"
        updated_story = "{} {}".format(story_so_far, chosen_prompt)
        game.choose_prompt(ChoosePrompt(chosen_prompt))

        self.first_player.notify.assert_called_with(StoryUpdate(updated_story, is_final_round=True))

    def test_end_of_game(self):
        story_so_far = "Story so far"
        game = ChoosingGame(self.host, MOCK_GAME_ID, [self.first_player], story_so_far, TOTAL_ROUNDS)

        chosen_prompt = "Chosen prompt"
        updated_story = "{} {}".format(story_so_far, chosen_prompt)
        result_game = game.choose_prompt(ChoosePrompt(chosen_prompt))

        self.first_player.notify.assert_called_with(Done(winner="Everybody!", story=updated_story))
        self.assertIs(type(result_game), CompleteGame)

    def create_player(self, name):
        new_player = Mock(spec=Player)
        new_player.name = name
        return new_player

    def create_game_with_player(self, new_player):
        game = self.game_factory.new_game(self.host)
        game.register(new_player)
        return game
