class NavigationAbstract(object):

    @staticmethod
    def get_by_id(*args, **kwargs):
        raise NotImplementedError("method get_by_id is not implemented implemented in subclass")

    
    @staticmethod
    def get_by_parent_id(*args, **kwargs):
        raise NotImplementedError("method get_by_parent_id is not implemented in subclass")
