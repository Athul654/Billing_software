from django.urls import path
from .views import products_view, add_product_view, edit_product_view, delete_product_view

urlpatterns = [
    path("", products_view, name="products"),
    path("add/", add_product_view, name="add_product"),
    path("edit/<int:product_id>/", edit_product_view, name="edit_product"),
    path("delete/<int:product_id>/", delete_product_view, name="delete_product"),
]
