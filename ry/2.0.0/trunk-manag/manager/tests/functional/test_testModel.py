from manager.tests import *

class TestTestmodelController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='testModel', action='index'))
        # Test response...
