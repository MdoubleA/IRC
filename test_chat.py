import unittest
import nose
from unittest import TestCase

from Server import Chat

class TestChat(TestCase):
    def test_basic(self):
        
        # get rid of profanity
        input = "blah"
        expect = "fuck off steve"
        actual = "hi steve"

        assert(actual == expect)
        #self.fail()

    def test_connectionLost(self):
        input = "blah"
        expect = "fuck off steve"
        actual = "hi steve"

        chat = Chat()
        chat.client_list = ['steve', 'bob', 'michael']


        chat.connectionLost()
        assert(actual == expect)
        #self.fail()

    def test_dataReceived(self):
        self.fail()

    def test_handle_GREET(self):
        self.fail()

    def test_handle_CONVO(self):
        self.fail()

    def test_get_user_room_names(self):
        self.fail()

    def test_message(self):
        self.fail()

    def test_join(self):
        self.fail()

    def test_create(self):
        self.fail()

    def test_list(self):
        self.fail()

    def test_hello(self):
        self.fail()

    def test_make(self):
        self.fail()

    def test_panic(self):
        self.fail()
