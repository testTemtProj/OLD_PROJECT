from manager.tests import *

class TestShopaddController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='shopAdd', action='index'))
        # Test response...
