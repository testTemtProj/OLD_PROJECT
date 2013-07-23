
def find_category_in_array(cats, id):
    for cat in cats:
        if cat['ID'] == id:
            return cat

def get_childrens(cats, id):
    categories = []
    for cat in cats:
        try:
            if cat['ParentID'] == id:
                categories.append(cat)
        except:
            pass
    return categories
