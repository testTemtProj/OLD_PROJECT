# coding: utf-8

from rynok.model.baseModel import Base
from rynok.model.categoriesModel import CategoriesModel
from rynok.model.item.referenceItem import ReferenceItem

class ReferenceModel(object):
    """
    Шаблон модели эталонов
    """

    reference_collection = Base.products_collection

    @staticmethod
    def get_reference(**kwargs):
        """
        Входные параметры:
        where={'КЛЮЧ':'ЗНАЧЕНИЕ'}
        by='ПОЛЕ'
        direction='НАПРАВЛЕНИЕ: asc | desc'
        limit='КОЛИЧЕСТВО'
        page='СТРАНИЦА'
        perPage='КОЛИЧЕСТВО НА СТРАНИЦЕ'
        one='True | False'
        get_cursor='True | False' - взять курсор
        """

        references = ReferenceModel.reference_collection
        if len(kwargs) == 0:
            return ReferenceItem(references.find_one(slave_okay=True))

        if kwargs.has_key('where') and kwargs.has_key('one') == True:
            return ReferenceItem(references.find_one(kwargs['where'], slave_okay=True))

        if kwargs.has_key('where'):
            references = references.find(kwargs['where'], slave_okay=True)
        else:
            references = references.find(slave_okay=True)

        if kwargs.has_key('by'):
            if not kwargs.has_key('direction'):
                direction = asc
            else:
                if kwargs['direction'] == 'asc':
                    direction = 1
                else:
                    direction = -1
            references = references.sort([(kwargs['by'], direction), ('images', -1)])

        if kwargs.has_key('skip'):
            references = references.skip(int(kwargs['skip']))

        if kwargs.has_key('limit'):
            references = references.limit(kwargs['limit'])

        if kwargs.has_key('page'):
            page = int(kwargs['page'])
            referencesPerPage = 10 if not kwargs.has_key('perPage') else int(kwargs['perPage'])
            references = references.skip((page) * referencesPerPage).limit(referencesPerPage)

        if kwargs.has_key('get_cursor'):
            if kwargs['get_cursor'] == True:
                return references

        referencesArray = []
        for reference in references:
            try:
                reference['redirect'] = reference['url']
                referencesArray.append(ReferenceItem(reference))
            except:
                pass

        return referencesArray

    @staticmethod
    def get_by_id(id):
        return ReferenceModel.get_reference(where={'id': id}, one=True)

    @staticmethod
    def get_by_title(title):
        re_title = re.compile(title, re.IGNORECASE)
        return ReferenceModel.get_reference(where={'title': re_title}, by="weight", page=1)

    @staticmethod
    def get_by_category_id(category_id):
        return ReferenceModel.get_reference(where={'categoryId': int(category_id)})

    @staticmethod
    def get_category_total(category_id):
        references = ReferenceModel.reference_collection
        return references.find({"categoryId": int(category_id)}, slave_okay=True).count()

    @staticmethod
    def get_by_market_id(market_id):
        return ReferenceModel.get_reference(where={'shopId': int(market_id)})

    @staticmethod
    def get_by_vendor_id(vendor_id):
        return ReferenceModel.get_reference(where={'vendor': int(vendor_id)})

    @staticmethod
    def get_max_price(query, currency):
        if not isinstance(query, dict):
            raise Exception('query must be dict')

        refs = ReferenceModel.get_reference(where=query, by=currency, direction='desc', limit=1)

        if not len(refs):
            return 0

        # TODO сделать в итеме has_key
        try:
            return int(refs[0][currency])
        except TypeError:
            return 0

    @staticmethod
    def get_count(query):
        references = ReferenceModel.reference_collection

        # HACK for currency nokey
        #        for currency in ['UAH', 'USD', 'RUB']:
        #            if query.has_key(currency):
        #                del query[currency]

        return references.find(query, slave_okay=True).count()

    @staticmethod
    def group(keys, condition, initial={}, reduce='function(obj, prev){}'):
        if not isinstance(keys, dict):
            raise Exception('keys must be dict')
        if not isinstance(condition, dict):
            raise Exception('condition must be dict')
        return ReferenceModel.reference_collection.group(key=keys, condition=condition, initial=initial, reduce=reduce)

    @staticmethod 
    def get_popular_products(categories, products_per_category):
        if 'getPopularProducts' not in Base.connection.system_js.list():
            code = """
                function (cats, per_cat) {
                    var cats = db.Category.find({'count':{$gt:0}, 'isLeaf':true}).sort({'popularity': -1}).limit(cats);
                    var result = [];
                    for(i=0; i<cats.length(); i++){
                        var products = db.Products.find({'categoryId' : cats[i]['ID'], 'images':{"$exists": true, "$ne":"None"}}).sort({'popularity':-1});
                        for(j=0; j<per_cat; j++){
                            if(!products.hasNext()){
                                break;
                            }
                            var product = products.next();
                            if(cats[i]['AlternativeTitle'])
                                product['category'] = cats[i]['AlternativeTitle'];
                            else
                                product['category'] = cats[i]['Name'];
                            product['counter'] = i.toString();
                            result.push(product);
                        }
                    }
                    return result;
                }
            """
            Base.connection.system_js.getPopularProducts = code
    
        result = []
        
        for product in Base.connection.system_js.getPopularProducts(categories, products_per_category):
            result.append(ReferenceItem(product))
            
        return result


    @staticmethod
    def get_new_products(limit):
        #TODO сделать map_reduce
        if 'getNewProducts' not in Base.connection.system_js.list():
            code = """
                function (limit){
                    var products = db.Products.find({'images':{"$exists":true, "$ne":"None"}}).sort({"$natural":-1});
                    var result = [];
                    var last_category_id = 0;
                    var counter = 0;
                    for(i=0; i<100000; i++){
                        if(!products.hasNext() || counter > limit){
                            break;
                        }
                        var product = products.next();
                        if(product['categoryId'] != last_category_id){
                            result.push(product);
                            counter++;
                            last_category_id = product['categoryId'];
                            continue;
                        }
                    }
                    return result;
                }
            """

            Base.connection.system_js.getNewProducts = code

        result = []
        
        for product in Base.connection.system_js.getNewProducts(limit):
            result.append(ReferenceItem(product))
            
        return result
        
