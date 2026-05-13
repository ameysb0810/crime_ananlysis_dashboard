from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.conf import settings
from pathlib import Path
from collections import Counter
import csv
import io
import json
import requests

from .models import CrimeRecord
from .forms import CrimeRecordForm, PDFUploadForm, FilterForm


# =========================
# CONFIG
# =========================
KHARGONE_CENTER_LATITUDE = 21.82
KHARGONE_CENTER_LONGITUDE = 75.61


# =========================
# UTIL FUNCTIONS
# =========================
def load_khargone_geojson():
    geojson_path = Path(settings.BASE_DIR) / 'static' / 'maps' / 'khargone.geojson'
    with geojson_path.open(encoding='utf-8') as f:
        return json.load(f)


def get_time_slot_label(dt):
    hour = dt.hour
    if 0 <= hour < 4:
        return '12 AM - 4 AM'
    if 4 <= hour < 8:
        return '4 AM - 8 AM'
    if 8 <= hour < 12:
        return '8 AM - 12 PM'
    if 12 <= hour < 16:
        return '12 PM - 4 PM'
    if 16 <= hour < 20:
        return '4 PM - 8 PM'
    return '8 PM - 12 AM'


def get_alert_level(count):
    if count >= 3:
        return 'red'
    if count >= 2:
        return 'yellow'
    return 'green'



def serialize_record(record):
    return {
        'id': record.id,
        'crime_type': record.crime_type,
        'crime_type_display': record.get_crime_type_display(),
        'latitude': record.latitude,
        'longitude': record.longitude,
        'location_name': record.location_name,
        'date_time': record.date_time.strftime('%d %b %Y, %I:%M %p'),
        'reported_by': record.reported_by.username if record.reported_by else 'N/A',
        'time_slot': get_time_slot_label(record.date_time),
    }


# =========================
# HOTSPOT LOGIC
# =========================
def build_alert_data(records):
    areas = {}
    slot_counter = Counter()

    for record in records:
        key = record.location_name.strip().lower()

        if key not in areas:
            areas[key] = {
                'location_name': record.location_name,
                'latitude_sum': 0.0,
                'longitude_sum': 0.0,
                'valid_points': 0,
                'count': 0,
                'crime_types': Counter(),
                'time_slots': Counter(),
                'latest_report': record.date_time,
            }

        area = areas[key]
        area['count'] += 1
        area['crime_types'][record.get_crime_type_display()] += 1

        slot = get_time_slot_label(record.date_time)
        area['time_slots'][slot] += 1
        slot_counter[slot] += 1

        if record.date_time > area['latest_report']:
            area['latest_report'] = record.date_time

        if -90 <= record.latitude <= 90 and -180 <= record.longitude <= 180:
            area['latitude_sum'] += record.latitude
            area['longitude_sum'] += record.longitude
            area['valid_points'] += 1

    hotspot_areas = []

    for area in areas.values():
        if area['valid_points'] == 0:
            continue

        top_crime, _ = area['crime_types'].most_common(1)[0]
        dominant_slot, dominant_count = area['time_slots'].most_common(1)[0]

        hotspot_areas.append({
            'location_name': area['location_name'],
            'latitude': round(area['latitude_sum'] / area['valid_points'], 6),
            'longitude': round(area['longitude_sum'] / area['valid_points'], 6),
            'report_count': area['count'],
            'alert_level': get_alert_level(area['count']),
            'top_crime': top_crime,
            'unsafe_time_slot': dominant_slot,
            'unsafe_time_slot_count': dominant_count,
            'latest_report': area['latest_report'].strftime('%d %b %Y, %I:%M %p'),
        })

    hotspot_areas.sort(key=lambda x: -x['report_count'])

    alert_summary = {
        'red_count': sum(1 for a in hotspot_areas if a['alert_level'] == 'red'),
        'yellow_count': sum(1 for a in hotspot_areas if a['alert_level'] == 'yellow'),
        'green_count': sum(1 for a in hotspot_areas if a['alert_level'] == 'green'),
    }

    risky_time_slots = [
        {'label': k, 'count': v}
        for k, v in slot_counter.most_common()
    ]

    return hotspot_areas, alert_summary, risky_time_slots


# =========================
# ADMIN CHECK
# =========================
def is_admin_user(user):
    return user.is_authenticated and user.is_staff


# =========================
# FILTERS
# =========================
def apply_crime_filters(records, form):
    if not form.is_valid():
        return records

    crime_type = form.cleaned_data.get('crime_type')
    date_from = form.cleaned_data.get('date_from')
    date_to = form.cleaned_data.get('date_to')
    search = form.cleaned_data.get('search')

    if crime_type:
        records = records.filter(crime_type=crime_type)

    if date_from:
        records = records.filter(date_time__date__gte=date_from)

    if date_to:
        records = records.filter(date_time__date__lte=date_to)

    if search:
        records = records.filter(location_name__icontains=search)

    return records


# =========================
# ADMIN PANEL
# =========================
from django.contrib.auth.models import User
from django.db.models import Count
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test

from .models import CrimeRecord


def is_admin_user(user):
    return user.is_staff


@user_passes_test(is_admin_user, login_url='/accounts/login/')
def admin_panel(request):

    users = User.objects.annotate(
        complaint_count=Count('crimerecord')
    ).order_by('-complaint_count')

    all_complaints = CrimeRecord.objects.select_related(
        'reported_by'
    ).order_by('-date_time')

    recent_complaints = CrimeRecord.objects.select_related(
        'reported_by'
    ).order_by(
        'status',
        '-date_time'
    )[:20]

    pending_count = CrimeRecord.objects.filter(
        status='pending'
    ).count()

    approved_count = CrimeRecord.objects.filter(
        status='approved'
    ).count()

    rejected_count = CrimeRecord.objects.filter(
        status='rejected'
    ).count()

    return render(request, 'crimes/admin_panel.html', {

        'total_users': users.count(),

        'active_users': users.filter(
            is_active=True
        ).count(),

        'staff_users': users.filter(
            is_staff=True
        ).count(),

        'total_complaints': CrimeRecord.objects.count(),

        'recent_complaints': recent_complaints,

        'all_complaints': all_complaints,

        'pending_count': pending_count,

        'approved_count': approved_count,

        'rejected_count': rejected_count,

        'users': users,
    })


"""
=========================
APPROVE CRIME
=========================
"""

@user_passes_test(is_admin_user, login_url='/accounts/login/')
def approve_crime(request, pk):

    crime = get_object_or_404(
        CrimeRecord,
        id=pk
    )

    crime.status = 'approved'

    crime.save()

    return redirect('admin_panel')


"""
=========================
REJECT CRIME
=========================
"""

@user_passes_test(is_admin_user, login_url='/accounts/login/')
def reject_crime(request, pk):

    crime = get_object_or_404(
        CrimeRecord,
        id=pk
    )

    crime.status = 'rejected'

    crime.save()

    return redirect('admin_panel')

# =========================
# DASHBOARD (ONLY APPROVED)
# =========================
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Count
from django.db.models.functions import TruncMonth
import json

@login_required
def dashboard(request):

    records = CrimeRecord.objects.all()

    """
    =========================
    CRIME TYPE GRAPH
    =========================
    """

    type_data = (
        records
        .values('crime_type')
        .annotate(count=Count('id'))
        .order_by('-count')
    )

    max_type = max(
        [x['count'] for x in type_data],
        default=1
    )

    type_chart = []

    for item in type_data:

        type_chart.append({

            'label':
                item['crime_type']
                .replace('_', ' ')
                .title(),

            'count':
                item['count'],

            'height':
                (item['count'] / max_type) * 100
        })

    """
    =========================
    MONTHLY TREND
    =========================
    """

    monthly = (
        records
        .annotate(month=TruncMonth('date_time'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )

    max_month = max(
        [x['count'] for x in monthly],
        default=1
    )

    month_chart = []

    for item in monthly:

        if item['month']:

            month_chart.append({

                'label':
                    item['month'].strftime('%b %Y'),

                'count':
                    item['count'],

                'width':
                    (item['count'] / max_month) * 100
            })

    """
    =========================
    ALERT DATA
    =========================
    """

    hotspot_areas, alert_summary, risky_time_slots = build_alert_data(records)

    """
    =========================
    RECENT CRIMES
    =========================
    """

    recent_crimes = (
        records
        .order_by('-date_time')[:10]
    )

    """
    =========================
    RENDER
    =========================
    """

    return render(request, 'crimes/dashboard.html', {

        'total_crimes': records.count(),

        'type_chart': type_chart,

        'month_chart': month_chart,

        'hotspot_areas': hotspot_areas[:5],

        'alert_summary': alert_summary,

        'risky_time_slots': risky_time_slots[:5],

        'recent_crimes': recent_crimes,
    })

# =========================
# MAP VIEW (ONLY APPROVED)
# =========================
@login_required
def map_view(request):

    records = CrimeRecord.objects.filter(status='approved')

    serialized_records = [serialize_record(r) for r in records]

    hotspot_areas, alert_summary, risky_time_slots = build_alert_data(records)

    return render(request, 'crimes/map.html', {
        'map_data': json.dumps(serialized_records),
        'hotspot_areas': hotspot_areas,
        'hotspot_areas_json': json.dumps(hotspot_areas),
        'khargone_geojson': json.dumps(load_khargone_geojson()),
        'alert_summary': alert_summary,
        'risky_time_slots': risky_time_slots[:5],
    })


# =========================
# CRIME LIST (ONLY APPROVED)
# =========================
@login_required
def crime_list(request):

    form = FilterForm(request.GET)

    records = apply_crime_filters(
        CrimeRecord.objects.filter(status='approved'),
        form
    )

    paginator = Paginator(records, 10)
    crimes = paginator.get_page(request.GET.get('page'))

    return render(request, 'crimes/crime_list.html', {
        'crimes': crimes,
        'form': form
    })


# =========================
# ADD CRIME (PENDING BY DEFAULT)
# =========================
@login_required
def crime_add(request):

    if request.method == 'POST':

        form = CrimeRecordForm(request.POST, request.FILES)

        if form.is_valid():

            crime = form.save(commit=False)
            crime.reported_by = request.user
            crime.status = 'pending'

            crime.latitude = request.POST.get('latitude')
            crime.longitude = request.POST.get('longitude')

            crime.save()

            messages.success(request, "Complaint submitted for verification.")
            return redirect('crime_list')

    else:
        form = CrimeRecordForm()

    return render(request, 'crimes/crime_form.html', {
        'form': form,
        'khargone_geojson': json.dumps(load_khargone_geojson())
    })


@login_required
def crime_edit(request, pk):
    crime = get_object_or_404(CrimeRecord, pk=pk)

    if crime.reported_by != request.user:
        messages.error(request, "You can edit only your own complaint.")
        return redirect('crime_list')

    if request.method == 'POST':
        form = CrimeRecordForm(request.POST, instance=crime)

        lat = request.POST.get('latitude')
        lng = request.POST.get('longitude')

        if not lat or not lng:
            messages.error(request, "Select location on map")
            return render(request, 'crimes/crime_form.html', {'form': form, 'action': 'Edit'})

        if form.is_valid():
            crime = form.save(commit=False)
            crime.latitude = float(lat)
            crime.longitude = float(lng)

            crime.full_clean()
            crime.save()

            messages.success(request, "Updated successfully")
            return redirect('crime_list')

    else:
        form = CrimeRecordForm(instance=crime)

    return render(request, 'crimes/crime_form.html', {
        'form': form,
        'action': 'Edit'
    })


@login_required
def crime_delete(request, pk):

    crime = get_object_or_404(CrimeRecord, pk=pk)

    # only owner can delete
    if crime.reported_by != request.user:
        messages.error(request, "You can delete only your own complaint.")
        return redirect('crime_list')

    if request.method == 'POST':
        crime.delete()
        messages.success(request, "Deleted successfully")
        return redirect('crime_list')

    return render(request, 'crimes/crime_confirm_delete.html', {
        'crime': crime
    })


@user_passes_test(is_admin_user, login_url='/accounts/login/')
def approve_crime(request, pk):
    crime = get_object_or_404(CrimeRecord, pk=pk)
    crime.status = "approved"
    crime.save()
    return redirect('admin_panel')


@user_passes_test(is_admin_user, login_url='/accounts/login/')
def reject_crime(request, pk):
    crime = get_object_or_404(CrimeRecord, pk=pk)
    crime.status = "rejected"
    crime.save()
    return redirect('admin_panel')



@login_required
def pending_complaints(request):
    complaints = CrimeRecord.objects.filter(status='pending')
    return render(request, 'crimes/pending.html', {
        'complaints': complaints
    })



from django.http import JsonResponse

@login_required
def crime_api(request):

    crimes = CrimeRecord.objects.filter(status='approved')

    data = []

    for c in crimes:
       data.append({
    "lat": c.latitude,
    "lng": c.longitude,
    "type": c.get_crime_type_display(),
    "location": c.location_name,
    "proof_url": c.proof_file.url if c.proof_file else ""
})

    return JsonResponse(data, safe=False)



@login_required
def pdf_upload(request):

    if request.method == 'POST':

        form = PDFUploadForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            messages.success(
                request,
                "PDF uploaded successfully"
            )

            return redirect('crime_list')

    else:

        form = PDFUploadForm()

    return render(
        request,
        'crimes/pdf_upload.html',
        {
            'form': form
        }
    )