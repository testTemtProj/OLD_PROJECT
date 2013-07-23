#ifndef INFORMERTEMPLATE_H
#define INFORMERTEMPLATE_H
#pragma once

#include <string>
#include <iostream>
#include <fstream>
using namespace std;

/**
	
	\brief Класс, отвечающий за хранение шаблонов для информеров.
	
	Хранятся 2 шаблона: для тизеров (существовавший) и для баннеров (новый).
	Отдельно хранится текст библиотеки swfobject, который считывается из файла swfobject.js.
    Он нужен для отображения баннера (для шаблона для баннеров), т.к. втраивание flash-баннера в страницу сделано с помощью этой библиотеки.
    При написании и отладке молуля использовалась версия SWFObject v2.2.
*/
class InformerTemplate
{
private:
	InformerTemplate(){}
protected:
	string frameTemplate;

	bool initFrameTemplate();
public:
	static InformerTemplate* instance()
	{
		static InformerTemplate *ob = new InformerTemplate;
		return ob;
	}

	bool init();

	/** Шаблон информера с тизерами со следующими подстановками (существовавший шаблон):

    %1%	    CSS
    %2%	    JSON для initads (предложения, которые должны показаться на первой
	        странице)
    %3%	    количество товаров на странице
    %4%	    ссылка на скрипт получения следующей порции предложений в json,
	        к ней будут добавляться дополнительные параметры.
	*/
	const string& getTemplate() {return frameTemplate;}
};

#endif // INFORMERTEMPLATE_H
