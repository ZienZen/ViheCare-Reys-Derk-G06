from django.urls import path

from . import views

app_name = 'maintenance'

urlpatterns = [
    path('', views.record_list, name='list'),
    path('add/', views.record_create, name='add'),
    path('reminders/', views.reminder_list, name='reminders'),
    path('reminders/<int:pk>/done/', views.reminder_done, name='reminder_done'),
    path('all/', views.admin_record_list, name='admin_list'),
    path('<int:pk>/', views.record_detail, name='detail'),
    path('<int:pk>/edit/', views.record_update, name='edit'),
    path('<int:pk>/delete/', views.record_delete, name='delete'),
]
