# This file is used to store your site specific settings
# for database access.
# It also store satchmo unique information
#
#
# Modify this file to reflect your settings, then rename it to 
# local_settings.py
#
# This file is helpful if you have an existing Django project.  
# These are specific things that Satchmo will need.
# you MUST make sure these settings are imported from your project settings file!

import os
import logging
DIRNAME = os.path.dirname(__file__)

# This is useful, since satchmo is not the "current directory" like load_data expects.
# SATCHMO_DIRNAME = ''

# Only set these if Satchmo is part of another Django project
#SITE_NAME = ''
#ROOT_URLCONF = ''
#MEDIA_ROOT = os.path.join(DIRNAME, 'static/')
#DJANGO_PROJECT = 'Your Main Project Name'
#DJANGO_SETTINGS_MODULE = 'main-project.settings'

# Make sure Satchmo templates are added to your existing templates
# TEMPLATE_DIRS += (
#    os.path.join(SATCHMO_DIRNAME, "templates"),
#)

# Make sure Satchmo context processor is called
# TEMPLATE_CONTEXT_PROCESSORS += ('satchmo.shop.context_processors.settings')

DATABASE_NAME = ''
DATABASE_PASSWORD = ''
DATABASE_USER = ''
SECRET_KEY = ''

### Credit Card Module ###
# If you are processing credit cards, this is where you should set the appropriate modules
# to be called during the checkout process.
# Right now dummy and authorize.net are the only ones included
CREDIT_PROCESSOR = 'satchmo.payment.modules.dummy'

#### For Authorize.net ######
#AUTHORIZE_NET_CONNECTION = 'https://test.authorize.net/gateway/transact.dll'
#AUTHORIZE_NET_TEST = 'TRUE'
#AUTHORIZE_NET_LOGIN = ''
#AUTHORIZE_NET_TRANKEY = ''

#### For PayPal Web Payments Standard #### 
#PAYPAL_POST_URL = 'https://www.paypal.com/cgi-bin/webscr' # Production 
#PAYPAL_POST_URL = 'https://www.sandbox.paypal.com/cgi-bin/webscr' # Testing 
#PAYPAL_BUSINESS = '' # The email address for your PayPal account. 
#PAYPAL_CURRENCY_CODE = '' # If this is empty or invalid, PayPal assumes USD. 
#PAYPAL_RETURN_ADDRESS = '' # This is the URL that PayPal sends the user to after payment. 

# Google Analytics
# Set this to True if you wish to enable Google Analytics.  You must have
# a google ID in order for this to work
GOOGLE_ANALYTICS = False
# If google is enabled, enter the full google code here - Example "UA-abcd-1"
GOOGLE_ANALYTICS_CODE = "UA-xxxx-x"


#### Satchmo unique variables ####
#This is the base url for the shop.  Only include a leading slash
#examples: '/shop' or '/mystore'
#If you want the shop at the root directory, set SHOP_BASE = ''
SHOP_BASE = '/shop'

# Currency symbol to use
CURRENCY = '$'

#These are used when loading the test data
SITE_DOMAIN = "example.com"
SITE_NAME = "My Site"

#Shipping Modules to enable
SHIPPING_MODULES = ['satchmo.shipping.modules.per', 'satchmo.shipping.modules.flat']

#Configure logging
LOGDIR = "/path/to/log"
LOGFILE = "satchmo.log"
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S',
                    filename=os.path.join(LOGDIR, LOGFILE),
                    filemode='w')

# define a Handler which writes INFO messages or higher to the sys.stderr
fileLog = logging.FileHandler(os.path.join(LOGDIR, LOGFILE), 'w')
fileLog.setLevel(logging.DEBUG)
# set a format which is simpler for console use
formatter = logging.Formatter('%(asctime)s %(name)-12s: %(levelname)-8s %(message)s')
# tell the handler to use this format
fileLog.setFormatter(formatter)
# add the handler to the root logger
logging.getLogger('').addHandler(fileLog)
logging.info("Satchmo Started")
