from django.conf.urls import url
from apps.user.views import RegisterView, LoginView, ActiveView, LogoutView, UserInfoView, UserOrderView, UserAddressView

urlpatterns = [
    url(r'^register$', RegisterView.as_view(), name='register'),
    url(r'^active/(?P<token>.*)', ActiveView.as_view(), name='active'),
    url(r'^login$', LoginView.as_view(), name='login'),
    url(r'^logout$', LogoutView.as_view(), name='logout'),
    url(r'^info$', UserInfoView.as_view(), name='info'),
    url(r'^order/(?P<page>\d+)$', UserOrderView.as_view(), name='order'),
    url(r'^address$', UserAddressView.as_view(), name='address'),
]
