from django import template
from satchmo import caching
from satchmo.product.models import Product
from satchmo.shop.templatetags import get_filter_args
from satchmo.product.queries import bestsellers
from satchmo.product.views import display_featured

register = template.Library()


def is_producttype(product, ptype):
    """Returns True if product is ptype"""
    if ptype in product.get_subtypes():
        return True
    else:
        return False

register.filter('is_producttype', is_producttype)


def product_count(category, args=''):
    """Get a count of products for the base object.

    If `category` is None, then count everything.
    If it is a `Category` object then count everything in the category and subcategories.
    """
    args, kwargs = get_filter_args(args, boolargs=('variations'))
    variations = kwargs.get('variations', False)
    try:
        ct = caching.cache_get('product_count', category, variations)
    except caching.NotCachedError:
        if not category:
            ct = Product.objects.active_by_site(variations=variations).count()
        else:
            ct = category.active_products(include_children=True, variations=variations).count()

        caching.cache_set('product_count', category, args, value=ct)
    return ct

register.filter('product_count', product_count)


def product_images(product, args=""):
    args, kwargs = get_filter_args(
        args,
        keywords=('include_main', 'maximum'),
        boolargs=('include_main'),
        intargs=('maximum'),
        stripquotes=True)

    q = product.productimage_set
    if kwargs.get('include_main', True):
        q = q.all()
    else:
        main = product.main_image
        q = q.exclude(id=main.id)

    maximum = kwargs.get('maximum', -1)
    if maximum > -1:
        q = list(q)[:maximum]

    return q

register.filter('product_images', product_images)


def smart_attr(product, key):
    """
    Run the smart_attr function on the spec'd product
    """
    return product.smart_attr(key)

register.filter('smart_attr', smart_attr)


def product_sort_by_price(products):
    """
    Sort a product list by unit price

    Example::

        {% for product in products|product_sort_by_price %}
    """

    if products:
        fast = [(product.unit_price, product) for product in products]
        fast.sort()
        return zip(*fast)[1]

register.filter('product_sort_by_price', product_sort_by_price)


@register.inclusion_tag('bestsellers.html')
def show_bestsellers(limit=5):
    ''' Renders best sellers list '''
    products = bestsellers(limit)
    return {"bestsellers": products}


@register.inclusion_tag('featured.html')
def show_featured(limit=1, random=True):
    ''' Renders best sellers list '''
    products = display_featured(limit, random)
    return {"featured": products}


@register.inclusion_tag('product/quick_product.html')
def quick_product(product, show_wishlist=True):
    ''' Renders a product in a way that is usefull for a list '''
    if show_wishlist == "False":
        show_wishlist = False

    return {
        "product": product,
        "show_wishlist": show_wishlist
    }


@register.inclusion_tag('product/full_product.html')
def full_product(product):
    ''' Renders a product in a way that is usefull for the product detail page '''
    return {"product": product}
