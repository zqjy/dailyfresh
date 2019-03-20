from django.conf.urls import url
from apps.order.views import OrderInfoView, OrderCommitView, PayOrderView, CheckPayView, CommentView

urlpatterns = [
    url(r'^commit[/]?$', OrderCommitView.as_view(), name="commit"),
    url(r'^pay[/]?$', PayOrderView.as_view(), name="pay"),
    url(r'^check[/]?$', CheckPayView.as_view(), name="check"),
    url(r'^comment/(?P<order_id>.+)$', CommentView.as_view(), name="comment"),
    url(r'^$', OrderInfoView.as_view(), name="info"),

]
