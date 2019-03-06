from django.shortcuts import render, redirect
from django.views.generic import View
from django.http import HttpResponse
from django.core.urlresolvers import reverse
import re


# Create your views here.
class RegisterView(View):
    """注册页面视图类"""

    def get(self, request):
        return render(request, 'register.html')

    def post(self, request):
        user_name = request.POST.get("user_name")
        pwd = request.POST.get("pwd")
        cpwd = request.POST.get("cpwd")
        email = request.POST.get("email")
        allow = request.POST.get("allow")

        errmsg = ""
        if not all([user_name, pwd, cpwd, email]):
            return render(request, 'register.html', {'errmsg': "数据不完整"})
        if pwd != cpwd:
            return render(request, 'register.html', {'errmsg': "两次密码不一致"})
        if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'register.html', {'errmsg': "邮箱不正确"})
        if allow != 'on':
            return render(request, 'register.html', {'errmsg': "请阅读协议"})

        return redirect(reverse("user:login"))


class LoginView(View):
    """
    登录视图类
    """

    def get(self, request):
        return render(request, 'login.html')

    def post(self, request):
        pass


class ActiveView(View):
    """
    激活类
    """

    def get(self, request, token):
        pass