from rynok.tests import *

class TestNewProductsController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='new_products', action='index'))
        # Test response...
