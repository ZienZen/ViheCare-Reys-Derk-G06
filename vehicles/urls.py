from django.urls import path

from . import views

app_name = 'vehicles'

urlpatterns = [
    path('', views.vehicle_list, name='list'),
    path('add/', views.vehicle_create, name='add'),
    path('all/', views.admin_vehicle_list, name='admin_list'),
    path('<int:pk>/', views.vehicle_detail, name='detail'),
    path('<int:pk>/edit/', views.vehicle_update, name='edit'),
    path('<int:pk>/delete/', views.vehicle_delete, name='delete'),
]
