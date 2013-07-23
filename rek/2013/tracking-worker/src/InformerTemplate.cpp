#include "InformerTemplate.h"

/** Шаблон информера с тизерами со следующими подстановками (существовавший шаблон):

    %1%	    CSS
    %2%	    JSON для initads (предложения, которые должны показаться на первой
	    странице)
    %3%	    количество товаров на странице
    %4%	    ссылка на скрипт получения следующей порции предложений в json,
	    к ней будут добавляться дополнительные параметры.
*/
bool InformerTemplate::initFrameTemplate()
{
	if (frameTemplate!="")
	{
		return true;
	}

	frameTemplate = 
		"<html><head>"
		"<META http-equiv=\"Content-Type\" content=\"text/html; charset=utf-8\"><meta name=\"robots\" content=\"nofollow\" />\n"
		"<style type=\"text/css\">html, body {padding: 0; margin: 0; border: 0;}</style>\n"
		"</head> \n"
		"<body> \n"
		"</body>\n"
		"</html>\n";
	return true;
}



bool InformerTemplate::init()
{
	return initFrameTemplate();
}
