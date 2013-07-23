#ifndef GUARANTEEDDISPLAYTEMPLATE_H
#define GUARANTEEDDISPLAYTEMPLATE_H

#include <string>

/** Шаблон информера со следующими подстановками:

    %1%	    CSS
    %2%	    JSON для initads (предложения, которые должны показаться на первой
	    странице)
    %3%	    количество товаров на странице
    %4%	    ссылка на скрипт получения следующей порции предложений в json,
	    к ней будут добавляться дополнительные параметры.
*/
std::string GuaranteedDisplayTemplate()
{
    static std::string templ = 
        "<!DOCTYPE html PUBLIC '-//W3C//DTD XHTML 1.0 Strict//EN' 'http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd'>\n"
        "<html xmlns='http://www.w3.org/1999/xhtml' style='height: 100%%;'>\n"
        "    <head>\n"
        "        <meta http-equiv='Content-Type' content='text/html; charset=utf-8' />\n"
        "    </head>\n"
        "    <body style='margin:0 auto; display:table; height:100%%;'>\n"
        "        <div style='vertical-align:middle; display:table-cell;'>\n"
        "            <img src='data:image/gif;base64,R0lGODlhEAAQAPIAAP///wAAAMLCwkJCQgAAAGJiYoKCgpKSkiH/C05FVFNDQVBFMi4wAwEAAAAh/hpDcmVhdGVkIHdpdGggYWpheGxvYWQuaW5mbwAh+QQJCgAAACwAAAAAEAAQAAADMwi63P4wyklrE2MIOggZnAdOmGYJRbExwroUmcG2LmDEwnHQLVsYOd2mBzkYDAdKa+dIAAAh+QQJCgAAACwAAAAAEAAQAAADNAi63P5OjCEgG4QMu7DmikRxQlFUYDEZIGBMRVsaqHwctXXf7WEYB4Ag1xjihkMZsiUkKhIAIfkECQoAAAAsAAAAABAAEAAAAzYIujIjK8pByJDMlFYvBoVjHA70GU7xSUJhmKtwHPAKzLO9HMaoKwJZ7Rf8AYPDDzKpZBqfvwQAIfkECQoAAAAsAAAAABAAEAAAAzMIumIlK8oyhpHsnFZfhYumCYUhDAQxRIdhHBGqRoKw0R8DYlJd8z0fMDgsGo/IpHI5TAAAIfkECQoAAAAsAAAAABAAEAAAAzIIunInK0rnZBTwGPNMgQwmdsNgXGJUlIWEuR5oWUIpz8pAEAMe6TwfwyYsGo/IpFKSAAAh+QQJCgAAACwAAAAAEAAQAAADMwi6IMKQORfjdOe82p4wGccc4CEuQradylesojEMBgsUc2G7sDX3lQGBMLAJibufbSlKAAAh+QQJCgAAACwAAAAAEAAQAAADMgi63P7wCRHZnFVdmgHu2nFwlWCI3WGc3TSWhUFGxTAUkGCbtgENBMJAEJsxgMLWzpEAACH5BAkKAAAALAAAAAAQABAAAAMyCLrc/jDKSatlQtScKdceCAjDII7HcQ4EMTCpyrCuUBjCYRgHVtqlAiB1YhiCnlsRkAAAOwAAAAAAAAAAAA=='/>\n"
        "        </div>\n"
        "    </body>\n"
        "</html>\n";
        return templ;
    }



#endif // GUARANTEEDDISPLAYTEMPLATE_H
