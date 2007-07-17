from sets import Set
from django import http
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.db.models import Q
from django.utils import simplejson
from django.utils.translation import ugettext as _
from satchmo.product.models import Category, Option, Product, ConfigurableProduct, ProductVariation
from satchmo.shop.templatetags.currency_filter import moneyfmt
from satchmo.shop.views.utils import bad_or_missing

def serialize_options(config_product, selected_options=Set()):
    """
    Return a list of optiongroups and options for display to the customer.
    Only returns options that are actually used by members of this ConfigurableProduct.

    Return Value:
    [
    {
    name: 'group name',
    id: 'group id',
    items: [{ 
        name: 'opt name',
        value: 'opt value',
        price_change: 'opt price',
        selected: False,
        },{..}]
    },
    {..}
    ]

    Note: This doesn't handle the case where you have multiple options and
    some combinations aren't available. For example, you have option_groups
    color and size, and you have a yellow/large, a yellow/small, and a
    white/small, but you have no white/large - the customer will still see
    the options white and large.
    """
    d = {}
    for options in config_product.get_valid_options():
        for option in options:
            if not d.has_key(option.optionGroup_id):
                d[option.optionGroup.id] = {
                        'name': option.optionGroup.name,
                        'id': option.optionGroup.id,
                        'items': []
                        }
            if not option in d[option.optionGroup_id]['items']:
                d[option.optionGroup_id]['items'] += [option]
                option.selected = str(option) in selected_options
    return d.values()

def get_product(request, product_name, selected_options=Set()):
    try:
        product = Product.objects.get(active=True, name=product_name)
    except Product.DoesNotExist:
        return bad_or_missing(request, _('The product you have requested does not exist.'))

    p_types = product.get_subtypes()

    options = []
    
    if 'ProductVariation' in p_types:
        selected_options = product.productvariation.option_values
        #Display the ConfigurableProduct that this ProductVariation belongs to.
        product = product.productvariation.parent.product
        p_types = product.get_subtypes()

    if 'ConfigurableProduct' in p_types:
        options = serialize_options(product.configurableproduct, selected_options)

    return render_to_response('base_product.html', {'product': product, 'options': options}, RequestContext(request))

def optionset_from_post(configurableproduct, POST):
    chosenOptions = Set()
    for opt_grp in configurableproduct.option_group.all():
        if POST.has_key(str(opt_grp.id)):
            chosenOptions.add('%s-%s' % (opt_grp.id, POST[str(opt_grp.id)]))
    return chosenOptions

def get_price(request, product_name):
    quantity = 1

    try:
        product = Product.objects.get(active=True, name=product_name)
    except Product.DoesNotExist:
        return http.HttpResponseNotFound(simplejson.dumps(('','not available')), mimetype="text/javascript")

    prod_name = product.name

    if request.POST.has_key('quantity'):
        quantity = int(request.POST['quantity'])

    if 'ConfigurableProduct' in product.get_subtypes():
        cp = product.configurableproduct
        chosenOptions = optionset_from_post(cp, request.POST)
        pvp = cp.get_product_from_options(chosenOptions)

        if not pvp:
            return http.HttpResponse(simplejson.dumps(('','not available')), mimetype="text/javascript")
        prod_name = pvp.name
        price = moneyfmt(pvp.get_qty_price(quantity))
    else:
        price = moneyfmt(product.get_qty_price(quantity))

    if not price:
        return http.HttpResponse(simplejson.dumps(('','not available')), mimetype="text/javascript")

    return http.HttpResponse(simplejson.dumps((prod_name,price)), mimetype="text/javascript")


def do_search(request):
    keywords = request.POST.get('keywords', '').split(' ')
    keywords = filter(None, keywords)
    if not keywords:
        return render_to_response('search.html', RequestContext(request))

    categories = Category.objects
    products = Product.objects.filter(active=True)
    for keyword in keywords:
        categories = categories.filter(Q(name__icontains=keyword) | Q(meta__icontains=keyword) | Q(description__icontains=keyword))
        products = products.filter(Q(full_name__icontains=keyword) | Q(short_description__icontains=keyword) | Q(description__icontains=keyword) | Q(meta__icontains=keyword))
    list = []
    for category in categories:
        list.append(('Category', category.name, category.get_absolute_url()))
    for product in products:
        list.append(('Product', product.full_name, product.get_absolute_url()))

    return render_to_response('search.html', {'results': list}, RequestContext(request))


def getConfigurableProductOptions(request, id):
    cp = get_object_or_404(ConfigurableProduct, product__id=id)
    options = ''
    for og in cp.option_group.all():
        for opt in og.option_set.all():
            options += '<option value="%s">%s</option>' % (opt.id, str(opt))
    if not options:
        return '<option>No valid options found in "%s"</option>' % cp.product.name
    return http.HttpResponse(options, mimetype="text/html")
