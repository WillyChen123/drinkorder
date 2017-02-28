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

#menu_group
def menu_groups_key(group = 'default'):
    return db.Key.from_path('menu_groups', group)

class MenuGroup(db.Model):
    store_name = db.StringProperty(required = True)
    menu_group_name = db.StringProperty(required = True)
    menu_group_no = db.StringProperty(required = True)

    @classmethod
    def by_menu_group_name(cls, store_name ,menu_group_name):
        menu_groupquery = db.GqlQuery("SELECT * FROM Menu WHERE store_name = :store_name and menu_group_name = :menu_group_name " ,store_name = store_name ,menu_group_name = menu_group_name)
        u=menu_groupquery.fetch(None,0)
        return u

    @classmethod
    def add_menu_group(cls, store_name,menu_group_name,menu_group_no):
        return MenuGroup(parent = menu_groups_key(),
                    store_name = store_name,
                    menu_group_name = menu_group_name,
                    menu_group_no = menu_group_no)

