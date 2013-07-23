# This Python file uses the following encoding: utf-8
from getmyad.model import Account
from getmyad import model
from pymongo import Connection



class TestAccount:
    
    def setUp(self):
        self.mongo = Connection()
        self.mongo.drop_database('getmyad_tests')
        self.db = self.mongo['getmyad_tests']
        model.Options.db = self.db
    
    def tearDown(self):
        self.mongo.drop_database(self.db)
        self.mongo.disconnect()

    def test_register_and_load_account(self):
        acc1 = Account(login='test')
        acc1.email = 'silver@ukr.net'
        acc1.manager_get = 'manager'
        acc1.min_out_sum = 30
        acc1.owner_name = u'Вася Пупкин'
        acc1.password = '123qwe'
        acc1.phone = '+38(050) 123-123-12'
        acc1.register()

        acc2 = Account(login='test')
        acc2.load()

        assert acc1.email == acc2.email == 'silver@ukr.net'
        assert acc1.manager_get == acc2.manager_get == 'manager'
        assert acc1.min_out_sum == acc2.min_out_sum == 30
        assert acc1.owner_name == acc2.owner_name == u'Вася Пупкин'
        assert acc1.password == acc2.password == '123qwe'
        assert acc1.phone == acc2.phone == '+38(050) 123-123-12'

    def test_register_account_duplicate(self):
        try:
            acc = Account('test_login')
            acc.db = self.db
            acc.register()
            acc.register()
            raise AssertionError('Duplicate logins are not allowed')
        except Account.AlreadyExistsError:
            pass
        except:
            raise