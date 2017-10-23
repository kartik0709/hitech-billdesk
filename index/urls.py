from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.home, name='home'),
    url(r'^register/$', views.register, name='register'),
    url(r'^login/$', views.login, name='login'),
    url(r'^logout/$', views.logout, name='logout'),
    url(r'^purchase/$', views.purchase, name='purchase'),
    url(r'^sell/$', views.sell, name='sell'),
    url(r'^stock/$', views.stock, name='stock'),
    url(r'^pdf/$', views.invoice, name='invoice'),
    url(r'^item_list/$', views.item_list, name='item_list'),
    url(r'^report/$', views.report, name='report'),
    url(r'^update/sale/price/$', views.update_sale_price, name='update_sale_price'),
    url(r'^ajax/validate_pid', views.validate_pid, name='validate_pid'),
    url(r'^ajax/pid_check', views.pid_check, name='pid_check'),
    url(r'^ajax/get_vendors', views.get_vendors, name='get_vendors'),
]
