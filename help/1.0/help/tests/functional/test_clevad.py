from help.tests import *

class TestClevadController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='clevad', action='index'))
        # Test response...
