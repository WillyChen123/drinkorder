# -*- coding: utf-8 -*-
import os
import re
import random
import hashlib
import hmac
from string import letters
from time import strftime


from google.appengine.ext import db

import webapp2
import jinja2

import datetime

from handler import *
from user import *
from menu import *
from order import *
from personalorder import *
from store import *
from menugroup import *
from config import *

USER_RE = re.compile(r"^[a-zA-Z0-9_-]{6,10}$")
def valid_username(username):
    return username and USER_RE.match(username)

PASS_RE = re.compile(r"^.{6,20}$")
def valid_password(password):
    return password and PASS_RE.match(password)

class MainPage(Handler):
    def get(self):
        self.redirect('/login')

class Login(Handler):
    def get(self):
        self.render('login.html')

    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')

        u = User.login(username, password)
        if u:
            self.login(u)
            self.redirect('/welcome')
        else:
            msg = u'登入錯誤'
            self.render('login.html', error = msg)

class Logout(Handler):
    def get(self):
        self.logout()
        self.redirect('/')

class Welcome(Handler):
    def get(self):
        if self.user :
            if not self.user.stop:
                self.render('welcome.html', username = self.user.name , admin = self.user.admin,chinesename = self.user.chinesename)
            elif self.user.stop:
                self.redirect('/stop')
        else:
            self.redirect('/')

class Signup(Handler):
    def get(self):
        if signup_open:
            self.render("signup.html")
        else:
            self.redirect('/')

    def post(self):
        have_error = False
        self.username = self.request.get('username')
        self.password = self.request.get('password')
        self.verify = self.request.get('verify')
        self.admin=self.request.get("admin")
        self.chinesename = self.request.get("chinesename")
        agree=self.request.get('agree')
        answer=self.request.get('answer')
        self.Booladmin = False

        params = dict(username = self.username)

        if answer != invitation_code:
            params['error_answer'] = u"錯誤"
            have_error = True

        if not valid_username(self.username):
            params['error_username'] = u"請輸入帳號"
            have_error = True

        if not valid_password(self.password):
            params['error_password'] = u"請輸入密碼"
            have_error = True
        if not self.chinesename:
            params['error_chinesename'] = u"請輸入姓名"
            have_error = True
        if self.password != self.verify:
            params['error_verify'] = u"密碼不一致"
            have_error = True
        if not agree:
            params['error_agree'] = u"請同意以上事項"
            have_error = True

        if have_error:
            self.render('signup.html', **params)
        else:
            self.done()

    def done(self, *a, **kw):
        raise NotImplementedError

class Register(Signup):
    def done(self):
        #make sure the user doesn't already exist
        u = User.by_name(self.username)
        if u:
            msg = u'帳號已被註冊'
            self.render('signup.html', error_username = msg)
        else:
            if self.admin == "on":
                self.Booladmin = True
            self.stop=False
            self.stop_admin = ' '
            u = User.register(self.username, self.password, self.chinesename , self.Booladmin, self.stop , self.stop_admin)
            u.put()

            self.login(u)
            self.redirect('/welcome')

class ChangePassword(Handler):
    def get(self):
        if self.user :
            if not self.user.stop:
                self.render('changepassword.html',username = self.user.name , admin = self.user.admin ,chinesename = self.user.chinesename)
            elif self.user.stop:
                self.redirect('/stop')
        else:
            self.redirect('/')

    def post(self):
        changepassword = self.request.get('changepassword')
        changeverify = self.request.get('changeverify')
        have_error = False

        params = dict()
        params['username']=self.user.name
        params['admin'] = self.user.admin
        params['chinesename'] = self.user.chinesename

        if not valid_password(changepassword):
            params['error_password'] = u"請輸入密碼"
            have_error = True
        elif changepassword != changeverify:
            params['error_verify'] = u"密碼不一致"
            have_error = True

        if have_error:
            self.render('changepassword.html', **params)
        else:
            q = db.GqlQuery("SELECT * FROM User WHERE name = :username " ,username = self.user.name )
            results = q.fetch(10)
            db.delete(results)

            self.Boolstop=False
            self.stop_admin = ' '
            
            u = User.register(self.user.name, changepassword, self.user.chinesename ,self.user.admin,self.Boolstop,self.stop_admin)
            u.put()

            self.login(u)
            self.redirect('/changepasswordsuccessful')        

class ChangePasswordSuccessful(Handler):
    def get(self):
        if self.user :
            if not self.user.stop:
                self.render('changepasswordsuccessful.html',username=self.user.name,admin = self.user.admin ,chinesename = self.user.chinesename)
            elif self.user.stop:
                self.redirect('/stop')
        else:
            self.redirect('/')

class NotAdmin(Handler):
    def get(self):
        if self.user :
            if not self.user.stop:
                self.render('notadmin.html',username = self.user.name , admin = self.user.admin,chinesename = self.user.chinesename)
            elif self.user.stop:
                self.redirect('/stop')
        else:
            self.redirect('/')
            
class AddMenu(Handler):
    def get(self):
        if self.user :
            if not self.user.stop:
                if self.user.admin:
                    menu_groupquery=MenuGroup.all()
                    menu_groups=menu_groupquery.fetch(None,0)
                    self.render('addmenu.html',username = self.user.name , admin = self.user.admin,chinesename = self.user.chinesename , menu_groups = menu_groups)
                else:
                    self.redirect('/notadmin')
            elif self.user.stop:
                self.redirect('/stop')
        else:
            self.redirect('/')

    def post(self):
        store_name = self.request.get('store_name')
        menu_group = self.request.get('menu_group_name')
        menu_name = self.request.get('menu_name')
        sprice = self.request.get('price')        

        if not store_name or not menu_group or not menu_name or not sprice or not sprice.isdigit() or len(menu_name)>15:
            msg = u"請重試一遍"
            menu_groupquery=MenuGroup.all()
            menu_groups=menu_groupquery.fetch(None,0)
            self.render('addmenu.html', error=msg,username = self.user.name , admin = self.user.admin,chinesename = self.user.chinesename , menu_groups = menu_groups)
        else:
            menu_store_name = menu_group.split(',')[0]  
            menu_group_name = menu_group.split(',')[1] 
            if menu_store_name != store_name:
                msg = u'請重新選擇'
                menu_groupquery=MenuGroup.all()
                menu_groups=menu_groupquery.fetch(None,0)
                self.render('addmenu.html', error=msg,username = self.user.name , admin = self.user.admin,chinesename = self.user.chinesename , menu_groups = menu_groups)
            else:
                u = Menu.by_menu_name(store_name ,menu_name)
                if u:
                    msg = u'已有此飲料'
                    menu_groupquery=MenuGroup.all()
                    menu_groups=menu_groupquery.fetch(None,0)
                    self.render('addmenu.html', error=msg,username = self.user.name , admin = self.user.admin,chinesename = self.user.chinesename , menu_groups = menu_groups)
                else:                
                    price = int(sprice)
                    u = Menu.add_menu(store_name , menu_group_name,menu_name , price)
                    u.put()

                    self.redirect('/addmenusuccessful')

class AddMenuSuccessful(Handler):
    def get(self):
        if self.user :
            if not self.user.stop:
                if self.user.admin:
                    self.render('addmenusuccessful.html',username = self.user.name , admin = self.user.admin,chinesename = self.user.chinesename)
                else:
                    self.redirect('/notadmin')
            elif self.user.stop:
                self.redirect('/stop')
        else:
            self.redirect('/')

class ViewMenu(Handler):
    def get(self):
        if self.user :
            if not self.user.stop:
                # menuquery = db.GqlQuery("SELECT * FROM Menu ")
                # smenus=menuquery.fetch(None,0)
                # menus = sorted(smenus, reverse=True , key=lambda smenus : smenus.store_name)
                groupquery = db.GqlQuery("SELECT * FROM MenuGroup ")
                sgroups=groupquery.fetch(None,0)
                groups = sorted(sgroups, reverse=True , key=lambda sgroups : sgroups.store_name)                
                self.render('viewmenu.html', username = self.user.name , admin = self.user.admin,chinesename = self.user.chinesename,groups=groups)
            elif self.user.stop:
                self.redirect('/stop')
        else:
            self.redirect('/')
    def post(self):
        search = self.request.get('search')
        if not search:
            self.redirect('/viewmenu')
        else:
            store_name=search.split(',')[0]  
            menu_group_name =search.split(',')[1]  
            menuquery = db.GqlQuery("SELECT * FROM Menu WHERE store_name=:store_name and menu_group_name=:menu_group_name ",store_name=store_name,menu_group_name=menu_group_name)
            smenus=menuquery.fetch(None,0)
            menus = sorted(smenus, reverse=True , key=lambda smenus : smenus.menu_name)
            groupquery = db.GqlQuery("SELECT * FROM MenuGroup ")
            sgroups=groupquery.fetch(None,0)
            groups = sorted(sgroups, reverse=True , key=lambda sgroups : sgroups.store_name)                
            self.render('viewmenu.html', username = self.user.name , admin = self.user.admin,chinesename = self.user.chinesename,menus = menus , groups=groups)
              
        

class AddStore(Handler):
    def get(self):
        if self.user:
            if not self.user.stop:
                if self.user.admin:
                    self.render('addstore.html',username = self.user.name , admin = self.user.admin,chinesename = self.user.chinesename)
                else:
                    self.redirect('/notadmin')
            elif self.user.stop:
                self.redirect('/stop')
        else:
            self.redirect('/')

    def post(self):
        store_name = self.request.get('store_name')
        phone = self.request.get('phone')        

        if not store_name or not phone or len(store_name)>8:
            msg = u"請重試一遍"
            self.render('addstore.html', error=msg,username = self.user.name , admin = self.user.admin,chinesename = self.user.chinesename)
        else:
            u = Store.by_store_name(store_name)
            if u:
                msg = u'已有此商店'
                self.render('addstore.html', error = msg ,username = self.user.name , admin = self.user.admin,chinesename = self.user.chinesename)
            else:
                u = Store.add_store(store_name , phone)
                u.put()

                self.redirect('/addstoresuccessful')

class AddStoreSuccessful(Handler):
    def get(self):
        if self.user :
            if not self.user.stop:
                if self.user.admin:
                    self.render('addstoresuccessful.html',username = self.user.name , admin = self.user.admin,chinesename = self.user.chinesename)
                else:
                    self.redirect('/notadmin')
            elif self.user.stop:
                self.redirect('/stop')
        else:
            self.redirect('/')

class ViewStore(Handler):
    def get(self):
        if self.user :
            if not self.user.stop:
                query=Store.all()
                stores=query.fetch(None,0)

                self.render('viewstore.html', username = self.user.name , admin = self.user.admin,chinesename = self.user.chinesename,stores = stores)
            elif self.user.stop:
                self.redirect('/stop')
        else:
            self.redirect('/')

def valid_year(year):
    if year == 2014 or year == 2015:
        return False
    else:
        return True

def valid_month(month):
    if month >=1 and month <= 12:
        return False
    else:
        return True

def valid_day(day):
    if day >=1 and day <=31:
        return False
    else:
        return True

def valid_hour(hour):
    if hour >= 0 and hour <= 23:
        return False
    else:
        return True

def valid_minute(minute):
    if minute >=0 and minute <=59:
        return False
    else:
        return True

class CreateOrder(Handler):
    def get(self):
        if self.user :
            if not self.user.stop:
                storequery=Store.all()
                stores=storequery.fetch(None,0)
                current_year = datetime.date.today().strftime("%Y")
                current_month = datetime.date.today().strftime("%m")
                current_day = datetime.date.today().strftime("%d")
                sorder_name = "" + current_year + (current_month if current_month>=10 else "0"+current_month)+(current_day if current_day>=10 else "0"+current_day)
                self.render('createorder.html',username = self.user.name , admin = self.user.admin,chinesename = self.user.chinesename , order_name = sorder_name , stores = stores,order_name_len=order_name_len,current_year=current_year,current_month=current_month,current_day=current_day)
            elif self.user.stop:
                self.redirect('/stop')
        else:
            self.redirect('/')

    def post(self):
        sorder_name = self.request.get('order_name')
        sdeadline_year = self.request.get('deadline_year')
        sdeadline_month = self.request.get('deadline_month')
        sdeadline_day = self.request.get('deadline_day')
        sdeadline_hour = self.request.get('deadline_hour')
        sdeadline_minute = self.request.get('deadline_minute')
        store_name = self.request.get('store_name')
        isopen = True        
        have_error = False
        current_year = datetime.date.today().strftime("%Y")
        current_month = datetime.date.today().strftime("%m")
        current_day = datetime.date.today().strftime("%d")

        if not sorder_name.isdigit() or not sdeadline_year.isdigit() or not sdeadline_month.isdigit() or not sdeadline_day.isdigit() or not sdeadline_hour.isdigit() or not sdeadline_minute.isdigit():
            storequery=Store.all()
            stores=storequery.fetch(None,0)
            msg = u"請重試一遍"
            self.render('createorder.html', error=msg,username = self.user.name , admin = self.user.admin,chinesename = self.user.chinesename, order_name = sorder_name ,stores=stores,order_name_len=order_name_len,current_year=current_year,current_month=current_month,current_day=current_day)
            have_error = True        
        if not have_error:
            deadline_year = int(sdeadline_year)
            deadline_month = int(sdeadline_month)
            deadline_day = int(sdeadline_day)
            deadline_hour = int(sdeadline_hour)
            deadline_minute = int(sdeadline_minute)
            if  len(sorder_name) != order_name_len or not store_name or not valid_year(sdeadline_year) or not valid_month(sdeadline_month) or not valid_day(sdeadline_day) or not valid_hour(sdeadline_hour) or not valid_minute(sdeadline_minute):
                storequery=Store.all()
                stores=storequery.fetch(None,0)
                msg = u"請重試一遍"
                self.render('createorder.html', error=msg,username = self.user.name , admin = self.user.admin,chinesename = self.user.chinesename,order_name = sorder_name ,stores=stores,order_name_len=order_name_len,current_year=current_year,current_month=current_month,current_day=current_day)
            else:
                order_name = int(sorder_name)
                u = Order.by_order_name(order_name , self.user.name)
                if u:
                    storequery=Store.all()
                    stores=storequery.fetch(None,0)
                    msg = u'已有此訂單'
                    self.render('createorder.html', error = msg ,username = self.user.name , admin = self.user.admin,chinesename = self.user.chinesename,order_name = sorder_name ,stores=stores,order_name_len=order_name_len,current_year=current_year,current_month=current_month,current_day=current_day)
                else:               
                    u = Order.create_order(order_name , deadline_year , deadline_month,deadline_day,deadline_hour,deadline_minute,self.user.name,store_name,isopen)
                    u.put()

                    self.redirect('/createordersuccessful')

class CreateOrderSuccessful(Handler):
    def get(self):
        if self.user :
            if not self.user.stop:
                self.render('createordersuccessful.html',username = self.user.name , admin = self.user.admin,chinesename = self.user.chinesename)
            elif self.user.stop:
                self.redirect('/stop')
        else:            
            self.redirect('/')

class ViewOrder(Handler):
    def get(self):
        if self.user :
            if not self.user.stop:
                orderquery=Order.all()
                sorders=orderquery.fetch(None,0)
                orders = sorted(sorders, reverse=True , key=lambda sorders : sorders.order_name)
                self.render('vieworder.html',username = self.user.name , admin = self.user.admin,chinesename = self.user.chinesename,orders=orders)
            elif self.user.stop:
                self.redirect('/stop')
        else:
            self.redirect('/')

class ChooseOrderDrink(Handler):
    def get(self):
        if self.user :
            if not self.user.stop:
                orderquery=Order.all()
                sorders=orderquery.fetch(None,0)
                orders = sorted(sorders, reverse=True , key=lambda sorders : sorders.order_name)                
                self.render('chooseorderdrink.html',username = self.user.name , admin = self.user.admin,chinesename = self.user.chinesename,orders = orders)        
            elif self.user.stop:
                self.redirect('/stop')
        else:
            self.redirect('/')

    def post(self):
        order = self.request.get('order')
        if not order:
            self.redirect('/chooseorderdrink')
        else:
            order_name = order.split(',')[0]  
            create_user = order.split(',')[1]           
            if order_name :
                self.redirect('/choosemenugroup?order=%s&create_user=%s' %(order_name,create_user))
            else:
                self.redirect('/chooseorderdrink')

class ChooseMenuGroup(Handler):
    def get(self):
        if self.user :
            if not self.user.stop:
                sorder_name = self.request.get('order')
                create_user = self.request.get('create_user')
                if not sorder_name.isdigit() or not create_user:
                    self.redirect('/chooseorderdrink')
                else:
                    order_name = int(sorder_name)
                    orderquery = db.GqlQuery("SELECT * FROM Order WHERE order_name = :order_name " ,order_name = order_name)
                    sorders=orderquery.fetch(None,0)
                    if not sorders:
                        self.redirect('/chooseorderdrink')
                    else:
                        store_name = sorders[0].store_name
                        menugroupquery=db.GqlQuery("SELECT * FROM MenuGroup WHERE store_name = :store_name" , store_name = store_name)
                        menu_groups=menugroupquery.fetch(None,0)
                        self.render('choosemenugroup.html',username = self.user.name , admin = self.user.admin,chinesename = self.user.chinesename,order_name = order_name ,create_user = create_user,store_name = store_name,menu_groups = menu_groups)                
            elif self.user.stop:
                self.redirect('/stop')
        else:
            self.redirect('/')
    def post(self):
        order_name = self.request.get('order_name')
        create_user = self.request.get('create_user')
        menu_group_no = self.request.get('menu_group_no')
        if not order_name or not create_user or not menu_group_no:
            self.redirect('/chooseorderdrink')
        else:
            self.redirect('/orderdrink?order_name=%s&create_user=%s&menu_group_no=%s' %(order_name,create_user,menu_group_no))



class OrderDrink(Handler):
    def get(self):
        if self.user :
            if not self.user.stop:
                sorder_name = self.request.get('order_name')
                create_user = self.request.get('create_user')
                menu_group_no = self.request.get('menu_group_no')
                if not sorder_name.isdigit() and not create_user or not menu_group_no:
                    self.redirect('/chooseorderdrink')
                else:
                    order_name = int(sorder_name)
                    orderquery = db.GqlQuery("SELECT * FROM Order WHERE order_name = :order_name " ,order_name = order_name)
                    sorders=orderquery.fetch(None,0)
                    menu_groupquery = db.GqlQuery("SELECT * FROM MenuGroup WHERE menu_group_no = :menu_group_no " ,menu_group_no=menu_group_no)
                    menu_groups=menu_groupquery.fetch(None,0)
                    if not sorders or not menu_groups:
                        self.redirect('/chooseorderdrink')
                    else:
                        menu_group_name = menu_groups[0].menu_group_name
                        store_name = menu_groups[0].store_name
                        menuquery = db.GqlQuery("SELECT * FROM Menu WHERE store_name = :store_name and menu_group_name = :menu_group_name  " ,store_name = store_name,menu_group_name=menu_group_name)
                        smenus=menuquery.fetch(None,0)
                        menus = sorted(smenus, reverse=True , key=lambda smenus : smenus.menu_name)
                        self.render('orderdrink.html',username = self.user.name , admin = self.user.admin,chinesename = self.user.chinesename,order_name=order_name,store_name = store_name,create_user = create_user,menus = menus)
            elif self.user.stop:
                self.redirect('/stop')
        else:
            self.redirect('/')

    def post(self):        
        sorder_name = self.request.get("order_name")
        store_name = self.request.get("store_name")
        order_drink = self.request.get("order_drink")
        sorder_num = self.request.get("drink_num")        
        create_user = self.request.get("create_user")
        hot_cold = self.request.get('hot_cold')
        ice = self.request.get('ice')
        sugar = self.request.get('sugar')        
        order_paid = False
        have_error = False
        

        if not sorder_num.isdigit() or not sorder_name.isdigit() or not store_name or not order_drink or not create_user or not hot_cold or not ice or not sugar:
            self.redirect('/chooseorderdrink')
        else:
            if hot_cold!=u'冷' and hot_cold != u'熱':  
                self.redirect('/chooseorderdrink')
            elif ice != u'正常' and ice !=u'少冰'and ice!=u'去冰':
                self.redirect('/chooseorderdrink')
            elif sugar != u'正常' and sugar !=u'少糖'and sugar!=u'無糖':
                self.redirect('/chooseorderdrink')
            else:          
                order_name = int(sorder_name)
                orderquery = db.GqlQuery("SELECT * FROM Order WHERE order_name = :order_name and store_name = :store_name and create_user = :create_user " ,order_name = order_name , store_name = store_name,create_user = create_user)
                orders=orderquery.fetch(None,0)
                if not orders:
                    self.redirect('/chooseorderdrink')  
                else:                 
                    sdrink_price = order_drink.split(',')[1]
                    drink_name = order_drink.split(',')[0]
                    drink_price = int(sdrink_price)
                    order_num = int(sorder_num)

                    if order_num >= 4 or order_num < 1:
                        self.redirect('/chooseorderdrink')
                    else:
                        u = PersonalOrder.by_personalorder_name(order_name ,store_name,create_user , self.user.name,drink_name)
                        if u:
                            msg = u'已有此訂單'
                            menuquery = db.GqlQuery("SELECT * FROM Menu WHERE store_name = :store_name " ,store_name = store_name)
                            menus=menuquery.fetch(None,0)       
                            self.render('orderdrink.html', error = msg ,username = self.user.name , admin = self.user.admin,chinesename = self.user.chinesename,order_name = order_name,store_name = store_name,create_user = create_user,menus = menus )
                        else:
                            total = drink_price * order_num
                            u = PersonalOrder.order_drink(self.user.name,self.user.chinesename,order_name,store_name,create_user,drink_name,drink_price,hot_cold,ice,sugar,order_num,total,order_paid)
                            u.put()
                            self.redirect('/orderdrinksuccessful')

class OrderDrinkSuccessful(Handler):
    def get(self):
        if self.user :
            if not self.user.stop:
                self.render('orderdrinksuccessful.html',username = self.user.name , admin = self.user.admin,chinesename = self.user.chinesename)
            elif self.user.stop:
                self.redirect('/stop')
        else:
            self.redirect('/')

class ManageOrder(Handler):
    def get(self):
        if self.user :
            if not self.user.stop:
                orderquery = db.GqlQuery("SELECT * FROM Order WHERE create_user = :username " ,username = self.user.name)
                sorders=orderquery.fetch(None,0)
                orders = sorted(sorders, reverse=True , key=lambda sorders : sorders.order_name)
                self.render('manageorder.html',username = self.user.name , admin = self.user.admin,chinesename = self.user.chinesename , orders = orders)
            elif self.user.stop:
                self.redirect('/stop')
        else:
            self.redirect('/')

    def post(self):
        orderquery = db.GqlQuery("SELECT * FROM Order WHERE create_user = :username " ,username = self.user.name)
        sorders=orderquery.fetch(None,0)
        orders = sorted(sorders, reverse=True , key=lambda sorders : sorders.order_name)
        isopen = False
        for order in orders:
            
            order_name = str(order.order_name) + "isopen"
            changeisopen = self.request.get(order_name)

            if changeisopen == 'False' and order.isopen:
                q = db.GqlQuery("SELECT * FROM Order WHERE order_name = :order_name and  create_user = :username " ,order_name = order.order_name ,username = self.user.name )
                results = q.fetch(10)
                db.delete(results)

                u = Order.create_order(order.order_name , order.deadline_year , order.deadline_month,order.deadline_day,order.deadline_hour,order.deadline_minute,self.user.name,order.store_name,isopen)
                u.put()

        self.redirect('/manageordersuccessful')

class ManageOrderSuccessful(Handler):
    def get(self):
        if self.user :
            if not self.user.stop:
                self.render('manageordersuccessful.html',username = self.user.name , admin = self.user.admin,chinesename = self.user.chinesename)
            elif self.user.stop:
                self.redirect('/stop')
        else:
            self.redirect('/')   


class AccountOrder(Handler):
    def get(self):
        if self.user :
            if not self.user.stop:
                sorder_name = self.request.get('search')
                if sorder_name.isdigit():
                    order_name = int(sorder_name)
                    haveorderquery = db.GqlQuery("SELECT * FROM Order WHERE order_name = :order_name " ,order_name = order_name)
                    haveorders=haveorderquery.fetch(None,0)
                                        
                    if not haveorders:
                        self.redirect('/')
                    else:
                        creatusername = haveorders[0].create_user
                        store_name = haveorders[0].store_name
                        orderquery = db.GqlQuery("SELECT * FROM PersonalOrder WHERE create_user = :username and order_name = :order_name " ,username = creatusername , order_name = order_name)
                        sperorders=orderquery.fetch(None,0)
                        perorders = sorted(sperorders, reverse=False , key=lambda sperorders : sperorders.order_user)                    
                        count_order_name = []
                        count_order_num = []
                        find = 0
                        all_total = 0
                        for perorder in perorders:
                            if  perorder.hot_cold+' '+perorder.drink_name+' '+perorder.ice+' '+perorder.sugar not in count_order_name:
                                count_order_name.append(perorder.hot_cold+' '+perorder.drink_name+' '+perorder.ice+' '+perorder.sugar) 
                                count_order_num.append(perorder.order_num)
                            elif perorder.hot_cold+' '+perorder.drink_name+' '+perorder.ice+' '+perorder.sugar in count_order_name:
                                find = count_order_name.index(perorder.hot_cold+' '+perorder.drink_name+' '+perorder.ice+' '+perorder.sugar)
                                count_order_num[find] += perorder.order_num
                            all_total += perorder.total
                        self.render('accountorder.html',username = self.user.name , admin = self.user.admin,chinesename = self.user.chinesename,store_name = store_name,creatusername = creatusername,perorders = perorders , sorder_name = sorder_name , count_order_name = count_order_name , count_order_num = count_order_num , all_total = all_total)
                else:
                    self.redirect('/')
            elif self.user.stop:
                self.redirect('/stop')
        else:
            self.redirect('/')

    def post(self):
        sorder_name = self.request.get('search')
        if sorder_name.isdigit():
            order_name = int(sorder_name)

            haveorderquery = db.GqlQuery("SELECT * FROM Order WHERE create_user = :username and order_name = :order_name " ,username = self.user.name , order_name = order_name)
            haveorders=haveorderquery.fetch(None,0)

            if not haveorders:
                self.redirect('/notadmin')
            else:
                orderquery = db.GqlQuery("SELECT * FROM PersonalOrder WHERE create_user = :username and order_name = :order_name " ,username = self.user.name , order_name = order_name)
                perorders=orderquery.fetch(None,0)

                order_paid = True
                for perorder in perorders:                
                    perorder_name = perorder.drink_name + ',' + perorder.order_user+'order_paid'
                    change_order_paid = self.request.get(perorder_name)                

                    if change_order_paid == 'True' and not perorder.order_paid:
                        q = db.GqlQuery("SELECT * FROM PersonalOrder WHERE create_user = :username and order_name = :order_name and order_user = :order_user and drink_name = :drink_name " ,username = self.user.name , order_name = order_name , order_user = perorder.order_user , drink_name = perorder.drink_name)
                        results = q.fetch(10)
                        db.delete(results)

                        u = PersonalOrder.order_drink(perorder.order_user,perorder.order_user_chinesename,perorder.order_name,perorder.store_name,perorder.create_user,perorder.drink_name,perorder.drink_price,perorder.hot_cold,perorder.ice,perorder.sugar,perorder.order_num,perorder.total,order_paid)
                        u.put()
                self.redirect('/accountordersuccessful?search=%s' %order_name)

class AccountOrderSuccessful(Handler):
    def get(self):
        if self.user :
            if not self.user.stop:
                order_name = self.request.get('search')
                self.render('accountordersuccessful.html',username = self.user.name , admin = self.user.admin,chinesename = self.user.chinesename ,order_name = order_name)
            elif self.user.stop:
                self.redirect('/stop')
        else:
            self.redirect('/')

class About(Handler):
    def get(self):
        if self.user :
            if not self.user.stop:
                self.render('about.html',username = self.user.name , admin = self.user.admin,chinesename = self.user.chinesename)
            elif self.user.stop:
                self.redirect('/stop')
        else:
            self.redirect('/')
        
class SiteMap(Handler):
    def get(self):
        if self.user :
            if not self.user.stop:
                self.render('sitemap.html',username = self.user.name , admin = self.user.admin,chinesename = self.user.chinesename)
            elif self.user.stop:
                self.redirect('/stop')
        else:
            self.redirect('/')

class AddMenuGroup(Handler):
    def get(self):
        if self.user :
            if not self.user.stop:
                if self.user.admin:
                    storequery = db.GqlQuery("SELECT * FROM Store")
                    stores=storequery.fetch(None,0)
                    self.render('addmenugroup.html',username = self.user.name , admin = self.user.admin,chinesename = self.user.chinesename ,stores=stores)
                else:
                    self.redirect('/notadmin')
            elif self.user.stop:
                self.redirect('/stop')
        else:
            self.redirect('/')

    def post(self):
        store_name = self.request.get('store_name')
        storequery = db.GqlQuery("SELECT * FROM Store WHERE store_name=:store_name",store_name = store_name)
        stores=storequery.fetch(None,0)
        menu_group_name = self.request.get('menu_group_name')
        if not stores or not menu_group_name or len(menu_group_name)>15:
            storequery = db.GqlQuery("SELECT * FROM Store")
            stores=storequery.fetch(None,0)
            msg = u"請重試一遍"
            self.render('addmenugroup.html', error=msg,username = self.user.name , admin = self.user.admin,chinesename = self.user.chinesename,stores=stores)
        else:
            u = MenuGroup.by_menu_group_name(store_name,menu_group_name)
            if u:
                storequery = db.GqlQuery("SELECT * FROM Store")
                stores=storequery.fetch(None,0)
                msg = u'已有此群組'
                self.render('addmenugroup.html', error = msg ,username = self.user.name , admin = self.user.admin,chinesename = self.user.chinesename,stores=stores)
            else:
                menu_group_no = strftime(r'%Y%m%d%H%M%S')
                u = MenuGroup.add_menu_group(store_name , menu_group_name , menu_group_no)
                u.put()

                self.redirect('/addmenugroupsuccessful')

class AddMenuGroupSuccessful(Handler):
    def get(self):
        if self.user :
            if not self.user.stop:          
                self.render('addmenugroupsuccessful.html',username = self.user.name , admin = self.user.admin,chinesename = self.user.chinesename)
            elif self.user.stop:
                self.redirect('/stop')
        else:
            self.redirect('/')

class ViewMenuGroup(Handler):
    def get(self):
        if self.user :
            if not self.user.stop:
                menugroupquery=db.GqlQuery("SELECT * FROM MenuGroup")
                smenugroups=menugroupquery.fetch(None,0)
                menu_groups = sorted(smenugroups, reverse=True , key=lambda smenugroups : smenugroups.store_name)
                self.render('viewmenugroup.html',username = self.user.name , admin = self.user.admin,chinesename = self.user.chinesename,menu_groups = menu_groups)
            elif self.user.stop:
                self.redirect('/stop')
        else:
            self.redirect('/')

class Stop(Handler):
    def get(self):
        if self.user :
            if self.user.stop:            
                self.render('stop.html',username = self.user.name , admin = self.user.admin,chinesename = self.user.chinesename,stop_admin=self.user.stop_admin)
        else:
            self.redirect('/')

class AccountUser(Handler):
    def get(self):
        if self.user :
            if not self.user.stop:
                if self.user.admin:
                    userquery = db.GqlQuery("SELECT * FROM User ")
                    users=userquery.fetch(None,0)
                    self.render('accountuser.html',username = self.user.name , admin = self.user.admin,chinesename = self.user.chinesename,users=users)
                else:
                    self.redirect('/notadmin')
            elif self.user.stop:
                self.redirect('/stop')
        else:
            self.redirect('/')
    def post(self):
        userquery=db.GqlQuery("SELECT * FROM User")
        users=userquery.fetch(None,0)
        for user in users:
            change = self.request.get(user.name+',stop')
            if not user.stop and  change =='True':
                userquery = db.GqlQuery("SELECT * FROM User WHERE name = :username",username = user.name)
                results = userquery.fetch(10)
                db.delete(results)

                u = User.changeregister(user.name,user.pw_hash,user.chinesename,user.admin,True,self.user.name)
                u.put()
            elif user.stop and not change:
                userquery = db.GqlQuery("SELECT * FROM User WHERE name = :username",username = user.name)
                results = userquery.fetch(10)
                db.delete(results)

                u = User.changeregister(user.name,user.pw_hash,user.chinesename,user.admin,False,' ')
                u.put()

        self.redirect('/accountusersuccessful')   

class AccountUserSuccessful(Handler):
    def get(self):
        if self.user :
            if not self.user.stop:
                if self.user.admin:                
                    self.render('accountusersuccessful.html',username = self.user.name , admin = self.user.admin,chinesename = self.user.chinesename)
                else:
                    self.redirect('/notadmin')
            elif self.user.stop:
                self.redirect('/stop')
        else:
            self.redirect('/') 

class MyDrink(Handler):
    def get(self):        
        if self.user :
            if not self.user.stop:       
                    drinkquery=db.GqlQuery("SELECT * FROM PersonalOrder WHERE order_user=:username",username = self.user.name)
                    sdrinks=drinkquery.fetch(None,0)  
                    drinks = sorted(sdrinks, reverse=True , key=lambda sdrinks : sdrinks.order_name)                
                    self.render('mydrink.html',username = self.user.name , admin = self.user.admin,chinesename = self.user.chinesename,drinks = drinks)                
            elif self.user.stop:
                self.redirect('/stop')
        else:
            self.redirect('/') 
            
app = webapp2.WSGIApplication([('/', MainPage),
                                ('/login',Login),
                                ('/welcome', Welcome),
                                ('/signup',Register),
                                ('/changepassword',ChangePassword),
                                ('/changepasswordsuccessful',ChangePasswordSuccessful),
                                ('/logout',Logout),
                                ('/notadmin',NotAdmin),
                                ('/addmenu',AddMenu),
                                ('/addmenusuccessful',AddMenuSuccessful),                                
                                ('/viewmenu',ViewMenu),
                                ('/addstore',AddStore),
                                ('/addstoresuccessful',AddStoreSuccessful),                                
                                ('/viewstore',ViewStore),
                                ('/createorder',CreateOrder),
                                ('/createordersuccessful',CreateOrderSuccessful),
                                ('/vieworder',ViewOrder),
                                ('/chooseorderdrink',ChooseOrderDrink),
                                ('/choosemenugroup',ChooseMenuGroup),
                                ('/orderdrink',OrderDrink),
                                ('/orderdrinksuccessful',OrderDrinkSuccessful),
                                ('/manageorder',ManageOrder),
                                ('/manageordersuccessful',ManageOrderSuccessful),
                                ('/accountorder',AccountOrder),
                                ('/accountordersuccessful' , AccountOrderSuccessful),
                                ('/about' , About),
                                ('/addmenugroup' , AddMenuGroup),
                                ('/addmenugroupsuccessful',AddMenuGroupSuccessful),
                                ('/viewmenugroup' , ViewMenuGroup),
                                ('/stop',Stop),
                                ('/accountuser',AccountUser),
                                ('/accountusersuccessful',AccountUserSuccessful),
                                ('/mydrink',MyDrink)
                                ],
                                debug=debug)