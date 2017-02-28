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
def orders_key(group = 'default'):
    return db.Key.from_path('orders', group)

class Order(db.Model):
    order_name = db.IntegerProperty(required = True)
    deadline_year = db.IntegerProperty(required = True)
    deadline_month = db.IntegerProperty(required = True)
    deadline_day = db.IntegerProperty(required = True)
    deadline_hour = db.IntegerProperty(required = True)
    deadline_minute = db.IntegerProperty(required = True)
    create_user = db.StringProperty(required = True)
    store_name = db.StringProperty(required = True)
    isopen = db.BooleanProperty(required = True)

    @classmethod
    def by_order_name(cls, order_name , create_user):
        u = Order.all().filter('order_name =', order_name).get()
        if u :
            return True
        else:
            return False

    @classmethod
    def create_order(cls, order_name, deadline_year , deadline_month , deadline_day , deadline_hour,deadline_minute,create_user,store_name,isopen):
        return Order(parent = orders_key(),
                    order_name = order_name,
                    deadline_year = deadline_year,
                    deadline_month = deadline_month,
                    deadline_day = deadline_day,
                    deadline_hour = deadline_hour,
                    deadline_minute = deadline_minute,
                    create_user = create_user,
                    store_name = store_name,
                    isopen = isopen)
