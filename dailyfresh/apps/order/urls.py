from django.conf.urls import url
from apps.order.views import OrderInfoView, OrderCommitView

urlpatterns = [
    url(r'^commit[/]?$', OrderCommitView.as_view(), name="commit"),
    url(r'^$', OrderInfoView.as_view(), name="info"),

]
