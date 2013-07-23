from rynok.tests import *

class TestPopularProductsController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='popular_products', action='index'))
        # Test response...
