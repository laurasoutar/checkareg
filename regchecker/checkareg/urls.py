from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.get_reg, name='get_reg'),
    url(r'^$', views.get_reg, name='confirmation'),
]