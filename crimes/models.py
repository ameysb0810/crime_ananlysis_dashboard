from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings
from shapely.geometry import Point, shape
from pathlib import Path
import json


class CrimeRecord(models.Model):

    CRIME_TYPES = [
        ('theft', 'Theft'),
        ('assault', 'Assault'),
        ('robbery', 'Robbery'),
        ('murder', 'Murder'),
        ('fraud', 'Fraud'),
        ('vandalism', 'Vandalism'),
        ('drug_offense', 'Drug Offense'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    crime_type = models.CharField(
        max_length=20,
        choices=CRIME_TYPES
    )

    description = models.TextField()

    location_name = models.CharField(
        max_length=255,
        blank=True
    )

    latitude = models.FloatField()
    longitude = models.FloatField()

    date_time = models.DateTimeField(auto_now_add=True)

    reported_by = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    # ================= STATUS =================

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    admin_remark = models.TextField(
        blank=True,
        null=True
    )

    # ================= PROOF FILE =================

    proof_file = models.FileField(
        upload_to='proofs/',
        blank=True,
        null=True
    )

    # ================= VALIDATION =================

    def clean(self):

        # Latitude longitude validation
        if self.latitude is None or self.longitude is None:
            raise ValidationError(
                "Latitude & Longitude are required."
            )

        if not (-90 <= self.latitude <= 90):
            raise ValidationError("Invalid latitude")

        if not (-180 <= self.longitude <= 180):
            raise ValidationError("Invalid longitude")

        # Khargone boundary validation
        geojson_path = (
            Path(settings.BASE_DIR)
            / 'static'
            / 'maps'
            / 'khargone.geojson'
        )

        if geojson_path.exists():

            with open(geojson_path, encoding='utf-8') as f:
                geojson = json.load(f)

            polygon = shape(
                geojson['features'][0]['geometry']
            )

            point = Point(
                self.longitude,
                self.latitude
            )

            if not polygon.contains(point):
                raise ValidationError(
                    "Location must be inside Khargone"
                )

    def __str__(self):
        return f"{self.get_crime_type_display()} - {self.location_name}"