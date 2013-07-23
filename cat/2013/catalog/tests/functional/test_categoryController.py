from catalog.tests import *

class TestCategorycontrollerController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='categoryController', action='index'))
        # Test response...
