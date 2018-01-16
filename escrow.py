#!/usr/bin/env python
#-*- coding: utf-8 -*-

"""Escrow 在线支付接口

支付官网 https://www.escrow.com
开发文档 https://www.escrow.com/api/docs
"""

import sys
sys.dont_write_bytecode = True

import requests
from posixpath import join as posix_join
from weakref import proxy as weakref_proxy
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

    def __init__(self, api_secret, api_key, account_email, password):
        self.account_email = account_email
        self.api_secret = api_secret
        self.password = password
        self.api_key = api_key

def parse_object(data):
    if isinstance(data, list):
        tmp = []
        for value in data:
            if isinstance(value, (list, tuple, dict)):
                tmp.append(parse_object(value))
            elif isinstance(value, Base):
                tmp.append(value.to_dict())
            else:
                tmp.append(value)
        return tmp
    if isinstance(data, dict):
        tmp = {}
        for key, value in data.items():
            if isinstance(value, (list, tuple, dict)):
                tmp[key] = parse_object(value)
            elif isinstance(value, Base):
                tmp[key] = value.to_dict()
            else:
                tmp[key] = value
        return tmp
    if isinstance(data, Base):
        return data.to_dict()
    return data

class Base(object):

    def to_dict(self):
        return parse_object(self.__dict__)

class Transaction(Base):

    def __init__(self, escrowapi, buyer_email=None, seller_email=None,
                       currency='usd', description=None):
        self.escrowapi = weakref_proxy(escrowapi)
        self.buyer_email = buyer_email
        self.seller_email = seller_email
        self.currency = currency
        self.description = description
        self.items = []

    def add_item(self, transaction_item):
        self.items.append(transaction_item)

    def finish(self):
        api_url = self.escrowapi.create_api_url('transaction')
        response = requests.post(
            api_url, auth=self.auth, json=self.to_dict()
        )
        if 200 != status_code:
            text = response.text or error_codes[status_code]
            raise EscrowAPIError(text)
        return response.json()

    def to_dict(self):
        return {
            'parties': [
                {
                    'role': 'buyer',
                    'customer': self.buyer_email
                },
                {
                    'role': 'seller',
                    'customer': self.seller_email
                }
            ],
            'currency': self.currency,
            'description': self.description,
            'items': parse_object(self.items)
        }
        return parse_object(self.__dict__)

class TransactionItem(Base):

    def __init__(self, title=None, description=None, type=None,
                       inspection_period=None, quantity=None):
        self.title = title
        self.description = description
        self.type = type
        self.inspection_period = inspection_period
        self.quantity = quantity
        self.schedule = []

    def add_schedule(self, amount=None, payer_customer=None,
                           beneficiary_customer=None):
        item_schedule = TransactionItemSchedule(
            amount=amount, payer_customer=payer_customer,
            beneficiary_customer=beneficiary_customer
        )
        self.schedule.append(item_schedule)

class TransactionItemSchedule(Base):

    def __init__(self, amount=None, payer_customer=None,
                       beneficiary_customer=None):
        self.amount = amount
        self.payer_customer = payer_customer
        self.beneficiary_customer = beneficiary_customer

class EscrowAPI(object):

    def __init__(self, api_baseurl, api_secret, api_key, account_email,
                       password=None):
        self.authorization = Authorization(
            api_secret, api_key, account_email, password)
        self.api_baseurl = api_baseurl

    @property
    def auth(self):
        authorization = self.authentication
        return authorization.account_email, authorization.api_key

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

    def create_api_url(self, *args):
        args = filter(None, map(lambda s: str(s).strip('/'), args))
        return posix_join(self.api_baseurl, *args)

    def customer(self, email, first_name=None, middle_name=None,
                       last_name=None, line1=None, line2=None, city=None,
                       state=None, country=None, post_code=None,
                       post_number=None):
        api_url = self.create_api_url('/customer')
        response = requests.post(api_url, auth=self.auth, json={
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
        })
        status_code = response.status_code
        if 200 != status_code:
            text = response.text or error_codes[status_code]
            raise EscrowAPIError(text)
        return response.json()

    def me(self):
        api_url  = self.create_api_url('/customer/me')
        response = requests.get(api_url, auth=self.auth)
        status_code = response.status_code
        if 200 != status_code:
            text = response.text or error_codes[status_code]
            raise EscrowAPIError(text)
        return response.json()

    def transaction_as_customer(self, transaction_id, as_customer, action):
        api_url = self.create_api_url('transaction', transaction_id)
        headers = { 'As-Customer': as_customer }
        json    = { 'action': action }
        response = requests.patch(
            api_url, auth=self.auth, headers=headers, json=json)
        status_code = response.status_code
        if 200 != status_code:
            text = response.text or error_codes[status_code]
            raise EscrowAPIError(text)
        return response.json()

    def get_transaction(self, transaction_id):
        api_url = self.create_api_url('transaction', transaction_id)
        response = requests.get(api_url, auth=self.auth)
        if 200 != status_code:
            text = response.text or error_codes[status_code]
            raise EscrowAPIError(text)
        return response.json()

    def create_transaction(self, seller_email, currency='usd',
                                 description=None):
        return Transaction(
            self, buyer_email='me', seller_email=seller_email,
            currency=currency, description=description
        )

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
    # print escrowapi.me()
    # 
    transaction = Transaction(
        buyer_email='me', seller_email='keanu.reaves@escrow.com',
        currency='usd', description='johnwick.com'
    )
    transaction_item = TransactionItem(
        title='johnwick.com', description='johnwick.com',
        type='domain_name', inspection_period=259200, quantity=1
    )
    transaction_item.add_schedule(
        amount=1000, payer_customer='me',
        beneficiary_customer='keanu.reaves@escrow.com'
    )
    transaction.add_item(transaction_item)

    ret = transaction_item.to_dict()
    ret = transaction.to_dict()
    import json
    print json.dumps(ret, indent=4)

if '__main__' == __name__:
    main()