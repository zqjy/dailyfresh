# 使用celery
from django.core.mail import send_mail
from django.conf import settings
from celery import Celery
from django.template import loader, RequestContext


# 在任务处理者一端加入代码
import os
# import django
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dailyfresh.settings")
# django.setup()

from goods.models import GoodsType, IndexGoodsBanner, IndexPromotionBanner, IndexTypeGoodsBanner

app = Celery("celery_tasks.tasks", broker="redis://192.168.31.199:6379/8")


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

@app.task
def generate_static_index_html():
    # 获取商品分类
    types = GoodsType.objects.all()
    # 获取商品轮播图
    goods_banners = IndexGoodsBanner.objects.all().order_by("index")
    # 获取活动
    promotion_banners = IndexPromotionBanner.objects.all().order_by("index")
    # 获取各分类商品
    for type in types:
        title_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=0).order_by("index")
        image_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=1).order_by("index")
        type.title_banners = title_banners
        type.image_banners = image_banners
    # 获取购物车数量
    cart_count = 0

    context = {
        "types": types,
        "goods_banners": goods_banners,
        "promotion_banners": promotion_banners,
        "cart_count": cart_count,
    }
    # 加载模板返回模板对象
    temp = loader.get_template("static_index.html")
    # 渲染模板
    static_index_html = temp.render(context)

    save_path = os.path.join(settings.BASE_DIR, "static/index.html")
    with open(save_path, "w") as f:
        f.write(static_index_html)
