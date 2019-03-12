# 使用celery
from django.core.mail import send_mail
from django.conf import settings
from celery import Celery


# 在任务处理者一端加入代码
# import os
# import django
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dailyfresh.settings")
# django.setup()

app = Celery("celery_tasks.tasks", broker="redis://127.0.0.1:6379/8")


@app.task
def send_register_active_email(to_email, username, token):
    """发送激活邮件"""
    subject = "天天生鲜欢迎信息"
    message = ""
    sender = settings.EMAIL_FROM
    receiver = [to_email]
    html_message = ""
    html_message += '<h1>%s, 欢迎您成为天天生鲜注册会员</h1>'
    html_message += '请点击下面链接激活您的账户<br/>'
    html_message += '<a href="http://127.0.0.1:8000/user/active/%s">http://127.0.0.1:8000/user/active/%s</a>'
    html_message = html_message % (username, token, token)
    # print(html_message)

    send_mail(subject=subject, message=message, from_email=sender, recipient_list=receiver, html_message=html_message)
