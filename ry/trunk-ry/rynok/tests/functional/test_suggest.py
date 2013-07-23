from rynok.tests import *

class TestSuggestController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='suggest', action='index'))
        # Test response...
