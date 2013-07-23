from rynok.tests import *

class TestRedirectController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='redirect', action='index'))
        # Test response...
