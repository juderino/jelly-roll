"""
Stores Customer and Order information
"""

from django.db import models
from django.contrib.auth.models import User 
from satchmo.product.models import SubItem
from satchmo.shipping.modules import activeModules
#from satchmo.shop.models import Cart
# Create your models here.

CONTACT_CHOICES = (
    ('Customer', 'Customer'),
    ('Supplier', 'Supplier'),
    ('Distributor', 'Distributor'),
)

ORGANIZATION_CHOICES = (
    ('Company', 'Company'),
    ('Government','Government'),
    ('Non-profit','Non-profit'),
)

ORGANIZATION_ROLE_CHOICES = (
    ('Supplier','Supplier'),
    ('Distributor','Distributor'),
    ('Manufacturer','Manufacturer'),

)
class Organization(models.Model):
    """
    An organization can be a company, government or any kind of group to 
    collect contact info.
    """
    name = models.CharField(maxlength=50, core=True)
    type = models.CharField(maxlength=30,choices=ORGANIZATION_CHOICES)
    role = models.CharField(maxlength=30,choices=ORGANIZATION_ROLE_CHOICES)
    create_date = models.DateField(auto_now_add=True)
    notes = models.TextField(maxlength=200, blank=True, null=True)
    
    def __str__(self):
        return self.name
    
    class Admin:
        list_filter = ['type','role']
        list_display = ['name','type','role']
        
class Contact(models.Model):
    """
    A customer, supplier or any individual that a store owner might interact with.
    """
    first_name = models.CharField(maxlength=30, core=True)
    last_name = models.CharField(maxlength=30, core=True)
    user = models.ForeignKey(User, unique=True, blank=True, null=True, edit_inline=models.TABULAR, 
                            num_in_admin=1,min_num_in_admin=1, max_num_in_admin=1,num_extra_on_change=0)
    role = models.CharField(maxlength=20, blank=True, null=True, choices=CONTACT_CHOICES)
    organization = models.ForeignKey(Organization, blank=True, null=True)
    dob = models.DateField(blank=True, null=True)   
    email = models.EmailField(blank=True)
    notes = models.TextField("Notes",maxlength=500, blank=True)
    create_date = models.DateField(auto_now_add=True)
    
    def _get_full_name(self):
        "Returns the person's full name."
        return '%s %s' % (self.first_name, self.last_name)
    full_name = property(_get_full_name)
    
    def _shipping_address(self):
        for address in self.addressbook_set.all():
            if address.is_default_shipping: 
                return(address)
        return(None)
    shipping_address = property(_shipping_address)
    
    def _billing_address(self):
        for address in self.addressbook_set.all():
            if address.is_default_billing: 
                return(address)
        return(None)
    billing_address = property(_billing_address)
    
    def _primary_phone(self):
        for phonenum in self.phonenumber_set.all():
            if phonenum.primary:
                return(phonenum)
        return(None)
    primary_phone = property(_primary_phone)
    
    def __str__(self):
        return (self.full_name)
        
    class Admin:
        list_display = ('last_name','first_name','organization','role')
        list_filter = ['create_date', 'role', 'organization']
        ordering = ['last_name']

PHONE_CHOICES = (
    ('Work', 'Work'),
    ('Home', 'Home'),
    ('Fax', 'Fax'),
    ('Mobile','Mobile'),
)

INTERACTION_CHOICES = (
    ('Email','Email'),
    ('Phone','Phone'),
    ('In-person','In-person'),
)

class Interaction(models.Model):
    """
    A type of activity with the customer.  Useful to track emails, phone calls or
    in-person interactions.
    """
    contact = models.ForeignKey(Contact)
    type = models.CharField(maxlength=30,choices=INTERACTION_CHOICES)
    date_time = models.DateTimeField(core=True)
    description = models.TextField(maxlength=200)
    
    def __str__(self):
        return ("%s - %s" % (self.contact.full_name, self.type))
    
    class Admin:
        list_filter = ['type', 'date_time']
     
class PhoneNumber(models.Model):
    """
    Multiple phone numbers can be associated with a contact.  Cell, Home, Business etc.
    """
    contact = models.ForeignKey(Contact,edit_inline=models.TABULAR, num_in_admin=1)
    type = models.CharField("Description", choices=PHONE_CHOICES, maxlength=20)
    phone = models.CharField(blank=True, maxlength=12, core=True)
    primary = models.BooleanField(default=False)
    
    def __str__(self):
        return ("%s - %s" % (self.type, self.phone))
    
    class Meta:
        unique_together = (("contact", "primary"),)
        ordering = ['-primary']
        
class AddressBook(models.Model):
    """
    Address information associated with a contact.
    """
    contact=models.ForeignKey(Contact,edit_inline=models.STACKED, num_in_admin=1)
    description=models.CharField("Description", maxlength=20,help_text='Description of address - Home,Relative, Office, Warehouse ,etc.',)
    street1=models.CharField("Street",core=True, maxlength=50)
    street2=models.CharField("Street", maxlength=50, blank=True)
    city=models.CharField("City", maxlength=50)
    state=models.CharField("State", maxlength=10)
    postalCode=models.CharField("Zip Code", maxlength=10)
    country=models.CharField("Country", maxlength=50, blank=True)
    is_default_shipping=models.BooleanField("Default Shipping Address", default=False)
    is_default_billing=models.BooleanField("Default Billing Address", default=False)

    def __str__(self):
       return ("%s - %s" % (self.contact.full_name, self.description))
       
    def save(self):
        """
        If the new address is the default and there already was a default billing or shipping address
        set the old one to False - we only want 1 default for each.
        If there are none, then set this one to default to both
        """
        try:
            existingBilling = self.contact.billing_address
            existingShipping = self.contact.shipping_address
        except:
            existingBilling = None
            existingShipping = None
        
        #If we're setting shipping & one already exists delete it
        if self.is_default_shipping and existingShipping:
            existingShipping.delete()
        #If we're setting billing & one already exists delete it
        if self.is_default_billing and existingBilling:
            existingBilling.delete()
        if not existingBilling:
            self.is_default_billing = True
        if not existingShipping:
            self.is_default_shipping = True
        super(AddressBook, self).save()
        


# Create your models here.

ORDER_CHOICES = (
    ('Online', 'Online'),
    ('In Person', 'In Person'),
    ('Show', 'Show'),
)

ORDER_STATUS = (
    ('Temp', 'Temp'),
    ('Pending', 'Pending'),
    ('Shipped', 'Shipped'),
)

PAYMENT_CHOICES = (
    ('Cash','Cash'),
    ('Credit Card','Credit Card'),
    ('Check','Check'),
)

class Order(models.Model):
    """
    Orders need to contain a copy of all the information at the time the order is placed.
    A user's address or other info could change over time.
    """
    contact = models.ForeignKey(Contact)
    shipStreet1=models.CharField("Street",maxlength=50, blank=True)
    shipStreet2=models.CharField("Street", maxlength=50, blank=True)
    shipCity=models.CharField("City", maxlength=50, blank=True)
    shipState=models.CharField("State", maxlength=10, blank=True)
    shipPostalCode=models.CharField("Zip Code", maxlength=10, blank=True)
    shipCountry=models.CharField("Country", maxlength=50, blank=True)
    billStreet1=models.CharField("Street",maxlength=50, blank=True)
    billStreet2=models.CharField("Street", maxlength=50, blank=True)
    billCity=models.CharField("City", maxlength=50, blank=True)
    billState=models.CharField("State", maxlength=10, blank=True)
    billPostalCode=models.CharField("Zip Code", maxlength=10, blank=True)
    billCountry=models.CharField("Country", maxlength=50, blank=True)
    sub_total = models.FloatField(max_digits=6, decimal_places=2, blank=True)
    total = models.FloatField(max_digits=6,decimal_places=2, blank=True)
    discount = models.FloatField(max_digits=6, decimal_places=2, blank=True, null=True)
    payment= models.CharField(choices=PAYMENT_CHOICES, maxlength=25, blank=True)
    method = models.CharField(choices=ORDER_CHOICES, maxlength=50, blank=True)
    shippingDescription = models.CharField(maxlength=50, blank=True, null=True)
    shippingMethod = models.CharField(maxlength=50, blank=True, null=True)
    shippingModel = models.CharField(choices=activeModules, maxlength=30, blank=True, null=True)
    shippingCost = models.FloatField(max_digits=6, decimal_places=2, blank=True, null=True)
    tax = models.FloatField(max_digits=6, decimal_places=2, blank=True, null=True)
    timeStamp = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    
    def __str__(self):
        return self.contact.full_name
    
    def copyAddresses(self):
        """
        Copy the address so we know what the information was at time of order
        """
        shipaddress = self.contact.shipping_address
        billaddress = self.contact.billing_address
        self.shipStreet1 = shipaddress.street1
        self.shipStreet2 = shipaddress.street2
        self.shipCity = shipaddress.city
        self.shipState = shipaddress.state
        self.shipPostalCode = shipaddress.postalCode
        self.shipCountry = shipaddress.country
        self.billStreet1 = billaddress.street1
        self.billStreet2 = billaddress.street2
        self.billCity = billaddress.city
        self.billState = billaddress.state
        self.billPostalCode = billaddress.postalCode
        self.billCountry = billaddress.country
        
    def copyItems(self):
        pass
    
    def _status(self):
        return(self.orderstatus_set.latest('timeStamp').status)
    status = property(_status)        
    
    def removeAllItems(self):
        for item in self.orderitem_set.all():
            item.delete()
        self.save()
    
    def _CC(self):
        return(self.creditcarddetail_set.all()[0])
    CC = property(_CC)
    
    def _fullBillStreet(self, delim="<br/>"):
        if self.billStreet2:
            return (self.billStreet1 + delim + self.billStreet2)
        else:
            return (self.billStreet1)
    fullBillStreet = property(_fullBillStreet)
    
    def _fullShipStreet(self, delim="<br/>"):
        if self.shipStreet2:
            return (self.shipStreet1 + delim + self.shipStreet2)
        else:
            return (self.shipStreet1)
    fullShipStreet = property(_fullShipStreet)
    
    def save(self):
        self.copyAddresses()
        super(Order, self).save() # Call the "real" save() method.
    
    def invoice(self):
        return('<a href="/admin/print/invoice/%s/">View</a>' % self.id)
    invoice.allow_tags = True
    
    def packingslip(self):
        return('<a href="/admin/print/packingslip/%s/">View</a>' % self.id)
    packingslip.allow_tags = True
    
    def shippinglabel(self):
        return('<a href="/admin/print/shippinglabel/%s/">View</a>' % self.id)
    shippinglabel.allow_tags = True
    
    class Admin:
        fields = (
        (None, {'fields': ('contact','method',)}),
        ('Shipping Information', {'fields': ('shipStreet1','shipStreet2', 'shipCity','shipState', 'shipPostalCode','shipCountry',), 'classes': 'collapse'}),
        ('Billing Information', {'fields': ('billStreet1','billStreet2', 'billCity','billState', 'billPostalCode','billCountry',), 'classes': 'collapse'}),
        ('Totals', {'fields': ( 'shippingCost', 'tax','total','timeStamp','payment',),}),       
        )
        list_display = ('contact', 'timeStamp', 'total','status', 'invoice', 'packingslip', 'shippinglabel')
        list_filter = ['timeStamp','contact']
        date_hierarchy = 'timeStamp'
    class Meta:
        verbose_name = "Product Order"
        
class OrderItem(models.Model):
    """
    A line item on an order.
    """
    order = models.ForeignKey(Order, edit_inline=models.TABULAR, num_in_admin=3)
    item = models.ForeignKey(SubItem)
    quantity = models.IntegerField(core=True)
    unitPrice = models.FloatField(max_digits=6,decimal_places=2)
    lineItemPrice = models.FloatField(max_digits=6,decimal_places=2)
    
    def __str__(self):
        return self.item.full_name

class OrderStatus(models.Model):
    """
    An order will have multiple statuses as it moves its way through processing.
    """
    order = models.ForeignKey(Order, edit_inline=models.STACKED, num_in_admin=1)
    status = models.CharField(maxlength=20, choices=ORDER_STATUS, core=True, blank=True)
    notes = models.CharField(maxlength=100, blank=True)
    timeStamp = models.DateTimeField()
    
    def __str__(self):
        return self.status

