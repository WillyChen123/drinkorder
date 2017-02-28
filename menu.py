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
def menus_key(group = 'default'):
    return db.Key.from_path('menus', group)

class Menu(db.Model):
    store_name = db.StringProperty(required = True)
    menu_group_name = db.StringProperty(required = True)
    menu_name = db.StringProperty(required = True)
    price = db.IntegerProperty(required = True)

    @classmethod
    def by_menu_name(cls, store_name ,menu_name):
        menuquery = db.GqlQuery("SELECT * FROM Menu WHERE store_name = :store_name and menu_name = :menu_name " ,store_name = store_name ,menu_name = menu_name)
        u=menuquery.fetch(None,0)
        return u

    @classmethod
    def add_menu(cls, store_name,menu_group_name,menu_name, price):
        return Menu(parent = menus_key(),
                    store_name = store_name,
                    menu_group_name = menu_group_name,
                    menu_name = menu_name,
                    price = price)
