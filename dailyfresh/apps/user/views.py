from django.shortcuts import render, redirect
from django.views.generic import View
from django.http import HttpResponse
from django.core.urlresolvers import reverse
from django.conf import settings
from django.contrib.auth import authenticate, login
from user.models import User
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired
from celery_tasks.tasks import send_register_active_email
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
        response = redirect(reverse("user:login"))
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
