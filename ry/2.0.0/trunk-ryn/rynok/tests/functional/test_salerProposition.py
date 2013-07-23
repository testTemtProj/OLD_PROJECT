from rynok.tests import *

class TestSalerpropositionController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='salerProposition', action='index'))
        # Test response...
