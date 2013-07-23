from manager.tests import *

class TestCampaignsController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='campaigns', action='index'))
        # Test response...
