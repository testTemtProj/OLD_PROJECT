from help.tests import *

class TestGetmyadController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='getmyad', action='index'))
        # Test response...
