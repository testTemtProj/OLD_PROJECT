#include <iostream>
#include <sstream>
#include <glog/logging.h>
#include "UrlParser.h"
#include "SearchEngines.h"


UrlParser::UrlParser(const string &url)
    : url_(url)
{
    parse();
	parseReferrer();//добавлено RealInvest Soft
}

/** Возвращает параметр par или пустую строку, если параметр не найден */
string UrlParser::param(const string &par) const
{
    map<string, string>::const_iterator it = params_.find(par);
    if (it != params_.end())
	return it->second;
    else
	return string();
}


/** Разбор URL-строки */
void UrlParser::parse()
{
	// Ищем первый вопросительный знак
	string::size_type pos = url_.find_first_of('?');
	if (pos == string::npos)
		pos = -1;

	while (pos < url_.size() || pos == (string::size_type)-1) {
		// Выделяем название параметра
		string::size_type end = url_.find_first_of('=', ++pos);
		if (end == string::npos) return;
		string param_name = url_.substr(pos, end - pos);
		pos = end;

		// Выделяем значение параметра
		end = url_.find_first_of('&', ++pos);
		if (end == string::npos)
			end = url_.size();
		string param_value = url_.substr(pos, end - pos);
		pos = end;

		params_[param_name] = percent_decode(param_value);
	}
}

/** Декодирует строку str из процентного представления */
std::string UrlParser::percent_decode(const std::string &str) const
{
    enum State {
	General,
	FirstPercentEncodedDigit,
	SecondPercentEncodedDigit
    } state = General;

    char first_char = '\0',
         second_char = '\0';
    std::stringstream result;

    for (std::string::const_iterator it = str.begin(); it != str.end(); it++) {
	switch (state) {

	case General:
	    if (*it != '%')
		result << *it;
	    else {
		state = FirstPercentEncodedDigit;
		first_char = second_char = '\0';
	    }
	    break;

	case FirstPercentEncodedDigit:
	    first_char = *it;
	    if (is_hex_digit(first_char)) {
		state = SecondPercentEncodedDigit;
	    } else {
		result << "%" << first_char;
		state = General;
	    }
	    break;

	case SecondPercentEncodedDigit:
	    second_char = *it;
	    if (is_hex_digit(second_char)) {

		result << char(
			(hex_digit_to_int(first_char) << 4) |
			 hex_digit_to_int(second_char));
		state = General;
	    } else {
		result << "%" << first_char << second_char;
		state = General;
	    }
	    break;
	}
    }
    return result.str();
}


/** Возвращает true, если \a hex_digit является шестнадцатиричным символом */
bool UrlParser::is_hex_digit(char hex_digit) const
{
    switch (hex_digit) {
    case '0':
    case '1':
    case '2':
    case '3':
    case '4':
    case '5':
    case '6':
    case '7':
    case '8':
    case '9':
    case 'a':
    case 'A':
    case 'b':
    case 'B':
    case 'c':
    case 'C':
    case 'd':
    case 'D':
    case 'e':
    case 'E':
    case 'f':
    case 'F':
	return true;
    default:
	return false;
    }
}

/** Возвращает число от 0 до 15, соответствующее hex_digit.

    Если hex_digit не является шестнадцатиричным символом, возвращат 0 */
int UrlParser::hex_digit_to_int(char hex_digit) const
{
    switch (hex_digit) {
    case '0':
	return 0;
    case '1':
	return 1;
    case '2':
	return 2;
    case '3':
	return 3;
    case '4':
	return 4;
    case '5':
	return 5;
    case '6':
	return 6;
    case '7':
	return 7;
    case '8':
	return 8;
    case '9':
	return 9;
    case 'a':
    case 'A':
	return 10;
    case 'b':
    case 'B':
	return 11;
    case 'c':
    case 'C':
	return 12;
    case 'd':
    case 'D':
	return 13;
    case 'e':
    case 'E':
	return 14;
    case 'f':
    case 'F':
	return 15;
    default:
	return 0;
    }
}


void UrlParser::parseReferrer()
{
	string referrer = param("referrer");

	bool isWin1251=false;
	if(referrer.find("windows-1251")!=string::npos) isWin1251=true;

	//LOG(INFO)<<"**********************referrer = "<<referrer<<endl;
	string keywordsParamsUrlReferrer;

	// Ищем первый вопросительный знак
	int posQuestionMark = referrer.find_first_of('?');
	//LOG(INFO)<<"**********************posQuestionMark (первый вопросительный знак) = "<<posQuestionMark<<endl;

	int posSearcherInReferrerURL;

	map<string,vector<string> >::iterator it = SearchEngineMapContainer::instance()->getMap().begin();
	for(; it != SearchEngineMapContainer::instance()->getMap().end() ;it++)
	{
		posSearcherInReferrerURL = referrer.find((*it).first);
		//LOG(INFO)<<"**********************engine = "<<(*it).first<<"  pos = "<<posSearcherInReferrerURL<<endl;
		if(posSearcherInReferrerURL != -1) break;
	}

	if(posSearcherInReferrerURL == -1 || posQuestionMark == -1 || posQuestionMark < posSearcherInReferrerURL )
	{
		//LOG(INFO) << "Не нашли поисковик или не нашли первый вопросительный знак или первый вопросительный знак находится перед поисковиком. В строку запроса записываем пустую строку.\n";
		//LOG(INFO)<<"**********************params_[userQueryString] = "<<endl;

		params_["userQueryString"] = "";
		return;
	}
	
	//ищем теперь значение вхождение подстроки с именем параметра для найденного поисковика
	int posKeywordsStart = 0;
	vector<string>::size_type i;
	for(i=0; i <(*it).second.size();i++)
	{
		//начиная с позиции знака '?' ищем вхождение подстроки с именем параметра
		posKeywordsStart = referrer.find((*it).second[i],posQuestionMark)/* +(*it).second[i].size()*/;
		//LOG(INFO)<<"********************** " << (*it).second[i] << " posKeywordsStart = "<<posKeywordsStart<<endl;

		if(posKeywordsStart != -1) break;//если нашли чего-то, выходим
	}
	//если чего-то нашли, вычисляем позицию начала самой строки.
	if (posKeywordsStart!=-1)
	{
		posKeywordsStart += (*it).second[i].size();
	}
	else{
		//если не нашли вхождения в строку параметра, отвечающего за значение строки запроса, то ставим строку запроса пустой и выходим.
		params_["userQueryString"] = "";
		return;
	}

	int posKeywordsEnd = referrer.find('&',posKeywordsStart);
	//LOG(INFO)<<"**********************posKeywordsEnd = "<<posKeywordsEnd <<endl;

	if(posKeywordsEnd == -1) posKeywordsEnd = referrer.size();

	//LOG(INFO)<<"**********************posKeywordsEnd = "<<posKeywordsEnd <<endl;

	keywordsParamsUrlReferrer = referrer.substr(posKeywordsStart, posKeywordsEnd - posKeywordsStart);
	//LOG(INFO)<<"**********************keywordsParamsUrlReferrer = "<<keywordsParamsUrlReferrer <<endl;
//----------------------------
	boost::to_upper(keywordsParamsUrlReferrer);


	LOG(INFO)<<"isWin1251 "<< isWin1251 <<endl;

	if(!isWin1251 && !isUTF8(keywordsParamsUrlReferrer)) isWin1251=true;

	LOG(INFO)<<"isWin1251 "<< isWin1251 <<endl;

	if(isWin1251)keywordsParamsUrlReferrer = stringToUtf8(keywordsParamsUrlReferrer);
	
	//LOG(INFO)<<"**********************keywordsParamsUrlReferrer = "<<keywordsParamsUrlReferrer <<endl;

	keywordsParamsUrlReferrer = percent_decode(keywordsParamsUrlReferrer);
	LOG(INFO)<<"**********************keywordsParamsUrlReferrer = "<<keywordsParamsUrlReferrer <<endl;
	
	//специальные символы замещаем на пробел
	replaceSymbols(keywordsParamsUrlReferrer);

	params_["userQueryString"] = keywordsParamsUrlReferrer;
    	//params_["userQueryString"] = "";
}

bool UrlParser::isUTF8(string &str)
{

	LOG(INFO)<<"str = "<<str;


			size_t lookHere = 0;
			size_t foundHere;
			int k1 = 0;
			while((foundHere = str.find("%", lookHere)) != string::npos)
			{
				
				lookHere = foundHere + 1;
				k1++;
				//LOG(INFO)<<"inside   k1 = "<<k1;

			}
			lookHere = 0;
			int k2 = 0;

			while((foundHere = str.find("%D0", lookHere)) != string::npos)
			{
				lookHere = foundHere + 1;
				k2++;

			}
			lookHere = 0;
			while((foundHere = str.find("%D1", lookHere)) != string::npos)
			{
				lookHere = foundHere + 1;
				k2++;

			}
	//LOG(INFO)<<"k1 = "<<k1;
	//LOG(INFO)<<"k2 = "<<k2;
	if (k2>k1/4) return true;
	else return false;

}


void UrlParser::replaceSymbols(string &str)
{
	for (size_t i=0; i<str.size(); i++)
	{
		if (isSpecialSymbol(str[i]))
		{
			str[i] = ' ';
		}		
	}	
}

bool UrlParser::isSpecialSymbol(char ch)
{
	if (ch=='+' || ch=='-' || ch=='&' || ch=='|' || ch=='!' || ch=='(' || ch==')' || ch=='{' || ch=='}' || ch=='[' || ch==']' || ch=='^' || ch=='"' || ch=='~' || ch=='*' || ch=='?' || ch==':' || ch==92)
	{
		return true;
	}
	
	return false;
}

string UrlParser::findUtf8Byte4Win1251Byte(const string &oneByte)
{
	if(oneByte=="%E0")return "%D0%B0";if(oneByte=="%E1")return "%D0%B1";if(oneByte=="%E2")return "%D0%B2";if(oneByte=="%E3")return "%D0%B3";if(oneByte=="%E4")return "%D0%B4";
	if(oneByte=="%E5")return "%D0%B5";if(oneByte=="%B8")return "%D1%91";if(oneByte=="%E6")return "%D0%B6";if(oneByte=="%E7")return "%D0%B7";if(oneByte=="%E8")return "%D0%B8";
	if(oneByte=="%E9")return "%D0%B9";if(oneByte=="%EA")return "%D0%BA";if(oneByte=="%EB")return "%D0%BB";if(oneByte=="%EC")return "%D0%BC";if(oneByte=="%ED")return "%D0%BD";
	if(oneByte=="%EE")return "%D0%BE";if(oneByte=="%EF")return "%D0%BF";if(oneByte=="%F0")return "%D1%80";if(oneByte=="%F1")return "%D1%81";if(oneByte=="%F2")return "%D1%82";
	if(oneByte=="%F3")return "%D1%83";if(oneByte=="%F4")return "%D1%84";if(oneByte=="%F5")return "%D1%85";if(oneByte=="%F6")return "%D1%86";if(oneByte=="%F7")return "%D1%87";
	if(oneByte=="%F8")return "%D1%88";if(oneByte=="%F9")return "%D1%89";if(oneByte=="%FC")return "%D1%8C";if(oneByte=="%FB")return "%D1%8B";if(oneByte=="%FA")return "%D1%8A";
	if(oneByte=="%FD")return "%D1%8D";if(oneByte=="%FE")return "%D1%8E";if(oneByte=="%FF")return "%D1%8F";if(oneByte=="%C0")return "%D0%90";if(oneByte=="%C1")return "%D0%91";
	if(oneByte=="%C2")return "%D0%92";if(oneByte=="%C3")return "%D0%93";if(oneByte=="%C4")return "%D0%94";if(oneByte=="%C5")return "%D0%95";if(oneByte=="%A8")return "%D0%81";
	if(oneByte=="%C6")return "%D0%96";if(oneByte=="%C7")return "%D0%97";if(oneByte=="%C8")return "%D0%98";if(oneByte=="%C9")return "%D0%99";if(oneByte=="%CA")return "%D0%9A";
	if(oneByte=="%CB")return "%D0%9B";if(oneByte=="%CC")return "%D0%9C";if(oneByte=="%CD")return "%D0%9D";if(oneByte=="%CE")return "%D0%9E";if(oneByte=="%CF")return "%D0%9F";
	if(oneByte=="%D0")return "%D0%A0";if(oneByte=="%D1")return "%D0%A1";if(oneByte=="%D2")return "%D0%A2";if(oneByte=="%D3")return "%D0%A3";if(oneByte=="%D4")return "%D0%A4";
	if(oneByte=="%D5")return "%D0%A5";if(oneByte=="%D6")return "%D0%A6";if(oneByte=="%D7")return "%D0%A7";if(oneByte=="%D8")return "%D0%A8";if(oneByte=="%D9")return "%D0%A9";
	if(oneByte=="%DC")return "%D0%AC";if(oneByte=="%DB")return "%D0%AB";if(oneByte=="%DA")return "%D0%AA";if(oneByte=="%DD")return "%D0%AD";if(oneByte=="%DE")return "%D0%AE";
	if(oneByte=="%DF")return "%D0%AF";

	return " ";
}

string UrlParser::stringToUtf8(string &str){
		//cout << "stringToUtf8 start.\n";
		//cout << "str.find(\"windows-1251\")=" << (str.find("windows-1251")) << "\n";
	//	if(str.find("windows-1251")!=string::npos)
	//	{
			//кодировка windows-1251. переводим в utf-8
			//в цикле проходим по строке. если встречаем '%', значит за ним должны быть ещё 2 символа, обозначающие в кодировке windows-1251 один байт. этот байт нам и нужно заменить на соответствующий ему байт в кодировке utf-8
			size_t lookHere = 0;
			size_t foundHere;
			string from, to;
			while((foundHere = str.find("%", lookHere)) != string::npos)
			{
				//нашли позицию '%'
				//нам нужно выделить последовательность из 3-х символов типа '%E1', foundHere смотрит на '%'
				from = str.substr(foundHere, 3);
				//cout << "from=" << from << "\n";
				//определяем, что это за байт и его замену
				to = findUtf8Byte4Win1251Byte(from);
				str.replace(foundHere, from.size(), to);
				lookHere = foundHere + to.size();
			}
	//	}
		//cout << "stringToUtf8 end.\n";
		return str;
	}
