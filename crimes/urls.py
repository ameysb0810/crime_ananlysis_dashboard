from django.urls import path
from django.shortcuts import redirect
from . import views

urlpatterns = [
    path('', lambda r: redirect('dashboard'), name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('crimes/', views.crime_list, name='crime_list'),
    path('crimes/add/', views.crime_add, name='crime_add'),
    path('crimes/edit/<int:pk>/', views.crime_edit, name='crime_edit'),
    path('crimes/delete/<int:pk>/', views.crime_delete, name='crime_delete'),
    path('crimes/upload/', views.csv_upload, name='csv_upload'),
    path('map/', views.map_view, name='map_view'),
]
