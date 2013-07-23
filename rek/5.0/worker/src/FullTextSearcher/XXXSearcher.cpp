#include "XXXSearcher.h"



XXXSearcher::XXXSearcher(const string& dirNameOffer, const string& dirNameInformer)
{
	LOG(INFO) <<"Constructor XXXSearcher"<<endl;
	index_folder_offer_ = dirNameOffer;
	index_folder_informer_ = dirNameInformer;
	

}

XXXSearcher::~XXXSearcher()
{
	LOG(INFO) <<"Destructor XXXSearcher "<< endl;
}

void XXXSearcher::setLuceneIndexParams(string &folder_offer, string &folder_informer)
{
	index_folder_offer_ = folder_offer;
	index_folder_informer_ = folder_informer;
}

list<pair<pair<string, float>, pair<string, string>>> XXXSearcher::processWithFilter(const string& query, const string& filter, float weight/* =1.0 */, bool onPlace, const string& branch, const string& conformity)
{


	if (query.empty())
	{
		LOG(INFO) << "пустой запрос.";
		return list<pair<pair<string, float>, pair<string, string>>>();
	}

	PerFieldAnalyzerWrapper *analyzer;
	analyzer = new PerFieldAnalyzerWrapper(new WhitespaceAnalyzer());
	analyzer->addAnalyzer(_T("guid"), new WhitespaceAnalyzer());
	analyzer->addAnalyzer(_T("keywords"), new lucene::analysis::snowball::SnowballAnalyzer(_T("Russian")));
	analyzer->addAnalyzer(_T("minus_words"), new lucene::analysis::snowball::SnowballAnalyzer(_T("Russian")));
	analyzer->addAnalyzer(_T("informer_ids"), new WhitespaceAnalyzer());
	analyzer->addAnalyzer(_T("campaign_id"), new WhitespaceAnalyzer());


	IndexReader* reader = IndexReader::open(index_folder_offer_.c_str());


	list< pair < pair <string, float>, pair<string, string> > > result;
	try
	{
		IndexReader* newreader = reader->reopen();
		if ( newreader != reader ){
			_CLLDELETE(reader);
			reader = newreader;
		}
		IndexSearcher s(reader);
        //VLOG(2) << "query string  = " << query;
        //VLOG(2) << "Ветка и соответствие " << branch << " " << conformity;
		TCHAR *tquery=new TCHAR[query.size()];
		lucene_utf8towcs(tquery,query.c_str(),query.size());
		tquery = lucene_tcslwr(tquery);

//=======================================================================================
		//Query* q = QueryParser::parse(tquery,_T("keywords"),analyzer);
		QueryParser* qp = _CLNEW QueryParser(_T("keywords"),analyzer);
		Query* q = qp->parse(tquery);
		_CLDELETE(qp);
//=======================================================================================


		//LOG(INFO)<<"filter = "<<filter;

		TCHAR *tquery1 = NULL;
		Query* qTemp = NULL;
		if (!filter.empty())
		{
			tquery1=new TCHAR[filter.size()];
			lucene_utf8towcs(tquery1,filter.c_str(),filter.size());
			tquery1 = lucene_tcslwr(tquery1);
		//LOG(INFO)<<"tquery1 = "<< *tquery1;


		 	
//=======================================================================================
		//qTemp = QueryParser::parse(tquery1,_T("guid"),analyzer);

		QueryParser* qp1 = _CLNEW QueryParser(_T("guid"),analyzer);
		qTemp = qp1->parse(tquery1);
		_CLDELETE(qp1);
//=======================================================================================


		}
		//LOG(INFO)<<"filter = "<<filter;


		Sort * _sort = NULL;
		if (onPlace)  
		{
			_sort = _CLNEW Sort();
			_sort->setSort (_T("rating"), true);
		}
		QueryFilter * f = NULL;
		if (!filter.empty())
			f = _CLNEW QueryFilter(qTemp);
		
		Hits* h = s.search(q, f, _sort);

		//Hits* h = s.search(q);
		
		size_t k= h->length();
		if (k>400) k=400;
		//VLOG(2) << "Найдено = " << h->length();
		Document* doc;
		float g=1;
 		for (size_t i=0; i<k; i++)
 		{
 			doc = &h->doc(i);

			//In onPlace requests all koeff will be equal to first.
			if (onPlace)
 			{   
                if (branch == "L1")
                {
                    g = 10;
                }
                else
                {
                    g = 0;
                }
            }
			else
            {
                g = h->score(i);
            }
 			result.push_back(pair<pair<string, float>,pair<string, string>>(
                        (pair<string, float>(Misc::toString(doc->get(_T("guid"))), g*weight)),
                        (pair<string, string>(branch, conformity))));
 			//VLOG(3) <<"Результат "<< i << ". " << Misc::toString(doc->get(_T("guid"))) << " - "<< g << " - " << g*weight;
			doc->clear();
 		}

		
		_CLLDELETE(h);
		_CLLDELETE(q);
		_CLLDELETE(f);

		_CLLDELETE(qTemp);

		_CLDELETE(_sort);
		
		s.close();
		delete [] tquery;
		delete [] tquery1;

			
	}
	catch(CLuceneError &err)
	{
		LOG(ERROR) << "Ошибка при запросе к lucene: " << err.what();
		//VLOG(1) << "Ошибка при запросе к lucene: "<< err.what();
	}
	catch(...)
	{
		//VLOG(1) << "Непонятная ошибка";
		LOG(ERROR) << "Непонятная ошибка";
	}

	reader->close();
	_CLLDELETE(reader);
	
	delete analyzer;


	
	return result;
}



map< string, float > XXXSearcher::process2(const string& query)
{
//return map<string, float >();

//LOG(INFO) << "query for informer: "<<query;
	if (query.empty())
	{
		return map<string, float >();
	}


	PerFieldAnalyzerWrapper *analyzer;
	analyzer = new PerFieldAnalyzerWrapper(new WhitespaceAnalyzer());
	analyzer->addAnalyzer(_T("offer"), new WhitespaceAnalyzer());
	analyzer->addAnalyzer(_T("informer"), new WhitespaceAnalyzer());



	IndexReader* reader = IndexReader::open(index_folder_informer_.c_str());


	map< string, float > result;
	try
	{

		IndexReader* newreader = reader->reopen();

		if ( newreader != reader ){
			_CLLDELETE(reader);
			reader = newreader;
		}
		IndexSearcher s(reader);
        TCHAR *tquery = NULL;
		tquery=new TCHAR[query.size()];
		lucene_utf8towcs(tquery,query.c_str(),query.size());
		tquery = lucene_tcslwr(tquery);
        //string sString;
        //const int nLength = ::_tcslen(tquery);
        //for (int nIndex = 0 ; nIndex < nLength; nIndex++)
        //{
        //    sString += char(tquery[nIndex]);
        //}
        //LOG(INFO)<<" TF!!!!: "<<"   ="<<sString<<"=";
        //VLOG(1) << "Try to parse query....";
		
//=============================================================================
		//Query* q = QueryParser::parse(tquery,_T("offer"),analyzer);

		QueryParser* qp = _CLNEW QueryParser(_T("offer"),analyzer);
		Query* q = qp->parse(tquery);
		_CLDELETE(qp);
//============================================================================

        //VLOG(1) << "Completed!";
		Hits* h = s.search(q);
		
		size_t k = h->length();
        //VLOG(2) << "Найдено = " << h->length();
		
		Document* doc;
		float g=1;
 		for (size_t i=0; i<k; i++)
 		{
 			doc = &h->doc(i);
 			if (i==0) g = h->score(i);

 			result.insert(
 				pair<string, float>(
 					Misc::toString(doc->get(_T("offer"))),
 					atof(Misc::toString(doc->get(_T("rating"))).c_str())
					
 				)

 			);
 			//VLOG(10) <<"Resultat "<< i << ". " << Misc::toString(doc->get(_T("offer"))) << " - " <<Misc::toString(doc->get(_T("rating"))) << "\n";
 			doc->clear();
 		}

		
		_CLLDELETE(h);
		_CLLDELETE(q);
		//_CLDELETE(_sort);
		
		s.close();
		delete [] tquery;
			
	}
	catch(CLuceneError &err)
	{
		LOG(ERROR) << "Ошибка при запросе к lucene: " << err.what();
		//VLOG(1) << "Ошибка при запросе к lucene: "<< err.what();
	}
	catch(...)
	{
		//VLOG(1) << "Непонятная ошибка";
		LOG(ERROR) << "Непонятная ошибка";
	}

	reader->close();
	_CLLDELETE(reader);
	delete analyzer;


	return result;
}
