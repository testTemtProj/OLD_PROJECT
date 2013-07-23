from catalog.tests import *

class TestLanguageController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='language', action='index'))
        # Test response...
