#ifndef URLPARSER_H
#define URLPARSER_H

#include <map>
#include <string>
#include <vector>
#include <boost/algorithm/string.hpp>
using namespace std;

/** \brief Парсит URL */
// TODO: Поддержка UrlEncoded значений параметров
class UrlParser
{
public:
    /** \brief Парсит строку url */
    UrlParser(const string &url);

    /** \brief Возвращает карту параметров (key => value) */
    map<string, string> params() const { return params_; }

    /** \brief Возвращает параметр par или пустую строку, если параметр не найден */
    string param(const string &par) const;

private:
    string url_;
    map<string, string> params_;

	void parse();
    string percent_decode(const string &str) const;
    bool is_hex_digit(char hex_digit) const;
    int hex_digit_to_int(char hex_digit) const;
	
	/** \brief Замещает специальные символы в строке пробелами. 
	 
	 добавлено RealInvest Soft. 
	 */
	void replaceSymbols(string &str);
	
	/** \brief Проверка символа ch на принадлежность к множеству специальных символов.
	 ** 
	 * добавлено RealInvest Soft.\n
	 * возвращает true, если символ специальный.\n
	 * символы: + - & | ! ( ) { } [ ] ^ " ~ * ? : \
	*/ 
	bool isSpecialSymbol(char ch);

	/** \brief Поиск соответствия между представлением байта символа в кодировке windows-1251 и его же представлением в кодировке utf-8.
	 * 
	 * @param oneByte байт в кодировке windows-1251.
	 * @return два байта, соответствующие oneByte в кодировке utf-8. Если соответствие не найдено (т.е. байта oneByte нет в таблице) возвращает <b>пробел</b>.
	 * 
	 * добавлено RealInvest Soft.\n
	 * 
	 * Пример:
	 * \code
	 * Вход (oneByte): "%E0" //байт из url, но в кодировке windows-1251.
	 * Выход: "%D0%B0" //соответствие байту oneByte, но в кодировке utf-8.
	 * \endcode
	 * 
	 * Таблица соответствий была взята из исходников сайта http://www.codenet.ru/services/urlencode-urldecode/ (javascript):
	 * \code
	 * rt['%E0']='%D0%B0';rt['%E1']='%D0%B1';rt['%E2']='%D0%B2';rt['%E3']='%D0%B3';rt['%E4']='%D0%B4';
	 * rt['%E5']='%D0%B5';rt['%B8']='%D1%91';rt['%E6']='%D0%B6';rt['%E7']='%D0%B7';rt['%E8']='%D0%B8';
	 * rt['%E9']='%D0%B9';rt['%EA']='%D0%BA';rt['%EB']='%D0%BB';rt['%EC']='%D0%BC';rt['%ED']='%D0%BD';
	 * rt['%EE']='%D0%BE';rt['%EF']='%D0%BF';rt['%F0']='%D1%80';rt['%F1']='%D1%81';rt['%F2']='%D1%82';
	 * rt['%F3']='%D1%83';rt['%F4']='%D1%84';rt['%F5']='%D1%85';rt['%F6']='%D1%86';rt['%F7']='%D1%87';
	 * rt['%F8']='%D1%88';rt['%F9']='%D1%89';rt['%FC']='%D1%8C';rt['%FB']='%D1%8B';rt['%FA']='%D1%8A';
	 * rt['%FD']='%D1%8D';rt['%FE']='%D1%8E';rt['%FF']='%D1%8F';rt['%C0']='%D0%90';rt['%C1']='%D0%91';
	 * rt['%C2']='%D0%92';rt['%C3']='%D0%93';rt['%C4']='%D0%94';rt['%C5']='%D0%95';rt['%A8']='%D0%81';
	 * rt['%C6']='%D0%96';rt['%C7']='%D0%97';rt['%C8']='%D0%98';rt['%C9']='%D0%99';rt['%CA']='%D0%9A';
	 * rt['%CB']='%D0%9B';rt['%CC']='%D0%9C';rt['%CD']='%D0%9D';rt['%CE']='%D0%9E';rt['%CF']='%D0%9F';
	 * rt['%D0']='%D0%A0';rt['%D1']='%D0%A1';rt['%D2']='%D0%A2';rt['%D3']='%D0%A3';rt['%D4']='%D0%A4';
	 * rt['%D5']='%D0%A5';rt['%D6']='%D0%A6';rt['%D7']='%D0%A7';rt['%D8']='%D0%A8';rt['%D9']='%D0%A9';
	 * rt['%DC']='%D0%AC';rt['%DB']='%D0%AB';rt['%DA']='%D0%AA';rt['%DD']='%D0%AD';rt['%DE']='%D0%AE';
	 * rt['%DF']='%D0%AF';
	 * \endcode
	*/
	string findUtf8Byte4Win1251Byte(const string &oneByte);
	
	/** \brief Преобразование процентного представления исходной строки из кодировки windows-1251 в кодировку utf-8.
	 * 
	 * @param str строка, являющаяся процентным представлением какой-либо исходной строки.
	 * @return процентное представление исходной строки, но в кодировке utf-8. Элементы, не найденные в таблице соответствия, будут заменены на пробел.
	 * 
	 * \warning Внутри метода кодировка не проверяется. Предполагается, что входящая строка - это процентное представление в кодировке windows-1251.
	 * 
	 * добавлено RealInvest Soft.\n
	 * Входная строка должна быть уже в готовом для преобразования виде.\n
	 * Пример:
	 * \code
	 * //исходная строка - "танк"
	 * вход: "%F2%E0%ED%EA" //процентное представление слова "танк" в кодировке windows-1251
	 * выход: "%D1%82%D0%B0%D0%BD%D0%BA" // процентное представление слова "танк" в кодировке utf-8
	 * \endcode
	 * 
	 * \see findUtf8Byte4Win1251Byte.
	 */
	string stringToUtf8(string &str);

	bool isUTF8(string &str);


	/**
	 * Рассматривался случай ТОЛЬКО для русского языка.
	 * В кодировке utf-8 все символы, окромя контрольных, начинаются на %D0 или %D1.
	 * После %D1 может идти только %8 или %91.
	 * После %D0 может идти: %B или %81 или %9 или %A.
	 * добавлено RealInvest Soft.
	 */
	bool isUTF8_2(const string &str);


	/** \brief Замещает все вхождения одной строки в другую.
	 ** 
	 * Источник - http://www.cppreference.com/wiki/ru/string/replace

	 * добавлено RealInvest Soft. 
	 */
	string& replaceAll(string& context, const string& from, const string& to);


};




#endif // URLPARSER_H
