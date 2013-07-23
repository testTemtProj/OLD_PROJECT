#include <boost/test/unit_test.hpp>
#include <map>

#include "../src/RandomEntity.h"


/** Тест случайного распределения с учётом весов элементов */
BOOST_AUTO_TEST_CASE( TestRandomEntity )
{
    RandomEntity<char> rand;
    rand.add('A', 1.5);
    rand.add('B', 1);
    rand.add('C', 2.5);

    std::map<char, unsigned int> counters;
    const unsigned int MAX = 100000;
    for (unsigned int i = 0; i < MAX; i++) {
	char element = rand.get();
	BOOST_REQUIRE(element != 0);
	counters[element]++;
    }

    // Погрешность не должна превышать 2%
    const double summ = 5.0;		// Суммарный вес всех элементов
    const double part = MAX / summ;	// Одна часть
    BOOST_CHECK_CLOSE(counters['A'], part * 1.5, 2);
    BOOST_CHECK_CLOSE(counters['B'], part * 1.0, 2);
    BOOST_CHECK_CLOSE(counters['C'], part * 2.5, 2);
}

/** Проверка работы пустого генератора */
BOOST_AUTO_TEST_CASE( TestEmptyRandomEntity )
{
    RandomEntity<char> rand;
    BOOST_CHECK_THROW ( rand.get(), RandomEntity<char>::NoItemsException );
}
