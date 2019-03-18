from django.conf.urls import url
from apps.cart.views import AddCartView, CartInfoView, UpdateCartView, DelCartView

urlpatterns = [
    url(r'^add[/]?$', AddCartView.as_view(), name="add"),
    url(r'^update[/]?$', UpdateCartView.as_view(), name="update"),
    url(r'^del[/]?$', DelCartView.as_view(), name="del"),
    url(r'^$', CartInfoView.as_view(), name="show"),
]
