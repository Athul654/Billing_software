from django.urls import path
from . import views

urlpatterns = [
    path("", views.billing_home, name="billing_home"),
    path("pos_billing/", views.pos_billing, name="pos_billing"),
    path("returns/",views.returns_page,name="returns"),
]