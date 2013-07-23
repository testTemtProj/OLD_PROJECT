#ifndef INFORMERTEMPLATE_H
#define INFORMERTEMPLATE_H
#pragma once

#include <string>
#include <iostream>
#include <fstream>
using namespace std;

class FrameTemplate
{
private:
	FrameTemplate(){}
protected:
	string frameTemplate;
	bool initFrameTemplate();
public:
	static FrameTemplate* instance()
	{
		static FrameTemplate *ob = new FrameTemplate;
		return ob;
	}
	bool init();
	const string& getFrameTemplate() {return frameTemplate;}
};

#endif // INFORMERTEMPLATE_H
