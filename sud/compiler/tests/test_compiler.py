# encoding: utf-8
import unittest
import subprocess
import os
import tempfile

COMPILER = "../bin/compiler"


class TestCompiler(unittest.TestCase):

    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(delete=False)
        self.filename = self.temp_file.name

    def tearDown(self):
        os.unlink(self.temp_file.name)

    def call(self, *args):
        ''' Вызывает системный процесс с аргументами ``args``, дожидается
            завершения и возвращает код возврата.
        '''
        return subprocess.call(args, stdout=subprocess.PIPE) 

    def test_required_args(self):
        ''' Проверка обязательных аргументов командной строки '''
        self.assertEquals(self.call(COMPILER), 1)

    def test_create_simple_dict(self):
        ''' Проверка на создание простейшего словаря '''
        d = tempfile.NamedTemporaryFile()
        d.writelines(["ab\n", "ac\n", "z\n"])
        d.seek(0)
        subprocess.call([COMPILER, self.filename], stdin=d, stdout=None)
        self.assertEquals(os.path.getsize(self.filename), 82)

    def test_create_russian_dict(self):
        ''' Проверка на создание словаря, содержащего кириллицу '''
        d = tempfile.NamedTemporaryFile()
        d.writelines(["аб\n", "ав\n", "я\n"])
        d.seek(0)
        subprocess.call([COMPILER, self.filename], stdin=d, stdout=None)
        self.assertEquals(os.path.getsize(self.filename), 82)

    def test_create_dict_with_themes_and_rates(self):
        ''' Проверка создания словаря с тематиками и весом каждой записи '''
        d = tempfile.NamedTemporaryFile()
        d.writelines(["ab\t0\t10\n", "ac\t0\t20\n", "z\t1\t5\n"])
        d.seek(0)
        subprocess.call([COMPILER, self.filename], stdin=d, stdout=None)
        self.assertEquals(os.path.getsize(self.filename), 84)

    def test_benchmark(self):
        ''' Замеры времени создания большого словаря '''
        return
        subprocess.call([COMPILER, '../../data/1M.compiled'],
                        stdin=open('../../data/1M.terms'))



if __name__ == '__main__':
    unittest.main()
