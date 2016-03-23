from unittest import TestCase

from events import Event, PlayerJoined


class TestEvent(TestCase):
    def test_event_properties(self):
        event_type = "CustomEvent"
        event = Event(event_type, a=1, b=2)
        self.assertIs(event.type, event_type)
        self.assertIs(event['a'], 1)
        self.assertIs(event['b'], 2)
        self.assertRaises(KeyError, lambda: event['c'])

    def test_event_equality(self):
        event_type = "CUSTOM_EVENT"
        event1 = Event(event_type, a=1, b=2)
        event2 = Event(event_type, a=1, b=2)

        self.assertEqual(event1, event2)