from manager.tests import *

class TestCategorysettingController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='categorySetting', action='index'))
        # Test response...
