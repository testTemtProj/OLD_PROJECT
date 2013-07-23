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


//void SearchFiles(const char* index)
list< pair<string, float> > XXXSearcher::process1(const string& query, float weight/* =1.0 */, bool onPlace)
{

// return list< pair<string, float> >();

	//LOG(INFO) << "process1 start.\n";

	if (query.empty())
	{
		//LOG(INFO) << "пустой запрос.\n";
		return list< pair<string, float> >();
	}
	
	PerFieldAnalyzerWrapper *analyzer;
	analyzer = new PerFieldAnalyzerWrapper(new WhitespaceAnalyzer());
	analyzer->addAnalyzer(_T("guid"), new WhitespaceAnalyzer());
	analyzer->addAnalyzer( _T("keywords"), new lucene::analysis::snowball::SnowballAnalyzer(_T("Russian")) );
	analyzer->addAnalyzer( _T("keywords_eng"), new lucene::analysis::snowball::SnowballAnalyzer(_T("english")) );
	analyzer->addAnalyzer( _T("minus_words"), new lucene::analysis::snowball::SnowballAnalyzer(_T("Russian")) );
	analyzer->addAnalyzer(_T("informer_ids"), new WhitespaceAnalyzer());
	analyzer->addAnalyzer(_T("campaign_id"), new WhitespaceAnalyzer());

	IndexReader* reader = NULL;
	try{
		reader = IndexReader::open(index_folder_offer_.c_str());
	}catch(CLuceneError &err)
	{
		LOG(INFO) << "Lucene opening index error:  " << err.what() << "\n";
	}


	list< pair<string, float> > result;
	try
	{
		IndexReader* newreader = reader->reopen();
		if ( newreader != reader ){
			_CLLDELETE(reader);
			reader = newreader;
		}
		IndexSearcher s(reader);

		TCHAR *tquery=new TCHAR[query.size()];
		lucene_utf8towcs(tquery,query.c_str(),query.size());
		tquery = lucene_tcslwr(tquery);

		Query* q = QueryParser::parse(tquery,_T("keywords"),analyzer);



		Sort * _sort = NULL;
		if (onPlace)  
		{
			_sort = _CLNEW Sort();
			_sort->setSort (_T("rating"), true);
		}

		Hits* h = s.search(q, NULL, _sort);

		//Hits* h = s.search(q);
		
		size_t k= h->length();
		if (k>300) k=300;
		//LOG(INFO) << "after search N=" << h->length() << "\n";
		Document* doc;
		float g=1;
 		for (size_t i=0; i<k; i++)
 		{
 			doc = &h->doc(i);

			//In onPlace requests all koeff will be equal to first.
			if (onPlace)
 				{if (i==0) g = h->score(i);}
			else g = h->score(i);

 			result.push_back(
 				pair<string, float>(
 					Misc::toString(doc->get(_T("guid"))),
 					g*weight
 				)
 			);
 			//LOG(INFO) <<"Resultat "<< i << ". " << Misc::toString(doc->get(_T("guid"))) << " - " << g*weight <<"   " << NumberTools::stringToLong(doc->get(_T("rating")))<<"\n";
 			//LOG(INFO) <<"Resultat "<< i << ". " << Misc::toString(doc->get(_T("guid"))) << " - " << g*weight <<"   " << Misc::toString(doc->get(_T("rating")))<<"\n";

			doc->clear();
 		}

		
		_CLLDELETE(h);
		_CLLDELETE(q);
		_CLDELETE(_sort);
		
		s.close();
		delete [] tquery;
			
	}
	catch(CLuceneError &err)
	{
		//LOG(INFO) << "Ошибка при запросе к lucene. " << err.what() << "\n";
		//LOG(ERROR) << "Ошибка при запросе к lucene. " << err.what() << "\n";
		LOG(INFO) << "Lucene query decoding error!!!";
		//LOG(ERROR) << "Ошибка при запросе к lucene. " << err.what() << "\n";
	}
	catch(...)
	{
		LOG(INFO) << "Непонятная ошибка.\n";
		LOG(ERROR) << "Непонятная ошибка.\n";
	}

	reader->close();
	_CLLDELETE(reader);
	
	delete analyzer;


	
	return result;
}

list< pair<string, float> > XXXSearcher::processWithFilter(const string& query, const string& filter, float weight/* =1.0 */, bool onPlace)
{

// return list< pair<string, float> >();

	if (query.empty())
	{
		//LOG(INFO) << "пустой запрос.\n";
		return list< pair<string, float> >();
	}
	//char index[30]="/var/www/index";

	PerFieldAnalyzerWrapper *analyzer;
	analyzer = new PerFieldAnalyzerWrapper(new WhitespaceAnalyzer());
	analyzer->addAnalyzer(_T("guid"), new WhitespaceAnalyzer());
	analyzer->addAnalyzer( _T("keywords"), new lucene::analysis::snowball::SnowballAnalyzer(_T("Russian")) );
	analyzer->addAnalyzer( _T("keywords_eng"), new lucene::analysis::snowball::SnowballAnalyzer(_T("english")) );
	analyzer->addAnalyzer( _T("minus_words"), new lucene::analysis::snowball::SnowballAnalyzer(_T("Russian")) );
	analyzer->addAnalyzer(_T("informer_ids"), new WhitespaceAnalyzer());
	analyzer->addAnalyzer(_T("campaign_id"), new WhitespaceAnalyzer());


	IndexReader* reader = IndexReader::open(index_folder_offer_.c_str());


	list< pair<string, float> > result;
	try
	{
		IndexReader* newreader = reader->reopen();
		if ( newreader != reader ){
			_CLLDELETE(reader);
			reader = newreader;
		}
		IndexSearcher s(reader);

		TCHAR *tquery=new TCHAR[query.size()];
		lucene_utf8towcs(tquery,query.c_str(),query.size());
		tquery = lucene_tcslwr(tquery);

		Query* q = QueryParser::parse(tquery,_T("keywords"),analyzer);
		//LOG(INFO)<<"filter = "<<filter;

		TCHAR *tquery1 = NULL;
		Query* qTemp = NULL;
		if (!filter.empty())
		{
			tquery1=new TCHAR[filter.size()];
			lucene_utf8towcs(tquery1,filter.c_str(),filter.size());
			tquery1 = lucene_tcslwr(tquery1);
		//LOG(INFO)<<"tquery1 = "<<tquery1;


		 	qTemp = QueryParser::parse(tquery1,_T("guid"),analyzer);
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
		if (k>300) k=300;
		//LOG(INFO) << "after search N=" << h->length() << "\n";
		Document* doc;
		float g=1;
 		for (size_t i=0; i<k; i++)
 		{
 			doc = &h->doc(i);

			//In onPlace requests all koeff will be equal to first.
			if (onPlace)
 				{if (i==0) g = h->score(i);}
			else g = h->score(i);

 			result.push_back(
 				pair<string, float>(
 					Misc::toString(doc->get(_T("guid"))),
 					g*weight
 				)
 			);
 			//LOG(INFO) <<"Resultat "<< i << ". " << Misc::toString(doc->get(_T("guid"))) << " - " << g*weight <<"   " << NumberTools::stringToLong(doc->get(_T("rating")))<<"\n";
 			//LOG(INFO) <<"Resultat "<< i << ". " << Misc::toString(doc->get(_T("guid"))) << " - " << g*weight <<"   " << Misc::toString(doc->get(_T("rating")))<<"\n";

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
		//LOG(INFO) << "Ошибка при запросе к lucene. " << err.what() << "\n";
		//LOG(ERROR) << "Ошибка при запросе к lucene. " << err.what() << "\n";
		LOG(INFO) << "Lucene query decoding error: "<< err.what() << "\n";

		//LOG(ERROR) << "Ошибка при запросе к lucene. " << err.what() << "\n";
	}
	catch(...)
	{
		LOG(INFO) << "Непонятная ошибка.\n";
		LOG(ERROR) << "Непонятная ошибка.\n";
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

		TCHAR *tquery=new TCHAR[query.size()];
		lucene_utf8towcs(tquery,query.c_str(),query.size());
		tquery = lucene_tcslwr(tquery);
LOG(INFO) << "Try to parse query....";
		Query* q = QueryParser::parse(tquery,_T("offer"),analyzer);
LOG(INFO) << "Completed!";
		Hits* h = s.search(q);
		
		size_t k= h->length();
		
		Document* doc;
		float g=1;
		LOG(INFO) <<"accodings count = "<<k;
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
 			//LOG(INFO) <<"Resultat "<< i << ". " << Misc::toString(doc->get(_T("offer"))) << " - " <<Misc::toString(doc->get(_T("rating"))) << "\n";
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

		LOG(INFO) << "Lucene query decoding error!!!"<< err.what() << "\n";
		//LOG(INFO) << "Lucene parser error!!!";

	}
	catch(...)
	{
		LOG(INFO) << "Непонятная ошибка.\n";
		LOG(ERROR) << "Непонятная ошибка.\n";
	}

	reader->close();
	_CLLDELETE(reader);
	delete analyzer;


	///эксперимен с RAMDirectory
	//dir->close();
	//delete dir;
	///

//	LOG(INFO) << "process1 end.\n";
//	
	return result;
}



const TCHAR* XXXSearcher::stop_words[] = {
	_T("или"),
	_T("vendor"),
	_T("able"),
	_T("about"),
	_T("above"),
	_T("abst"),
	_T("accordance"),
	_T("according"),
	_T("accordingly"),
	_T("across"),
	_T("act"),
	_T("actually"),
	_T("added"),
	_T("adj"),
	_T("adopted"),
	_T("afaik"),
	_T("afair"),
	_T("affected"),
	_T("affecting"),
	_T("affects"),
	_T("after"),
	_T("afterwards"),
	_T("again"),
	_T("against"),
	_T("ah"),
	_T("al"),
	_T("all"),
	_T("almost"),
	_T("alone"),
	_T("along"),
	_T("already"),
	_T("also"),
	_T("although"),
	_T("always"),
	_T("am"),
	_T("among"),
	_T("amongst"),
	_T("an"),
	_T("and"),
	_T("announce"),
	_T("another"),
	_T("any"),
	_T("anybody"),
	_T("anyhow"),
	_T("anymore"),
	_T("anyone"),
	_T("anything"),
	_T("anyway"),
	_T("anyways"),
	_T("anywhere"),
	_T("apparently"),
	_T("approximately"),
	_T("are"),
	_T("aren"),
	_T("arent"),
	_T("arise"),
	_T("around"),
	_T("as"),
	_T("aside"),
	_T("ask"),
	_T("asking"),
	_T("at"),
	_T("auth"),
	_T("available"),
	_T("away"),
	_T("awfully"),
	_T("back"),
	_T("be"),
	_T("became"),
	_T("because"),
	_T("become"),
	_T("becomes"),
	_T("becoming"),
	_T("been"),
	_T("before"),
	_T("beforehand"),
	_T("begin"),
	_T("beginning"),
	_T("beginnings"),
	_T("begins"),
	_T("behind"),
	_T("being"),
	_T("believe"),
	_T("below"),
	_T("beside"),
	_T("besides"),
	_T("between"),
	_T("beyond"),
	_T("biol"),
	_T("both"),
	_T("brief"),
	_T("briefly"),
	_T("but"),
	_T("by"),
	_T("ca"),
	_T("came"),
	_T("can"),
	_T("cannot"),
	_T("cant"),
	_T("cause"),
	_T("causes"),
	_T("certain"),
	_T("certainly"),
	_T("co"),
	_T("com"),
	_T("come"),
	_T("comes"),
	_T("contain"),
	_T("containing"),
	_T("contains"),
	_T("could"),
	_T("couldn"),
	_T("couldnt"),
	_T("date"),
	_T("did"),
	_T("didn"),
	_T("didnt"),
	_T("different"),
	_T("do"),
	_T("does"),
	_T("doesn"),
	_T("doesnt"),
	_T("doing"),
	_T("don"),
	_T("done"),
	_T("dont"),
	_T("down"),
	_T("downwards"),
	_T("due"),
	_T("during"),
	_T("each"),
	_T("ed"),
	_T("edu"),
	_T("eek"),
	_T("effect"),
	_T("eg"),
	_T("eight"),
	_T("eighty"),
	_T("either"),
	_T("else"),
	_T("elsewhere"),
	_T("end"),
	_T("ending"),
	_T("enough"),
	_T("especially"),
	_T("et"),
	_T("etc"),
	_T("even"),
	_T("ever"),
	_T("every"),
	_T("everybody"),
	_T("everyone"),
	_T("everything"),
	_T("everywhere"),
	_T("ex"),
	_T("except"),
	_T("far"),
	_T("few"),
	_T("ff"),
	_T("fifth"),
	_T("first"),
	_T("five"),
	_T("fix"),
	_T("followed"),
	_T("following"),
	_T("follows"),
	_T("for"),
	_T("former"),
	_T("formerly"),
	_T("forth"),
	_T("found"),
	_T("four"),
	_T("from"),
	_T("ftp"),
	_T("further"),
	_T("furthermore"),
	_T("gave"),
	_T("get"),
	_T("gets"),
	_T("getting"),
	_T("give"),
	_T("given"),
	_T("gives"),
	_T("giving"),
	_T("go"),
	_T("goes"),
	_T("gone"),
	_T("got"),
	_T("gotten"),
	_T("grin"),
	_T("had"),
	_T("hadn"),
	_T("happens"),
	_T("hardly"),
	_T("has"),
	_T("hasn"),
	_T("hasnt"),
	_T("have"),
	_T("haven"),
	_T("havent"),
	_T("having"),
	_T("he"),
	_T("hed"),
	_T("hence"),
	_T("her"),
	_T("here"),
	_T("hereafter"),
	_T("hereby"),
	_T("herein"),
	_T("heres"),
	_T("hereupon"),
	_T("hers"),
	_T("herself"),
	_T("hes"),
	_T("hi"),
	_T("hid"),
	_T("him"),
	_T("himself"),
	_T("his"),
	_T("hither"),
	_T("home"),
	_T("how"),
	_T("howbeit"),
	_T("however"),
	_T("http"),
	_T("hundred"),
	_T("id"),
	_T("ie"),
	_T("if"),
	_T("ill"),
	_T("im"),
	_T("imho"),
	_T("immediate"),
	_T("immediately"),
	_T("importance"),
	_T("important"),
	_T("in"),
	_T("inc"),
	_T("indeed"),
	_T("index"),
	_T("information"),
	_T("instead"),
	_T("into"),
	_T("invention"),
	_T("inward"),
	_T("is"),
	_T("isn"),
	_T("isnt"),
	_T("it"),
	_T("itd"),
	_T("itll"),
	_T("its"),
	_T("itself"),
	_T("ive"),
	_T("just"),
	_T("keep"),
	_T("keeps"),
	_T("kept"),
	_T("keys"),
	_T("kg"),
	_T("km"),
	_T("know"),
	_T("known"),
	_T("knows"),
	_T("largely"),
	_T("last"),
	_T("lately"),
	_T("later"),
	_T("latter"),
	_T("latterly"),
	_T("least"),
	_T("less"),
	_T("lest"),
	_T("let"),
	_T("lets"),
	_T("like"),
	_T("liked"),
	_T("likely"),
	_T("line"),
	_T("little"),
	_T("ll"),
	_T("look"),
	_T("looking"),
	_T("looks"),
	_T("ltd"),
	_T("made"),
	_T("mainly"),
	_T("make"),
	_T("makes"),
	_T("man"),
	_T("many"),
	_T("may"),
	_T("maybe"),
	_T("me"),
	_T("mean"),
	_T("means"),
	_T("meantime"),
	_T("meanwhile"),
	_T("merely"),
	_T("mg"),
	_T("might"),
	_T("million"),
	_T("miss"),
	_T("ml"),
	_T("more"),
	_T("moreover"),
	_T("most"),
	_T("mostly"),
	_T("mr"),
	_T("mrgreen"),
	_T("mrs"),
	_T("much"),
	_T("mug"),
	_T("must"),
	_T("my"),
	_T("myself"),
	_T("na"),
	_T("name"),
	_T("namely"),
	_T("nay"),
	_T("nd"),
	_T("near"),
	_T("nearly"),
	_T("necessarily"),
	_T("necessary"),
	_T("need"),
	_T("needs"),
	_T("neither"),
	_T("never"),
	_T("nevertheless"),
	_T("new"),
	_T("next"),
	_T("nine"),
	_T("ninety"),
	_T("no"),
	_T("nobody"),
	_T("non"),
	_T("none"),
	_T("nonetheless"),
	_T("noone"),
	_T("nor"),
	_T("normally"),
	_T("nos"),
	_T("not"),
	_T("noted"),
	_T("nothing"),
	_T("now"),
	_T("nowhere"),
	_T("obtain"),
	_T("obtained"),
	_T("obviously"),
	_T("of"),
	_T("off"),
	_T("often"),
	_T("oh"),
	_T("ok"),
	_T("okay"),
	_T("old"),
	_T("omitted"),
	_T("on"),
	_T("once"),
	_T("one"),
	_T("ones"),
	_T("only"),
	_T("onto"),
	_T("oops"),
	_T("or"),
	_T("ord"),
	_T("other"),
	_T("others"),
	_T("otherwise"),
	_T("ought"),
	_T("our"),
	_T("ours"),
	_T("ourselves"),
	_T("out"),
	_T("outside"),
	_T("over"),
	_T("overall"),
	_T("owing"),
	_T("own"),
	_T("page"),
	_T("pages"),
	_T("part"),
	_T("particular"),
	_T("particularly"),
	_T("past"),
	_T("per"),
	_T("perhaps"),
	_T("placed"),
	_T("please"),
	_T("plus"),
	_T("poorly"),
	_T("possible"),
	_T("possibly"),
	_T("potentially"),
	_T("pp"),
	_T("predominantly"),
	_T("present"),
	_T("previously"),
	_T("primarily"),
	_T("probably"),
	_T("promptly"),
	_T("proud"),
	_T("provides"),
	_T("put"),
	_T("que"),
	_T("quickly"),
	_T("quite"),
	_T("qv"),
	_T("ran"),
	_T("rather"),
	_T("razz"),
	_T("rd"),
	_T("re"),
	_T("readily"),
	_T("really"),
	_T("recent"),
	_T("recently"),
	_T("ref"),
	_T("refs"),
	_T("regarding"),
	_T("regardless"),
	_T("regards"),
	_T("related"),
	_T("relatively"),
	_T("research"),
	_T("respectively"),
	_T("resulted"),
	_T("resulting"),
	_T("results"),
	_T("right"),
	_T("roll"),
	_T("run"),
	_T("said"),
	_T("same"),
	_T("saw"),
	_T("say"),
	_T("saying"),
	_T("says"),
	_T("sec"),
	_T("section"),
	_T("see"),
	_T("seeing"),
	_T("seem"),
	_T("seemed"),
	_T("seeming"),
	_T("seems"),
	_T("seen"),
	_T("self"),
	_T("selves"),
	_T("sent"),
	_T("seven"),
	_T("several"),
	_T("shall"),
	_T("she"),
	_T("shed"),
	_T("shell"),
	_T("shes"),
	_T("should"),
	_T("shouldn"),
	_T("shouldnt"),
	_T("show"),
	_T("showed"),
	_T("shown"),
	_T("showns"),
	_T("shows"),
	_T("significant"),
	_T("significantly"),
	_T("similar"),
	_T("similarly"),
	_T("since"),
	_T("six"),
	_T("slightly"),
	_T("smile"),
	_T("so"),
	_T("some"),
	_T("somebody"),
	_T("somehow"),
	_T("someone"),
	_T("somethan"),
	_T("something"),
	_T("sometime"),
	_T("sometimes"),
	_T("somewhat"),
	_T("somewhere"),
	_T("soon"),
	_T("sorry"),
	_T("specifically"),
	_T("specified"),
	_T("specify"),
	_T("specifying"),
	_T("state"),
	_T("states"),
	_T("still"),
	_T("stop"),
	_T("strongly"),
	_T("sub"),
	_T("substantially"),
	_T("successfully"),
	_T("such"),
	_T("sufficiently"),
	_T("suggest"),
	_T("sup"),
	_T("sure"),
	_T("take"),
	_T("taken"),
	_T("taking"),
	_T("tell"),
	_T("tends"),
	_T("th"),
	_T("than"),
	_T("thank"),
	_T("thanks"),
	_T("thanx"),
	_T("that"),
	_T("thatll"),
	_T("thats"),
	_T("thatve"),
	_T("the"),
	_T("their"),
	_T("theirs"),
	_T("them"),
	_T("themselves"),
	_T("then"),
	_T("thence"),
	_T("there"),
	_T("thereafter"),
	_T("thereby"),
	_T("thered"),
	_T("therefore"),
	_T("therein"),
	_T("therell"),
	_T("thereof"),
	_T("therere"),
	_T("theres"),
	_T("thereto"),
	_T("thereupon"),
	_T("thereve"),
	_T("these"),
	_T("they"),
	_T("theyd"),
	_T("theyll"),
	_T("theyre"),
	_T("theyve"),
	_T("think"),
	_T("this"),
	_T("those"),
	_T("thou"),
	_T("though"),
	_T("thoughh"),
	_T("thousand"),
	_T("throug"),
	_T("through"),
	_T("throughout"),
	_T("thru"),
	_T("thus"),
	_T("til"),
	_T("tip"),
	_T("to"),
	_T("together"),
	_T("too"),
	_T("took"),
	_T("toward"),
	_T("towards"),
	_T("tried"),
	_T("tries"),
	_T("truly"),
	_T("try"),
	_T("trying"),
	_T("ts"),
	_T("twice"),
	_T("twisted"),
	_T("two"),
	_T("un"),
	_T("under"),
	_T("unfortunately"),
	_T("unless"),
	_T("unlike"),
	_T("unlikely"),
	_T("until"),
	_T("unto"),
	_T("up"),
	_T("upon"),
	_T("us"),
	_T("use"),
	_T("used"),
	_T("useful"),
	_T("usefully"),
	_T("usefulness"),
	_T("uses"),
	_T("using"),
	_T("usually"),
	_T("value"),
	_T("various"),
	_T("ve"),
	_T("very"),
	_T("via"),
	_T("viz"),
	_T("vol"),
	_T("vols"),
	_T("vs"),
	_T("want"),
	_T("wants"),
	_T("was"),
	_T("wasn"),
	_T("wasnt"),
	_T("way"),
	_T("we"),
	_T("web"),
	_T("wed"),
	_T("welcome"),
	_T("well"),
	_T("went"),
	_T("were"),
	_T("werent"),
	_T("weve"),
	_T("what"),
	_T("whatever"),
	_T("whatll"),
	_T("whats"),
	_T("whatve"),
	_T("when"),
	_T("whence"),
	_T("whenever"),
	_T("where"),
	_T("whereafter"),
	_T("whereas"),
	_T("whereby"),
	_T("wherein"),
	_T("wheres"),
	_T("whereupon"),
	_T("wherever"),
	_T("whether"),
	_T("which"),
	_T("while"),
	_T("whim"),
	_T("whither"),
	_T("who"),
	_T("whod"),
	_T("whoever"),
	_T("whole"),
	_T("wholl"),
	_T("whom"),
	_T("whomever"),
	_T("whos"),
	_T("whose"),
	_T("why"),
	_T("widely"),
	_T("will"),
	_T("willing"),
	_T("wink"),
	_T("wish"),
	_T("with"),
	_T("within"),
	_T("without"),
	_T("won"),
	_T("wont"),
	_T("words"),
	_T("world"),
	_T("would"),
	_T("wouldn"),
	_T("wouldnt"),
	_T("www"),
	_T("yes"),
	_T("yet"),
	_T("you"),
	_T("youd"),
	_T("youll"),
	_T("your"),
	_T("youre"),
	_T("yours"),
	_T("yourself"),
	_T("yourselves"),
	_T("youve"),
	_T("zeroах"),
	_T("без"),
	_T("бож"),
	_T("бол"),
	_T("больш"),
	_T("брат"),
	_T("буд"),
	_T("будет"),
	_T("будеш"),
	_T("будт"),
	_T("будут"),
	_T("будьт"),
	_T("буедт"),
	_T("бфть"),
	_T("бы"),
	_T("быв"),
	_T("был"),
	_T("быстр"),
	_T("быт"),
	_T("вам"),
	_T("вас"),
	_T("ваш"),
	_T("вдол"),
	_T("вдруг"),
	_T("вед"),
	_T("верн"),
	_T("ве"),
	_T("весьм"),
	_T("взял"),
	_T("видел"),
	_T("видн"),
	_T("виж"),
	_T("вмест"),
	_T("вне"),
	_T("вниз"),
	_T("внутр"),
	_T("во"),
	_T("вовс"),
	_T("вокруг"),
	_T("вот"),
	_T("вперед"),
	_T("впроч"),
	_T("времен"),
	_T("врем"),
	_T("все"),
	_T("всг"),
	_T("всегд"),
	_T("всег"),
	_T("всем"),
	_T("всех"),
	_T("всю"),
	_T("вся"),
	_T("вчер"),
	_T("вы"),
	_T("вышел"),
	_T("где"),
	_T("глаз"),
	_T("го"),
	_T("говор"),
	_T("да"),
	_T("дава"),
	_T("давн"),
	_T("даж"),
	_T("два"),
	_T("две"),
	_T("двер"),
	_T("двух"),
	_T("дел"),
	_T("дела"),
	_T("денег"),
	_T("ден"),
	_T("деньг"),
	_T("для"),
	_T("дни"),
	_T("дня"),
	_T("дням"),
	_T("до"),
	_T("довольн"),
	_T("долг"),
	_T("долж"),
	_T("должн"),
	_T("дом"),
	_T("достаточн"),
	_T("дык"),
	_T("дяд"),
	_T("дял"),
	_T("ев"),
	_T("ег"),
	_T("едв"),
	_T("ем"),
	_T("есл"),
	_T("ест"),
	_T("ещ"),
	_T("же"),
	_T("жизн"),
	_T("жит"),
	_T("за"),
	_T("завтр"),
	_T("замет"),
	_T("зач"),
	_T("зде"),
	_T("знает"),
	_T("знаеш"),
	_T("знал"),
	_T("знат"),
	_T("знач"),
	_T("зна"),
	_T("иб"),
	_T("ива"),
	_T("иванович"),
	_T("иваныч"),
	_T("из"),
	_T("ил"),
	_T("им"),
	_T("имен"),
	_T("имет"),
	_T("имх"),
	_T("иногд"),
	_T("их"),
	_T("ка"),
	_T("кажд"),
	_T("кажет"),
	_T("каза"),
	_T("как"),
	_T("какж"),
	_T("кем"),
	_T("княз"),
	_T("ко"),
	_T("когд"),
	_T("ког"),
	_T("ком"),
	_T("комнат"),
	_T("конечн"),
	_T("коотр"),
	_T("котор"),
	_T("которй"),
	_T("крайн"),
	_T("кром"),
	_T("кто"),
	_T("куд"),
	_T("лет"),
	_T("ли"),
	_T("либ"),
	_T("лиц"),
	_T("лиш"),
	_T("лучш"),
	_T("любв"),
	_T("любл"),
	_T("любов"),
	_T("люд"),
	_T("мал"),
	_T("мат"),
	_T("мегалол"),
	_T("межд"),
	_T("мен"),
	_T("мер"),
	_T("мест"),
	_T("минут"),
	_T("мит"),
	_T("мля"),
	_T("мне"),
	_T("мног"),
	_T("мно"),
	_T("мо"),
	_T("мог"),
	_T("могл"),
	_T("могут"),
	_T("мож"),
	_T("может"),
	_T("можеш"),
	_T("можн"),
	_T("молод"),
	_T("моч"),
	_T("мы"),
	_T("мысл"),
	_T("нем"),
	_T("на"),
	_T("навсегд"),
	_T("над"),
	_T("назад"),
	_T("наконец"),
	_T("нам"),
	_T("например"),
	_T("нарочн"),
	_T("нас"),
	_T("нах"),
	_T("нача"),
	_T("наш"),
	_T("не"),
	_T("нег"),
	_T("нельз"),
	_T("немн"),
	_T("непремен"),
	_T("нескольк"),
	_T("несмотр"),
	_T("нет"),
	_T("неужел"),
	_T("неч"),
	_T("ни"),
	_T("нибуд"),
	_T("никак"),
	_T("никогд"),
	_T("никт"),
	_T("ним"),
	_T("них"),
	_T("нич"),
	_T("но"),
	_T("ног"),
	_T("ноч"),
	_T("ну"),
	_T("нужн"),
	_T("нэ"),
	_T("об"),
	_T("облом"),
	_T("образ"),
	_T("один"),
	_T("одн"),
	_T("однак"),
	_T("окол"),
	_T("омч"),
	_T("он"),
	_T("опя"),
	_T("особен"),
	_T("от"),
	_T("ответ"),
	_T("отвеча"),
	_T("отец"),
	_T("отч"),
	_T("очен"),
	_T("перв"),
	_T("перед"),
	_T("петр"),
	_T("письм"),
	_T("по"),
	_T("под"),
	_T("подума"),
	_T("пожал"),
	_T("позвольт"),
	_T("пок"),
	_T("помн"),
	_T("понима"),
	_T("пор"),
	_T("посл"),
	_T("пот"),
	_T("поч"),
	_T("почт"),
	_T("пошел"),
	_T("пр"),
	_T("правд"),
	_T("прав"),
	_T("пред"),
	_T("прежд"),
	_T("при"),
	_T("пришел"),
	_T("про"),
	_T("проговор"),
	_T("продолжа"),
	_T("прост"),
	_T("прям"),
	_T("пуст"),
	_T("пят"),
	_T("раз"),
	_T("разв"),
	_T("разумеет"),
	_T("рубл"),
	_T("рук"),
	_T("сам"),
	_T("свет"),
	_T("свйо"),
	_T("сво"),
	_T("сдела"),
	_T("себ"),
	_T("сегодн"),
	_T("сейчас"),
	_T("сердц"),
	_T("сих"),
	_T("скаж"),
	_T("сказа"),
	_T("скольк"),
	_T("скор"),
	_T("слишк"),
	_T("слов"),
	_T("случа"),
	_T("смотрел"),
	_T("снов"),
	_T("со"),
	_T("соб"),
	_T("совершен"),
	_T("совс"),
	_T("спрос"),
	_T("стал"),
	_T("старик"),
	_T("сто"),
	_T("сторон"),
	_T("стоя"),
	_T("сут"),
	_T("сюд"),
	_T("та"),
	_T("тагд"),
	_T("так"),
	_T("такж"),
	_T("такй"),
	_T("там"),
	_T("те"),
	_T("теб"),
	_T("тем"),
	_T("тепер"),
	_T("тех"),
	_T("тих"),
	_T("то"),
	_T("тоб"),
	_T("тогд"),
	_T("тог"),
	_T("тож"),
	_T("тольк"),
	_T("том"),
	_T("тот"),
	_T("тотчас"),
	_T("точн"),
	_T("тоьлк"),
	_T("три"),
	_T("ту"),
	_T("тут"),
	_T("ты"),
	_T("уж"),
	_T("ужасн"),
	_T("ум"),
	_T("упс"),
	_T("ух"),
	_T("хорош"),
	_T("хот"),
	_T("хотел"),
	_T("хоч"),
	_T("чем"),
	_T("част"),
	_T("чег"),
	_T("че"),
	_T("через"),
	_T("чт"),
	_T("что"),
	_T("чтоб"),
	_T("чут"),
	_T("чье"),
	_T("чья"),
	_T("шта"),
	_T("ыбт"),
	_T("э"),
	_T("эт"),
	_T("этот")
};
