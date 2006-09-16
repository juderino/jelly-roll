from django.shortcuts import render_to_response
from django import http
from satchmo.shop.models import Cart, CartItem, Config
from satchmo.product.models import Item, Category, OptionItem
from sets import Set
from django.template import RequestContext, Context
from django.conf import settings
from satchmo.shop.views.utils import bad_or_missing

def display(request):
    #Show the items in the cart
    cart_list = []
    total = 0
    if request.session.get('cart',False):
        tempCart = Cart.objects.get(id=request.session['cart'])
        total = tempCart.total
        return render_to_response('base_cart.html', {'all_items': tempCart.cartitem_set.all(),
                                                       'total': total},
                                                        RequestContext(request))
    else:
        return render_to_response('base_cart.html', {'all_items' : [],
                                                        'total':total},
                                                        RequestContext(request))

def add(request, id):
    #Todo: Error checking for invalid combos
    #Add an item to the session/cart
    chosenOptions = Set()
    price_delta = 0
    try:
        product = Item.objects.get(pk=id)
    except Item.DoesNotExist:
        return bad_or_missing(request, 'The product you have requested does '
                'not exist.')
    for option in product.option_group.all():
        chosenOptions.add('%s-%s' % (option.id,request.POST[str(option.id)]))
        #print '%s-%s' % (option.id,request.POST[str(option.id)])
    try:
        quantity = int(request.POST['quantity'])
    except ValueError:
        return render_to_response('base_product.html', {
            'item': product,
            'error_message': "Please enter a whole number"},
             RequestContext(request))
    if quantity < 0:
        return render_to_response('base_product.html', {
            'item': product,
            'error_message': "Negative numbers can not be entered"},
             RequestContext(request))
    #Now get the appropriate sub_item
    chosenItem = product.get_sub_item(chosenOptions)
    #If we get a None, then there is not a valid subitem so tell the user
    if not chosenItem:
        return render_to_response('base_product.html', {
            'item': product,
            'error_message': "Sorry, this choice is not available."},
             RequestContext(request))
                
    if request.session.get('cart',False):
        tempCart = Cart.objects.get(id=request.session['cart'])
    else:
        tempCart = Cart()
    tempCart.save() #need to make sure there's an id
    tempCart.add_item(chosenItem, number_added=quantity)
    request.session['cart'] = tempCart.id

    return http.HttpResponseRedirect('%s/cart' % (settings.SHOP_BASE))

def remove(request, id):
    tempCart = Cart.objects.get(id=request.session['cart'])
    if request.has_key('quantity'):
        quantity = request.POST['quantity']
    else:
        quantity = 9999
    tempCart.remove_item(id, quantity)
    return http.HttpResponseRedirect('%s/cart' % (settings.SHOP_BASE))