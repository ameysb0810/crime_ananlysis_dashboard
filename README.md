# CDAVP - Crime Data Analysis & Visualization Portal

A Django-based web application for analyzing and visualizing crime data across regions.

## Features
- User authentication (login/register)
- Crime record management (CRUD operations)
- CSV data import
- Interactive crime statistics dashboard
- Geographic hotspot mapping
- Crime trend analysis

## Setup Instructions

1. Create virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run migrations:
   ```bash
   python manage.py makemigrations crimes
   python manage.py migrate
   ```

4. Create superuser:
   ```bash
   python manage.py createsuperuser
   ```

5. Start development server:
   ```bash
   python manage.py runserver
   ```

6. Open browser:
   ```
   http://127.0.0.1:8000
   ```

## Default Admin Panel
- Admin URL: `/admin/`
- Use superuser credentials

## Importing Sample Data
1. Navigate to: `/crimes/upload/`
2. Upload `sample_data.csv`
3. Data will be imported automatically
