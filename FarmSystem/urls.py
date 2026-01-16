"""
URL configuration for FarmSystem project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path
from core import views
from core.views import  planting_plan, harvest_record


urlpatterns = [
    path('admin/', admin.site.urls),
    path('register/', views.register_view, name='register'),
    path('', views.login_view, name='login'),
    path('add_record/', views.add_record, name='add_record'),
    path('update_status/<int:r_id>/', views.update_status, name='update_status'),
    path('harvest_record/', harvest_record),
    path('order_list/', views.order_list),
    path('admin_operation/', views.admin_operation, name='admin_operation'),
    path('logout/', views.logout_view, name='logout'),
    path('update_status/<str:p_id>/', views.update_status, name='update_status'),
    path('plot_admin/', views.plot_admin_view, name='plot_admin'),
    path('plot_staff/', views.plot_staff_view, name='plot_staff'),
    path('update_status/<str:p_id>/', views.update_status, name='update_status'),
    path('update_delivery/', views.update_delivery, name='update_delivery'),
    path('planting_plan/', views.planting_plan, name='planting_plan'),
    path('publish_plan/', views.planting_plan, name='publish_plan'),


]