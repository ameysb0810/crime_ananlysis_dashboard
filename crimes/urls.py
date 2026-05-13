from django.urls import path
from django.shortcuts import redirect
from . import views

urlpatterns = [
    path('', lambda r: redirect('dashboard'), name='home'),
    path('admin-panel/', views.admin_panel, name='admin_panel'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('crimes/', views.crime_list, name='crime_list'),
    path('crimes/add/', views.crime_add, name='crime_add'),
    path('crimes/edit/<int:pk>/', views.crime_edit, name='crime_edit'),
    path('crimes/delete/<int:pk>/', views.crime_delete, name='crime_delete'),
    path('crimes/upload/', views.pdf_upload, name='pdf_upload'),
    path('map/', views.map_view, name='map_view'),
    path('crime/approve/<int:pk>/', views.approve_crime, name='approve_crime'),
path('crime/reject/<int:pk>/', views.reject_crime, name='reject_crime'),
path('pending/', views.pending_complaints, name='pending_complaints'),
path('api/crimes/', views.crime_api, name='crime_api'),
path(
    'approve-crime/<int:pk>/',
    views.approve_crime,
    name='approve_crime'
),

path(
    'reject-crime/<int:pk>/',
    views.reject_crime,
    name='reject_crime'
),

]
