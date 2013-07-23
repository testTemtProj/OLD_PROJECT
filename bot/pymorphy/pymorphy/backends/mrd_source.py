#coding: utf-8
from __future__ import unicode_literals
import codecs
from pymorphy.backends.base import DictDataSource
from pymorphy.constants import PRODUCTIVE_CLASSES


class MrdDataSource(DictDataSource):
    """
    Источник данных для морфологического анализатора pymorphy,
    берущий информацию из оригинальных mrd-файлов (в которых кодировка
    была изменена с 1251 на utf-8). Используется для конвертации
    оригинальных данных в простые для обработки ShelveDict или PickledDict.
    """

    def __init__(self, dict_name, gramtab_name, strip_EE=True):
        super(MrdDataSource, self).__init__()
        self.dict_name = dict_name
        self.gramtab_name = gramtab_name
        self.strip_EE = strip_EE

    def load(self):
        self._load(self.dict_name, self.gramtab_name)
        self.calculate_rule_freq()
        self._calculate_endings()
        self._cleanup_endings()

#----------- protected methods -------------

    def _section_lines(self, file):
        """ Прочитать все строки в секции mrd-файла, заменяя Ё на Е,
            если установлен параметр strip_EE
        """
        lines_count = int(file.readline())
        for i in xrange(0, lines_count):
            if self.strip_EE:
                yield file.readline().replace('Ё','Е')
            else:
                yield file.readline()

    def _pass_lines(self, file):
        """ Пропустить секцию """
        for line in self._section_lines(file):
            pass

    def _load_rules(self, file):
        """ Загрузить все парадигмы слов"""
        for paradigm_id, line in enumerate(self._section_lines(file)):
            line_rules = line.strip().split('%')

            index = 0 # не enumerate, чтоб не считать пустые строки
            for rule in line_rules:
                if not rule:
                    continue

                parts = rule.split('*')
                if len(parts)==2:
                    parts.append('')

                suffix, ancode, prefix = parts
                ancode = ancode[:2]

                if paradigm_id not in self.rules:
                    self.rules[paradigm_id] = {}
                    # первое встреченное правило считаем за нормальную форму
                    self.normal_forms[paradigm_id] = parts
                paradigm = self.rules[paradigm_id]

                if suffix not in paradigm:
                    paradigm[suffix] = []

                paradigm[suffix].append((ancode, prefix, index))

                if prefix:
                    self.possible_rule_prefixes.add(prefix)

                index += 1


    def _load_lemmas(self, file):
        """ Загрузить текущую секцию как секцию с леммами """
        for line in self._section_lines(file):
            record = line.split()
            base, paradigm_id = record[0], record[1]

            # Информацию об ударениях, пользовательских сессиях,
            # общий для всех парадигм анкод и наборы префиксов мы тут не
            # учитываем.
            # Сессии - специфичная для aot-редактора информация,
            # анкод можно получить из парадигмы, префикс все равно
            # дублирует "префиксы" self.prefixes (?).
            # accent_model_no, session_no, type_ancode, prefix_set_no = record[2:]

            if base not in self.lemmas:
                self.lemmas[base] = []

            self.rule_freq[paradigm_id] = self.rule_freq.get(paradigm_id, 0) + 1

            # FIXME: т.к. мы отбрасываем анкод, у нас тут могут быть
            # дубликаты парадигм (и будут, для ДУМА, например).
            self.lemmas[base].append(int(paradigm_id))

    def _load_accents(self, file):
        return self._pass_lines(file)

    def _load_logs(self, file):
        """ Загрузить текущую секцию как секцию с логами (бесполезная штука) """
        for line in self._section_lines(file):
            self.logs.append(line.strip())

    def _load_prefixes(self, file):
        """ Загрузить текущую секцию как секцию с префиксами """
        for line in self._section_lines(file):
            self.prefixes.add(line.strip())

    def _load_gramtab(self, file):
        """ Загрузить грамматическую информацию из файла """
        for line in file:
            line=line.strip()
            if line.startswith('//') or line == '':
                continue
            g = line.split()
            if len(g)==3:
                g.append('')
            ancode, letter, type, info = g[0:4]
            self.gramtab[ancode] = (type, info, letter,)

    def _load(self, filename, gramfile):
        with codecs.open(filename, 'r', 'utf8') as dict_file:
            self._load_rules(dict_file)
            self._load_accents(dict_file)
            self._load_logs(dict_file)
            self._load_prefixes(dict_file)
            self._load_lemmas(dict_file)

        with codecs.open(gramfile, 'r', 'utf8') as gram_file:
            self._load_gramtab(gram_file)

    def _calculate_endings(self):
        """
        Подсчитать все возможные 5-буквенные окончания слов.
        Перебирает все возможные формы всех слов по словарю, смотрит окончание
        и добавляет его в словарь.
        """

        # перебираем все слова
        for lemma in self.lemmas:

            # берем все возможные парадигмы
            for paradigm_id in self.lemmas[lemma]:
                paradigm = self.rules[paradigm_id]

                for suffix in paradigm:
                    for ancode, prefix, index in paradigm[suffix]:
                        # формируем слово
                        word = ''.join((prefix, lemma, suffix))

                        # добавляем окончания и номера правил их получения в словарь
                        for i in 1,2,3,4,5:
                            word_end = word[-i:]
                            if word_end:
                                if word_end not in self.endings:
                                    self.endings[word_end] = {}
                                ending = self.endings[word_end]

                                if paradigm_id not in ending:
                                    ending[paradigm_id]=set()

                                ending[paradigm_id].add((suffix, ancode, prefix))


    def _cleanup_endings(self):
        """
        Очистка правил в словаре возможных окончаний. Правил получается много,
        оставляем только те, которые относятся к продуктивным частям речи +
        для каждого окончания оставляем только по 1 самому популярному правилу
        на каждую часть речи.
        """
        for word_end in self.endings:
            ending_info = self.endings[word_end]
            result_info = {}
            best_paradigms = {}

            for paradigm_id in ending_info:

                base_suffix, base_ancode, base_prefix = self.normal_forms[paradigm_id]
                base_gram = self.gramtab[base_ancode]
                word_class = base_gram[0]

                if word_class not in PRODUCTIVE_CLASSES:
                    continue

                if word_class not in best_paradigms:
                    best_paradigms[word_class] = paradigm_id
                else:
                    new_freq = self.rule_freq[paradigm_id]
                    old_freq = self.rule_freq[best_paradigms[word_class]]
                    if new_freq > old_freq:
                        best_paradigms[word_class] = paradigm_id

            for word_class in best_paradigms:
                paradigm_id = best_paradigms[word_class]
                # приводим к tuple, т.к. set плохо сериализуется
                result_info[paradigm_id] = tuple(ending_info[paradigm_id])
            self.endings[word_end] = result_info

    @staticmethod
    def setup_psyco():
        """ Оптимизировать узкие места в MrdDataSource с помощью psyco """
        try:
            import psyco
            psyco.bind(MrdDataSource._calculate_endings)
            psyco.bind(MrdDataSource._load_lemmas)
            psyco.bind(MrdDataSource._cleanup_endings)
            psyco.bind(MrdDataSource._section_lines)
            psyco.bind(DictDataSource.calculate_rule_freq)
        except ImportError:
            pass
