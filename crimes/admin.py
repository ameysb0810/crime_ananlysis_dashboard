from django.contrib import admin
from .models import CrimeRecord


@admin.register(CrimeRecord)
class CrimeRecordAdmin(admin.ModelAdmin):

    list_display = [
        'id',
        'crime_type',
        'location_name',
        'reported_by',
        'status',
        'date_time'
    ]

    list_filter = [
        'crime_type',
        'status',
        'date_time'
    ]

    search_fields = [
        'location_name',
        'description'
    ]

    date_hierarchy = 'date_time'

    actions = [
        'approve_crimes',
        'reject_crimes'
    ]

    def approve_crimes(self, request, queryset):

        queryset.update(status='approved')

    approve_crimes.short_description = (
        "Approve selected crimes"
    )

    def reject_crimes(self, request, queryset):

        queryset.update(status='rejected')

    reject_crimes.short_description = (
        "Reject selected crimes"
    )