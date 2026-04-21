from django.contrib import admin
from .models import CrimeRecord

@admin.register(CrimeRecord)
class CrimeRecordAdmin(admin.ModelAdmin):
    list_display = ['crime_type', 'location_name', 'date_time', 'reported_by', 'created_at']
    list_filter = ['crime_type', 'date_time']
    search_fields = ['location_name', 'description']
    date_hierarchy = 'date_time'
