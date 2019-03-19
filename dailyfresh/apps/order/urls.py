from django.conf.urls import url
from apps.order.views import OrderInfoView, OrderCommitView, PayOrderView

urlpatterns = [
    url(r'^commit[/]?$', OrderCommitView.as_view(), name="commit"),
    url(r'^pay[/]?$', PayOrderView.as_view(), name="pay"),
    url(r'^$', OrderInfoView.as_view(), name="info"),

]
