from django.conf.urls import url
from apps.cart.views import AddCartView, CartInfoView

urlpatterns = [
    url(r'^add[/]?$', AddCartView.as_view(), name="add"),
    url(r'^$', CartInfoView.as_view(), name="show"),
]
