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

#menu
def personalorders_key(group = 'default'):
    return db.Key.from_path('personalorders', group)

class PersonalOrder(db.Model):
    order_user = db.StringProperty(required = True)
    order_user_chinesename = db.StringProperty(required = True)    
    order_name = db.IntegerProperty(required = True)
    store_name = db.StringProperty(required = True)
    create_user = db.StringProperty(required = True)    
    drink_name = db.StringProperty(required = True)
    drink_price = db.IntegerProperty(required = True)
    hot_cold = db.StringProperty(required = True)
    ice = db.StringProperty(required = True)
    sugar = db.StringProperty(required = True)
    order_num = db.IntegerProperty(required = True)
    total = db.IntegerProperty(required = True)
    order_paid = db.BooleanProperty(required = True)

    @classmethod
    def by_personalorder_name(cls, order_name ,store_name, create_user,order_user ,drink_name):
        orderquery = db.GqlQuery("SELECT * FROM PersonalOrder WHERE order_name = :order_name and store_name = :store_name and create_user = :username and order_user = :order_user and drink_name = :drink_name " ,order_name = order_name ,store_name = store_name,username = create_user ,order_user = order_user ,drink_name = drink_name)
        sorders=orderquery.fetch(None,0)            
        if sorders:
            return True
        else:
            return False

    @classmethod
    def order_drink(cls, order_user ,order_user_chinesename, order_name,store_name, create_user,drink_name , drink_price,hot_cold,ice,sugar,order_num,total,order_paid):
        return PersonalOrder(parent = personalorders_key(),
                    order_user = order_user,
                    order_user_chinesename = order_user_chinesename ,
                    order_name = order_name,
                    store_name = store_name,
                    create_user = create_user,
                    drink_name = drink_name,
                    drink_price = drink_price,
                    hot_cold = hot_cold,
                    ice = ice,
                    sugar = sugar,
                    order_num = order_num,
                    total = total ,
                    order_paid = order_paid)




