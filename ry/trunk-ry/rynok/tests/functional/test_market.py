from rynok.tests import *

class TestMarketController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='market', action='index'))
        # Test response...
