from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.conf import settings
from pathlib import Path
from collections import Counter
import json, csv, io
from .models import CrimeRecord
from .forms import CrimeRecordForm, CSVUploadForm, FilterForm


def load_khargone_geojson():
    geojson_path = Path(settings.BASE_DIR) / 'static' / 'maps' / 'khargone.geojson'
    with geojson_path.open(encoding='utf-8') as geojson_file:
        return json.load(geojson_file)


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
        slot_label = get_time_slot_label(record.date_time)
        area['time_slots'][slot_label] += 1
        slot_counter[slot_label] += 1
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

        dominant_slot, dominant_slot_count = area['time_slots'].most_common(1)[0]
        top_crime, _ = area['crime_types'].most_common(1)[0]
        hotspot_areas.append({
            'location_name': area['location_name'],
            'latitude': round(area['latitude_sum'] / area['valid_points'], 6),
            'longitude': round(area['longitude_sum'] / area['valid_points'], 6),
            'report_count': area['count'],
            'alert_level': get_alert_level(area['count']),
            'top_crime': top_crime,
            'unsafe_time_slot': dominant_slot,
            'unsafe_time_slot_count': dominant_slot_count,
            'latest_report': area['latest_report'].strftime('%d %b %Y, %I:%M %p'),
        })

    hotspot_areas.sort(key=lambda item: (-item['report_count'], item['location_name'].lower()))
    alert_summary = {
        'red_count': sum(1 for area in hotspot_areas if area['alert_level'] == 'red'),
        'yellow_count': sum(1 for area in hotspot_areas if area['alert_level'] == 'yellow'),
        'green_count': sum(1 for area in hotspot_areas if area['alert_level'] == 'green'),
    }
    risky_time_slots = [
        {'label': label, 'count': count}
        for label, count in slot_counter.most_common()
    ]

    return hotspot_areas, alert_summary, risky_time_slots

@login_required
def dashboard(request):
    records = CrimeRecord.objects.all()
    type_data = records.values('crime_type').annotate(count=Count('id'))
    chart_labels = [d['crime_type'].replace('_', ' ').title() for d in type_data]
    chart_counts = [d['count'] for d in type_data]
    monthly = (records.annotate(month=TruncMonth('date_time'))
               .values('month').annotate(count=Count('id')).order_by('month'))
    month_labels = [m['month'].strftime('%b %Y') if m['month'] else '' for m in monthly]
    month_counts = [m['count'] for m in monthly]
    serialized_records = [serialize_record(record) for record in records]
    hotspot_areas, alert_summary, risky_time_slots = build_alert_data(records)
    context = {
        'total_crimes': records.count(),
        'chart_labels': json.dumps(chart_labels),
        'chart_counts': json.dumps(chart_counts),
        'month_labels': json.dumps(month_labels),
        'month_counts': json.dumps(month_counts),
        'map_data': json.dumps(serialized_records),
        'recent_crimes': records[:5],
        'community_reports': records[:10],
        'hotspot_areas': hotspot_areas[:5],
        'alert_summary': alert_summary,
        'risky_time_slots': risky_time_slots[:5],
    }
    return render(request, 'crimes/dashboard.html', context)

@login_required
def crime_list(request):
    form = FilterForm(request.GET)
    records = CrimeRecord.objects.all()
    if form.is_valid():
        if form.cleaned_data['crime_type']:
            records = records.filter(crime_type=form.cleaned_data['crime_type'])
        if form.cleaned_data['date_from']:
            records = records.filter(date_time__date__gte=form.cleaned_data['date_from'])
        if form.cleaned_data['date_to']:
            records = records.filter(date_time__date__lte=form.cleaned_data['date_to'])
        if form.cleaned_data['search']:
            records = records.filter(location_name__icontains=form.cleaned_data['search'])
    paginator = Paginator(records, 10)
    crimes = paginator.get_page(request.GET.get('page'))
    return render(request, 'crimes/crime_list.html', {'crimes': crimes, 'form': form})

@login_required
def crime_add(request):
    if request.method == 'POST':
        form = CrimeRecordForm(request.POST)
        if form.is_valid():
            crime = form.save(commit=False)
            crime.reported_by = request.user
            crime.save()
            messages.success(request, 'Crime record added successfully!')
            return redirect('crime_list')
    else:
        form = CrimeRecordForm()
    return render(request, 'crimes/crime_form.html', {'form': form, 'action': 'Add'})

@login_required
def crime_edit(request, pk):
    crime = get_object_or_404(CrimeRecord, pk=pk)
    if crime.reported_by != request.user:
        messages.error(request, 'You can edit only your own complaint.')
        return redirect('crime_list')
    if request.method == 'POST':
        form = CrimeRecordForm(request.POST, instance=crime)
        if form.is_valid():
            form.save()
            messages.success(request, 'Record updated successfully!')
            return redirect('crime_list')
    else:
        form = CrimeRecordForm(instance=crime)
    return render(request, 'crimes/crime_form.html', {'form': form, 'action': 'Edit'})

@login_required
def crime_delete(request, pk):
    crime = get_object_or_404(CrimeRecord, pk=pk)
    if crime.reported_by != request.user:
        messages.error(request, 'You can delete only your own complaint.')
        return redirect('crime_list')
    if request.method == 'POST':
        crime.delete()
        messages.success(request, 'Record deleted.')
        return redirect('crime_list')
    return render(request, 'crimes/crime_confirm_delete.html', {'crime': crime})

@login_required
def csv_upload(request):
    if request.method == 'POST':
        form = CSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            decoded = request.FILES['csv_file'].read().decode('utf-8')
            reader = csv.DictReader(io.StringIO(decoded))
            count = 0
            for row in reader:
                try:
                    CrimeRecord.objects.create(
                        crime_type=row['crime_type'],
                        date_time=row['date_time'],
                        location_name=row['location_name'],
                        latitude=float(row['latitude']),
                        longitude=float(row['longitude']),
                        description=row.get('description', ''),
                        reported_by=request.user,
                    )
                    count += 1
                except Exception:
                    continue
            messages.success(request, f'{count} records imported successfully!')
            return redirect('crime_list')
    else:
        form = CSVUploadForm()
    return render(request, 'crimes/csv_upload.html', {'form': form})

@login_required
def map_view(request):
    records = CrimeRecord.objects.all()
    serialized_records = [serialize_record(record) for record in records]
    hotspot_areas, alert_summary, risky_time_slots = build_alert_data(records)
    context = {
        'map_data': json.dumps(serialized_records),
        'khargone_geojson': json.dumps(load_khargone_geojson()),
        'hotspot_areas': json.dumps(hotspot_areas),
        'alert_summary': alert_summary,
        'risky_time_slots': risky_time_slots[:5],
    }
    return render(request, 'crimes/map.html', context)
