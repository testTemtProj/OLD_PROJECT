from catalog.tests import *

class TestModelcontrollerController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='modelController', action='index'))
        # Test response...
