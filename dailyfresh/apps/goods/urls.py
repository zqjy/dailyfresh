from django.conf.urls import url
from apps.goods.views import IndexView
# from apps.goods import views

urlpatterns = [
    url(r'^', IndexView.as_view(), name='index'),
]
