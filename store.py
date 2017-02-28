# -*- coding: utf-8 -*-
import os
import re
import random
import hashlib
import hmac
from string import letters

from google.appengine.ext import db

import webapp2
import jinja2


from handler import *
from user import *

#store
def stores_key(group = 'default'):
    return db.Key.from_path('sotres', group)

class Store(db.Model):
    store_name = db.StringProperty(required = True)
    phone = db.StringProperty(required = True)

    @classmethod
    def by_store_name(cls, store_name):
        storequery = db.GqlQuery("SELECT * FROM Store WHERE store_name = :store_name" ,store_name = store_name)
        u=storequery.fetch(None,0)
        return u

    @classmethod
    def add_store(cls, store_name , phone):
        return Store(parent = stores_key(),
                    store_name = store_name,
                    phone = phone)




