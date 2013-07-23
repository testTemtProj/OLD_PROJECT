from manager.model.item.productItem import ProductItem

def test_ProductItem():
    obj = {'key':'value'}
    product_item = ProductItem(obj)
    assert product_item.key == 'value'
