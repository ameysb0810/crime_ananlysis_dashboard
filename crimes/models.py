from django.db import models
from django.contrib.auth.models import User

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

class CrimeRecord(models.Model):
    crime_type = models.CharField(max_length=50, choices=CRIME_TYPES)
    date_time = models.DateTimeField()
    location_name = models.CharField(max_length=200)
    latitude = models.FloatField()
    longitude = models.FloatField()
    description = models.TextField(blank=True)
    reported_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_time']

    def __str__(self):
        return f"{self.get_crime_type_display()} at {self.location_name}"
