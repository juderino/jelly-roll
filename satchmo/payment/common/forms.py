from django import newforms as forms
from django.conf import settings
from django.template import Context
from django.template import loader
from django.utils.translation import gettext_lazy as _
from satchmo.contact.models import Contact
from satchmo.discount.models import Discount
from satchmo.payment.paymentsettings import PaymentSettings
from satchmo.shop.models import Cart
from satchmo.shop.views.common import ContactInfoForm
from satchmo.shop.views.utils import CreditCard
import calendar
import datetime
import sys

class PaymentContactInfoForm(ContactInfoForm):
    
    _choices = PaymentSettings().as_selectpairs()
    if len(_choices) > 1:
        _paymentwidget = forms.RadioSelect
    else:
        _paymentwidget = forms.HiddenInput(attrs={'value' : _choices[0][0]})

    paymentmethod = forms.ChoiceField(label=_('Payment Method'), 
                                    choices=_choices,
                                    widget=_paymentwidget,
                                    required=True)

class PayShipForm(forms.Form):
    credit_type = forms.ChoiceField()
    credit_number = forms.CharField(max_length=20)
    month_expires = forms.ChoiceField(choices=[(month,month) for month in range(1,13)])
    year_expires = forms.ChoiceField()
    ccv = forms.IntegerField() # find min_length
    shipping = forms.ChoiceField(widget=forms.RadioSelect())
    discount = forms.CharField(max_length=30, required=False)

    def __init__(self, request, paymentmodule, *args, **kwargs):
        creditchoices = paymentmodule.CREDITCHOICES
        super(PayShipForm, self).__init__(*args, **kwargs)

        self.fields['credit_type'].choices = creditchoices

        year_now = datetime.date.today().year
        self.fields['year_expires'].choices = [(year, year) for year in range(year_now, year_now+5)]

        shipping_options = []
        tempCart = Cart.objects.get(id=request.session['cart'])
        tempContact = Contact.objects.get(id=request.session['custID'])

        for module in settings.SHIPPING_MODULES:
            #Create the list of information the user will see
            shipping_module = sys.modules[module]
            shipping_instance = shipping_module.Calc(tempCart, tempContact)
            if shipping_instance.valid():
                template = paymentmodule.lookup_template('shipping_options.html')
                t = loader.get_template(template)
                c = Context({
                    'amount': shipping_instance.cost(),
                    'description' : shipping_instance.description(),
                    'method' : shipping_instance.method(),
                    'expected_delivery' : shipping_instance.expectedDelivery() })
                shipping_options.append((shipping_instance.id, t.render(c)))
        self.fields['shipping'].choices = shipping_options        

    def clean_credit_number(self):
        """ Check if credit card is valid. """
        card = CreditCard(self.cleaned_data['credit_number'], self.cleaned_data['credit_type'])
        results, msg = card.verifyCardTypeandNumber()
        if not results:
            raise forms.ValidationError(msg)

    def clean_year_expires(self):
        """ Check if credit card has expired. """
        month = int(self.cleaned_data['month_expires'])
        year = int(self.cleaned_data['year_expires'])
        max_day = calendar.monthrange(year, month)[1]
        if datetime.date.today() > datetime.date(year=year, month=month, day=max_day):
            raise forms.ValidationError('Your card has expired.')

    def clean_discount(self):
        """ Check if discount exists. """
        data = self.cleaned_data['discount']
        if data:
            discount = Discount.objects.filter(code=data).filter(active=True)
            if discount.count() == 0:
                raise forms.ValidationError('Invalid discount.')
            valid, msg = discount[0].isValid()
            if not valid:
                raise forms.ValidationError(msg)
            # TODO: validate that it can work with these products
