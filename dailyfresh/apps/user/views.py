from django.shortcuts import render, redirect
from django.views.generic import View
from django.http import HttpResponse
from django.core.urlresolvers import reverse
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.core.paginator import Paginator
from user.models import User, Address
from goods.models import GoodsSKU
from order.models import OrderInfo, OrderGoods
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired
from celery_tasks.tasks import send_register_active_email
from utils.mixin import LoginRequiredMixin
from django_redis import get_redis_connection

import re


# /user/register
class RegisterView(View):
    """注册页面视图类"""

    def get(self, request):
        return render(request, 'register.html')

    def post(self, request):
        username = request.POST.get("user_name")
        pwd = request.POST.get("pwd")
        cpwd = request.POST.get("cpwd")
        email = request.POST.get("email")
        allow = request.POST.get("allow")

        if not all([username, pwd, cpwd, email]):
            return render(request, 'register.html', {'errmsg': "数据不完整"})
        if pwd != cpwd:
            return render(request, 'register.html', {'errmsg': "两次密码不一致"})
        if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'register.html', {'errmsg': "邮箱不正确"})
        if allow != 'on':
            return render(request, 'register.html', {'errmsg': "请阅读协议"})

        try:
            User.objects.get(username=username)
        except User.DoesNotExist:
            user = User.objects.create_user(username=username, password=pwd, email=email)
            user.is_active = 0
            user.save()
        except Exception as e:
            return render(request, 'register.html', {'errmsg': "保存用户出错, 错误信息: %s" % e})
        else:
            return render(request, 'register.html', {'errmsg': "用户名已存在"})

        # 创建用户激活链接
        serializer = Serializer(settings.SECRET_KEY, 3600)
        info = {
            "confirm": user.id,
        }
        token = serializer.dumps(info)
        token = token.decode()
        # 向用户发送激活邮件
        send_register_active_email.delay(email, username, token)

        return redirect(reverse("goods:index"))


class LoginView(View):
    """
    登录视图类
    """

    def get(self, request):
        username = request.COOKIES.get("username")
        checked = 'checked'
        if username is None:
            username = ''
            checked = ''
        return render(request, 'login.html', {'username': username, 'checked': checked})

    def post(self, request):
        username = request.POST.get("username")
        pwd = request.POST.get("pwd")

        if not all([username, pwd]):
            return render(request, 'login.html', {'errmsg': "请输入用户名和密码"})

        user = authenticate(username=username, password=pwd)

        if user is None:
            return render(request, 'login.html', {'errmsg': "用户名密码不正确"})
        if not user.is_active:
            return render(request, 'login.html', {'errmsg': "账户未激活"})

        login(request, user)

        remember = request.POST.get("remember")
        url = request.GET.get("next", reverse("goods:index"))
        response = redirect(url)
        if remember == 'on':
            response.set_cookie(key="username", value=username, max_age=7 * 24 * 3600)
        else:
            response.delete_cookie("username")

        return response
        # return redirect(reverse("goods:index"))


class ActiveView(View):
    """
    激活类
    """

    def get(self, request, token):
        serializer = Serializer(settings.SECRET_KEY, 3600)
        try:
            info = serializer.loads(token)
        except SignatureExpired:
            # 激活链接已过期
            return HttpResponse('激活链接已过期')
        except Exception as e:
            return HttpResponse("error: %s" % e)
        else:
            user_id = info.get("confirm")
            user = User.objects.get(id=user_id)
            user.is_active = 1
            user.save()
        return redirect(reverse("goods:index"))


class LogoutView(View):
    """
    用户注销类
    """

    def get(self, request):
        logout(request)

        return redirect(reverse("goods:index"))


class UserInfoView(LoginRequiredMixin, View):
    """
    用户信息视图类
    """

    def get(self, request):
        address = Address.objects.get_default_address(request.user)

        conn = get_redis_connection("default")
        user = request.user
        history_key = "history_%d" % user.id
        sku_ids = conn.lrange(history_key, 0, 4)
        goods_li = []
        for id in sku_ids:
            goods = GoodsSKU.objects.get(id=id)
            goods_li.append(goods)
        return render(request, 'user_center_info.html', {"page": "user", "address": address, "goods_li": goods_li})


class UserOrderView(LoginRequiredMixin, View):
    """
    用户信息视图类
    """

    def get(self, request, page):

        user = request.user
        order_li = OrderInfo.objects.filter(user=user)
        for order in order_li:
            # print("order_id, ", order.order_id)
            goods_order_li = OrderGoods.objects.filter(order=order)
            for goods in goods_order_li:
                goods.amount = goods.count * goods.price
            order.status_name = OrderInfo.ORDER_STATUS[order.order_status]
            order.goods_order_li = goods_order_li

        paginator = Paginator(order_li, 1)
        try:
            page = int(page)
        except:
            page = 1

        max_page = paginator.num_pages
        if page > max_page:
            page = 1

        order_page = paginator.page(page)

        # 自定义页码显示的数量
        if page <= 3:
            if max_page >= 5:
                pages = range(1, 6)
            else:
                pages = range(1, max_page + 1)
        elif page > max_page - 2:
            if max_page >= 5:
                pages = range(max_page - 4, max_page + 1)
            else:
                pages = range(1, max_page + 1)
        else:
            if page + 3 <= max_page:
                pages = range(page - 2, page + 3)
            else:
                pages = range(page - 2, max_page + 1)

        context = {
            "page": "order",
            "order_li": order_li,
            "pages": pages,
            "order_page": order_page,
        }
        return render(request, 'user_center_order.html', context)


class UserAddressView(LoginRequiredMixin, View):
    """
    用户信息视图类
    """

    def get(self, request):
        address = Address.objects.get_default_address(request.user)
        return render(request, 'user_center_site.html', {"page": "address", "address": address})

    def post(self, request):
        receiver = request.POST.get("receiver").strip()  # 收件人
        addr = request.POST.get("addr")  # 收件地址
        zip_code = request.POST.get("zip_code")  # 邮政编码
        phone = request.POST.get("phone")  # 手机号码
        user = request.user

        if not all([addr, phone]):
            return render(request, 'user_center_site.html', {"page": "address", "errmsg": "数据不完整"})
        if not re.match(r'^1[35678]\d{9}$', phone):
            return render(request, 'user_center_site.html', {"page": "address", "errmsg": "手机号码不正确"})

        if receiver is None or len(receiver) <= 0:
            receiver = user.username
        if zip_code is None:
            zip_code = ''

        address = Address.objects.get_default_address(user)

        if address is None:
            print("*" * 30, address)
            is_default = True
        else:
            print("*" * 30, address.is_default)
            is_default = False

        Address.objects.create(user=user,
                               receiver=receiver,
                               addr=addr,
                               zip_code=zip_code,
                               phone=phone,
                               is_default=is_default)
        # address = Address()
        # address.user = request.user
        # address.zip_code = zip_code
        # address.receiver = receiver
        # address.addr = addr
        # address.phone = phone
        # address.is_default = is_default

        # address.save()
        return redirect(reverse("user:address"))
