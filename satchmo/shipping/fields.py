from django.db import models
from satchmo.configuration import SettingNotSet
from satchmo.configuration import config_choice_values

import config


def shipping_choices():
    try:
        return config_choice_values('SHIPPING', 'MODULES')
    except SettingNotSet:
        return ()


class ShippingChoiceCharField(models.CharField):

    def __init__(self, choices="__DYNAMIC__", *args, **kwargs):
        if choices == "__DYNAMIC__":
            kwargs['choices'] = shipping_choices()

        super(ShippingChoiceCharField, self).__init__(*args, **kwargs)
