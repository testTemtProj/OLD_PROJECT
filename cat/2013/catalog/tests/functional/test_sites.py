from catalog.tests import *

class TestSitesController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='sites', action='index'))
        # Test response...
