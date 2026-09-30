from django.urls import path
from .views import (
    login_view,
    admin_dashboard,
    staff_dashboard,
    logout_view,
    return_view,
    staff_view,
    add_staff_view,
    edit_staff_view,
    delete_staff_view,
)

urlpatterns = [
    path("", login_view, name="login"),
    path("admin-dashboard/", admin_dashboard, name="admin_dashboard"),
    path("staff-dashboard/", staff_dashboard, name="staff_dashboard"),
    path("logout/", logout_view, name="logout"),
    path("return-view/", return_view, name="return_view"),
    path("return-view/<int:return_id>/", return_view, name="return_detail"),
    path("staff/", staff_view, name="staff_view"),
    path("staff/add/", add_staff_view, name="add_staff"),
    path("staff/edit/<int:staff_id>/", edit_staff_view, name="edit_staff"),
    path("staff/delete/<int:staff_id>/", delete_staff_view, name="delete_staff"),
]
