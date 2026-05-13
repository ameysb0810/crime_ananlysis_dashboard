# Crime Data Analysis

Crime Data Analysis and Visualization Portal is a Django web app for recording crime complaints, viewing dashboards, and checking hotspot areas on a map.

## What It Does

- User registration and login
- Crime complaint add, edit, delete, and list pages
- Dashboard with complaint counts and trends
- Khargone map with alert areas
- PDF import for bulk complaint records
- Staff-only admin panel with user and complaint summaries

## Setup

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open the app at:

```text
http://127.0.0.1:8000/
```

## Useful Pages

- Dashboard: `/dashboard/`
- Records: `/crimes/`
- PDF upload: `/crimes/upload/`
- Map: `/map/`
- Custom admin panel: `/admin-panel/`
- Django admin: `/admin/`

## PDF Upload Format

The uploaded PDF must contain selectable text in this comma-separated format:

```text
crime_type,date_time,location_name,latitude,longitude,description
theft,2024-03-15 14:30:00,MG Road Khargone,22.05,75.18,Mobile snatched
```

Scanned image-only PDFs will not import unless they are converted to text first.
