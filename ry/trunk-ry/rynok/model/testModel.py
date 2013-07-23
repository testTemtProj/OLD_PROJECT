from rynok.model.baseModel import Base

class TestModel(object):

    some_value = 'some value'

    @staticmethod
    def some_method():
        return TestModel.some_value
    pass
