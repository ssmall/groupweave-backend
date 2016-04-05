from unittest import TestCase

from mock import Mock

from events import GameStarted, Done
from game import NotificationManager, Player


class TestNotificationManager(TestCase):
    def test_notifications(self):
        mgr = NotificationManager()

        player_one = Mock(spec=Player)
        player_two = Mock(spec=Player)

        mgr.subscribe(player_one, GameStarted, Done)
        mgr.subscribe(player_two, Done)

        started_event = GameStarted()
        mgr.publish(started_event)

        player_one.notify.assert_called_with(started_event)
        player_two.notify.assert_not_called()

        done_event = Done("Somebody", "Something")
        mgr.publish(done_event)

        player_two.notify.assert_called_with(done_event)
        player_one.notify.assert_called_with(done_event)
