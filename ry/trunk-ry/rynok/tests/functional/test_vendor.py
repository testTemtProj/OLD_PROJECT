from rynok.tests import *

class TestVendorController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='vendor', action='index'))
        # Test response...
