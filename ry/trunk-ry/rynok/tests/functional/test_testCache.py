from rynok.tests import *

class TestTestcacheController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='testCache', action='index'))
        # Test response...
