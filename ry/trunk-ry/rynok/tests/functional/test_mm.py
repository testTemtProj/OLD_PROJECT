from rynok.tests import *

class TestMmController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='mm', action='index'))
        # Test response...
