from django import forms
from django.contrib.auth import login, authenticate
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _, ugettext
from satchmo.accounts.mail import send_welcome_email
from satchmo.configuration import config_value
from satchmo.contact.forms import ContactInfoForm
from satchmo.contact.models import AddressBook, PhoneNumber, Contact
from satchmo.l10n.models import Country
from satchmo.utils.unique_id import generate_id

import logging
import signals

log = logging.getLogger(__name__)

class RegistrationForm(forms.Form):
    """The basic account registration form."""

    title = forms.CharField(max_length=30, label=_('Title'), required=False)
    username = forms.RegexField(label=_("Username"), max_length=30, regex=r'^\w+$',
        help_text = _("Required. 30 characters or fewer. Alphanumeric characters only (letters, digits and underscores)."),
        error_message = _("This value must contain only letters, numbers and underscores."), required=True)
    email = forms.EmailField(label=_('Email address'),
        max_length=320, required=True)
    password1 = forms.CharField(label=_('Password'),
        max_length=30, widget=forms.PasswordInput(), required=True)

    password2 = forms.CharField(label=_('Password (again)'),
        max_length=30, widget=forms.PasswordInput(), required=True)

    first_name = forms.CharField(label=_('First name'),
        max_length=30, required=False)
    last_name = forms.CharField(label=_('Last name'),
        max_length=30, required=False)

    def __init__(self, *args, **kwargs):
        self.contact = None
        super(RegistrationForm, self).__init__(*args, **kwargs)

    def clean_username(self):
        username = self.cleaned_data["username"]
        try:
            User.objects.get(username=username)
        except User.DoesNotExist:
            return username
        raise forms.ValidationError(_("A user with that username already exists."))

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1", "")
        password2 = self.cleaned_data["password2"]
        if password1 != password2:
            raise forms.ValidationError(_("The two password fields didn't match."))
        return password2

    def clean_email(self):
        """Prevent account hijacking by disallowing duplicate emails."""
        email = self.cleaned_data.get('email', None)
        if email and User.objects.filter(email=email).count() > 0:
            raise forms.ValidationError(
                ugettext("That email address is already in use."))

        return email

    def save(self, request=None, **kwargs):
        """Create the contact and user described on the form.  Returns the
        `contact`.
        """
        if self.contact:
            log.debug('skipping save, already done')
        else:
            self.save_contact(request)
        return self.contact

    def save_contact(self, request):
        log.debug("Saving contact")
        data = self.cleaned_data
        password = data['password1']
        email = data['email']
        first_name = data['first_name']
        last_name = data['last_name']
        username = data['username']

        verify = (config_value('SHOP', 'ACCOUNT_VERIFICATION') == 'EMAIL')

        if verify:
            from registration.models import RegistrationProfile
            user = RegistrationProfile.objects.create_inactive_user(
                username, password, email, send_email=True)
        else:
            user = User.objects.create_user(username, email, password)

        user.first_name = first_name
        user.last_name = last_name
        user.save()

        # If the user already has a contact, retrieve it.
        # Otherwise, create a new one.
        try:
            contact = Contact.objects.from_request(request, create=False)

        except Contact.DoesNotExist:
            contact = Contact()

        contact.user = user
        contact.first_name = first_name
        contact.last_name = last_name
        contact.email = email
        contact.role = 'Customer'
        contact.title = data.get('title', '')
        contact.save()

        signals.satchmo_registration.send(self, contact=contact, data=data)

        if not verify:
            user = authenticate(username=username, password=password)
            login(request, user)
            send_welcome_email(email, first_name, last_name)
            signals.satchmo_registration_verified.send(self, contact=contact)

        self.contact = contact

        return contact

class RegistrationAddressForm(RegistrationForm, ContactInfoForm):
    """Registration form which also requires address information."""
    
    def __init__(self, *args, **kwargs):
        super(RegistrationAddressForm, self).__init__(*args, **kwargs)

    def save(self, request=None, **kwargs):
        contact = self.save_contact(request)
        kwargs['contact'] = contact
        
        log.debug('Saving address for %s', contact)
        self.save_info(**kwargs)
                
        return contact