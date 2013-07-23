# coding: utf-8
from manager.model.baseModel import Base

class StaticPagesModel():
    
    static_pages_collection = Base.static_pages_collection
    

    @staticmethod
    def get_by_id(page_id):
        if page_id == 'new-page':
            return None
        try:
            page_id = int(page_id)
        except ValueError:
            print 'page_id must be int'
            return None

        return StaticPagesModel.static_pages_collection.find_one({'id': page_id})


    @staticmethod
    def get_by_slug(slug):
        return StaticPagesModel.static_pages_collection.find_one({'slug':slug})


    @staticmethod
    def get_children(root_page_id):
        return StaticPagesModel.static_pages_collection.find({'parent_id': int(root_page_id)})


    @staticmethod
    def save(data):
        # TODO сделать валидацию полей
        title = data.get('title', '')
        slug = data.get('slug', '')
        content = data.get('content', '')
        parent_id = int(data.get('parent_id', 0))

        page_id = data.get('page_id', None)

        page = StaticPagesModel.get_by_id(page_id=page_id)

        if page is None:
            page = {}
            page['id'] = StaticPagesModel.generate_new_id()

        page['title'] = title
        page['slug'] = slug
        page['content'] = content
        page['parent_id'] = parent_id

        if StaticPagesModel.static_pages_collection.find_one({'slug': page['slug'], 'id':{'$ne': page['id']}}):
            return False

        StaticPagesModel.static_pages_collection.save(page)
        
        return page['id']


    @staticmethod
    def remove(page_id):
        if page_id is None:
            return
        try:
            page_id = int(page_id)
        except ValueError:
            print "page_id must be integer"
            return

        StaticPagesModel.static_pages_collection.remove({'id':page_id})

        for page in StaticPagesModel.static_pages_collection.find({'parent_id': page_id}):
            StaticPagesModel.remove(page['id'])


    @staticmethod
    def generate_new_id():
        try:
            product = StaticPagesModel.static_pages_collection.find().sort('id', -1).limit(1)[0]
        except IndexError:
            return 0
        return int(product['id']) + 1
