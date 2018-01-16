#!/usr/bin/env python
#-*- coding: utf-8 -*-

"""Escrow 在线支付接口

支付官网 https://www.escrow.com
开发文档 https://www.escrow.com/api/docs
"""

import sys
sys.dont_write_bytecode = True

import requests
from api_config import ESCROW_SECRET, ESCROW_API_KEY

# See below for a list of HTTP codes we return.
error_codes = {
    200: "The API request was performed successfully",
    400: "The client submitted a bad request",
    401: "You are trying to perform an action that requires you to be authenticated",
    403: "You are trying to perform an action that you are not permitted to perform",
    404: "You are trying to access a resource that doesn't exist",
    422: "Your request was malformed",
    429: "You have performed too many requests and have been rate limited.",
    500: "There was an unexpected server error"
}

class Authorization(object):

    def __init__(self, api_secret, api_key, account_email, password=None):
        self.api_secret = api_secret
        self.api_key = api_key
        self.account_email = account_email
        self.password = password

class EscrowAPI(object):

    def __init__(self, api_baseurl,
                       api_secret,
                       api_key,
                       account_email,
                       password=None):
        self.authorization = Authorization(
            api_secret, api_key, account_email, password=password
        )
        self.api_baseurl = api_baseurl

    @property
    def api_secret(self):
        return self.authorization.api_secret

    @property
    def api_key(self):
        return self.authorization.api_key

    @property
    def account_email(self):
        return self.authorization.account_email

    @property
    def password(self):
        return self.authorization.password

    def customer(self, email, first_name=None,
                              middle_name=None,
                              last_name=None,
                              line1=None,
                              line2=None,
                              city=None,
                              state=None,
                              country=None,
                              post_code=None,
                              post_number=None):
        """Creating a new customer on Escrow.com
        
        You are only able to create customers where their email address is 
        not already in use. Creating an account for a user that already 
        exists will result in an error, and an HTTP 403 will be returned.
        Once a customer has been created, either through the API or if 
        they've signed up themselves, their information can no longer be 
        provided by API integrations.

        Once a customer has been created, they will then receive an email 
        introducing them to Escrow.com and to log in and set their password.

        Demo:
            import requests
            requests.post(
                'https://api.escrow.com/2017-09-01/customer',
                auth=('account-email', 'api-key')
                json={
                    "email": "john@escrow.com",
                    "first_name": "John",
                    "middle_name": "Kane",
                    "last_name": "Smith",
                    "address": {
                        "line1": "1829 West Lane",
                        "line2": "Apartment 301020",
                        "city": "San Francisco",
                        "state": "CA",
                        "country": "US",
                        "post_code": "10203"
                    },
                    "phone_number": "8885118600"
                }
            )

        Arguments:
            email {[type]} -- [description]
        
        Keyword Arguments:
            first_name {[type]} -- [description] (default: {None})
            middle_name {[type]} -- [description] (default: {None})
            last_name {[type]} -- [description] (default: {None})
            line1 {[type]} -- [description] (default: {None})
            line2 {[type]} -- [description] (default: {None})
            city {[type]} -- [description] (default: {None})
            state {[type]} -- [description] (default: {None})
            country {[type]} -- [description] (default: {None})
            post_code {[type]} -- [description] (default: {None})
            post_number {[type]} -- [description] (default: {None})
        
        Returns:
            [type] -- [description]
        """
        json = {
            'email': email,
            'first_name': first_name,
            'middle_name': middle_name,
            'last_name': last_name,
            'address': {
                'line1': line1,
                'line2': line2,
                'city': city,
                'state': state,
                'country': country,
                'post_code': post_code
            },
            'phone_number': phone_number
        }
        account_email = self.account_email
        api_key = self.api_key
        api_baseurl = self.api_baseurl
        response = requests.post(
            '%(api_baseurl)scustomer' % { 'api_baseurl': api_baseurl },
            auth=(account_email, api_key),
            json=json
        )
        status_code = response.status_code
        print response.headers
        if 200 != status_code:
            text = response.text or error_codes[status_code]
            raise EscrowAPIError(text)
        return response.json()

    def me(self):
        """Authentication with API keys

        From within the account settings page, you can generate API keys 
        associated with your account. This is preferable to using your user 
        name and password, as it allows you to recycle your credentials 
        without changing the password on your account. Using an API key 
        is almost identical to using a username and password for 
        authentication. Simply provide your API key as your password and 
        we will handle the rest.

        Demo:
            import requests
            requests.get(
                'https://api.escrow.com/2017-09-01/customer/me',
                auth=('account-email', 'api-key')
            )
        
        Returns:
            [type] -- [description]
        
        Raises:
            EscrowAPIError -- [description]
        """
        account_email = self.account_email
        api_key       = self.api_key
        api_baseurl   = self.api_baseurl
        response = requests.get(
            '%(api_baseurl)scustomer/me' % {
                'api_baseurl': api_baseurl
            },
            auth=(account_email, api_key),
        )
        status_code = response.status_code
        print response.headers
        if 200 != status_code:
            text = response.text or error_codes[status_code]
            raise EscrowAPIError(text)
        return response.json()

    def transaction_as_customer(self, transaction_id, as_customer, action):
        """Performing actions on behalf of customers in a transaction
        
        The way that this is accomplished is by setting the As-Customer 
        header to the email address of the party you want to perform 
        the action on behalf of.

        Demo:
            import requests
            requests.post(
                'https://api.escrow.com/2017-09-01/customer',
                auth=('email-address', 'api-key'),
                json={
                    "email": "john@escrow.com",
                    "first_name": "John",
                    "middle_name": "Kane",
                    "last_name": "Smith",
                    "address": {
                        "line1": "1829 West Lane",
                        "line2": "Apartment 301020",
                        "city": "San Francisco",
                        "state": "CA",
                        "country": "US",
                        "post_code": "10203"
                    },
                    "phone_number": "8885118600"
                }
            )
        
        Arguments:
            transaction_id {[type]} -- [description]
            as_customer {[type]} -- [description]
            action {[type]} -- [description]
        
        Returns:
            [type] -- [description]
        """
        account_email = self.account_email
        api_key       = self.api_key
        api_baseurl   = self.api_baseurl
        headers = { 'As-Customer': as_customer }
        json = { 'action': action }
        response = requests.patch(
            '%(api_baseurl)stransaction/%(transaction_id)s' % {
                'api_baseurl'   : api_baseurl,
                'transaction_id': transaction_id
            },
            auth=(account_email, api_key),
            headers=headers,
            json=json
        )
        status_code = response.status_code
        print response.headers
        if 200 != status_code:
            text = response.text or error_codes[status_code]
            raise EscrowAPIError(text)
        return response.json()

    def transaction(self, id, as_customer=None, action=None):
        """[summary]
        
        [description]
        
        Demo:
            import requests

            requests.get(
                'https://api.escrow.com/2017-09-01/transaction/100',
                auth=('john.wick@escrow.com', 'Escrow1234'),
            )

        Arguments:
            id {[type]} -- [description]
        
        Keyword Arguments:
            as_customer {[type]} -- [description] (default: {None})
            action {[type]} -- [description] (default: {None})
        """
        response = requests.get(
            '%(api)stransaction/100' % { 'api': api },
            auth=(account, password)
        )
        status_code = response.status_code
        text = response.text
        print status_code, text

def main():
    if len(sys.argv) < 2 or 'sandbox' == sys.argv[1].lower():
        API_BASEURL = 'https://api.escrow-sandbox.com/2017-09-01/'
        account_email = 'Your Sandbox Account Email'
        password = 'Your Sandbox Password'
    else:
        API_BASEURL = 'https://api.escrow.com/2017-09-01/'
        account_email = 'Your Account Email'
        password = 'Your Password'

    escrowapi = EscrowAPI(
        API_BASEURL, ESCROW_SECRET, ESCROW_API_KEY,
        account_email, password=password
    )

    # escrowapi.transaction()
    print escrowapi.me()

if '__main__' == __name__:
    main()