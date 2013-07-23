#include"SearcherWrapper.h"

bool rigthOrderPairCompare(const pair<string, float>  &a, const pair<string, float>  &b)
{
	return a.second < b.second;
}

bool inverseOrderPairCompare(const pair<string, float>  &a, const pair<string, float>  &b)
{
	return a.second > b.second;
}