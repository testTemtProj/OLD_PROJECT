from manager.tests import *

class TestParserSettinsController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='parser_settins', action='index'))
        # Test response...
