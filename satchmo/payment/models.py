"""
Stores details about the available payment options.
Also stores credit card info in an encrypted format.
"""

from Crypto.Cipher import Blowfish
from datetime import datetime
from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _
from satchmo import caching
from satchmo.configuration import config_value, config_choice_values, SettingNotSet
from satchmo.contact.models import Contact
from satchmo.payment.fields import PaymentChoiceCharField, CreditChoiceCharField
from satchmo.shop.models import OrderPayment
import config
import base64
import logging

try:
    from decimal import Decimal
except:
    from django.utils._decimal import Decimal

log = logging.getLogger('payment.models')
        
class PaymentOption(models.Model):
    """
    If there are multiple options - CC, Cash, COD, etc this class allows
    configuration.
    """
    description = models.CharField(_("Description"), max_length=20)
    active = models.BooleanField(_("Active"), 
        help_text=_("Should this be displayed as an option for the user?"))
    optionName = PaymentChoiceCharField(_("Option Name"), max_length=20, 
        unique=True, 
        help_text=_("The class name as defined in payment.py"))
    sortOrder = models.IntegerField(_("Sort Order"))
    
    class Meta:
        verbose_name = _("Payment Option")
        verbose_name_plural = _("Payment Options")

class CreditCardDetail(models.Model):
    """
    Stores an encrypted CC number, its information, and its
    displayable number.
    """
    orderpayment = models.ForeignKey(OrderPayment, unique=True, 
        related_name="creditcards")
    creditType = CreditChoiceCharField(_("Credit Card Type"), max_length=16)
    displayCC = models.CharField(_("CC Number (Last 4 digits)"),
        max_length=4, )
    encryptedCC = models.CharField(_("Encrypted Credit Card"),
        max_length=40, blank=True, null=True, editable=False)
    expireMonth = models.IntegerField(_("Expiration Month"))
    expireYear = models.IntegerField(_("Expiration Year"))
    
    def storeCC(self, ccnum):
        """Take as input a valid cc, encrypt it and store the last 4 digits in a visible form"""
        # Must remember to save it after calling!
        secret_key = settings.SECRET_KEY
        encryption_object = Blowfish.new(secret_key)
        # block cipher length must be a multiple of 8
        padding = ''
        if (len(ccnum) % 8) <> 0:
            padding = 'X' * (8 - (len(ccnum) % 8))
        self.encryptedCC = base64.b64encode(encryption_object.encrypt(ccnum + padding))
        self.displayCC = ccnum[-4:]
    
    def setCCV(self, ccv):
        """Put the CCV in the cache, don't save it for security/legal reasons."""
        if not self.encryptedCC:
            raise ValueError('CreditCardDetail expecting a credit card number to be stored before storing CCV')
            
        caching.cache_set(self.encryptedCC, skiplog=True, length=60*60, value=ccv)
    
    def getCCV(self):
        try:
            ccv = caching.cache_get(self.encryptedCC)
        except caching.NotCachedError:
            ccv = ""

        return ccv
    
    ccv = property(fget=getCCV, fset=setCCV)
    
    def _decryptCC(self):
        secret_key = settings.SECRET_KEY
        encryption_object = Blowfish.new(secret_key)
        # strip padding from decrypted credit card number
        ccnum = encryption_object.decrypt(base64.b64decode(self.encryptedCC)).rstrip('X')
        return (ccnum)
    decryptedCC = property(_decryptCC) 

    def _expireDate(self):
        return(str(self.expireMonth) + "/" + str(self.expireYear))
    expirationDate = property(_expireDate)
    
    class Meta:
        verbose_name = _("Credit Card")
        verbose_name_plural = _("Credit Cards")
