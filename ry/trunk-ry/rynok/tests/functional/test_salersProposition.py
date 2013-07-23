from rynok.tests import *

class TestSalerspropositionController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='salersProposition', action='index'))
        # Test response...
