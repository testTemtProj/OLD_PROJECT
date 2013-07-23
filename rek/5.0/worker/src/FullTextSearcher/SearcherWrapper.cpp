#include"SearcherWrapper.h"

bool rigthOrderPairCompare(const pair< pair<string, float>, pair<string, string> >  &a, const pair< pair<string, float>, pair<string, string> >  &b)
{
	return a.first.second < b.first.second;
}

bool inverseOrderPairCompare(const pair< pair<string, float>, pair<string, string> >  &a, const pair< pair<string, float>, pair<string, string> >  &b)
{
	return a.first.second > b.first.second;
}
