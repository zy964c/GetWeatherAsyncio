import copy

class Settings():

    options = {}
    cities = {}
    
    @classmethod
    def update_opts(cls, opts):
        cls.options = copy.deepcopy(opts)