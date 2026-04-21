from django import forms
from .models import CrimeRecord

class CrimeRecordForm(forms.ModelForm):
    class Meta:
        model = CrimeRecord
        fields = ['crime_type', 'date_time', 'location_name', 'latitude', 'longitude', 'description']
        widgets = {
            'date_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class CSVUploadForm(forms.Form):
    csv_file = forms.FileField(label='Upload CSV File')

class FilterForm(forms.Form):
    crime_type = forms.ChoiceField(
        choices=[('', 'All Types')] + list(CrimeRecord._meta.get_field('crime_type').choices),
        required=False
    )
    date_from = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False)
    date_to = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False)
    search = forms.CharField(required=False, max_length=100)
