from django import forms
from .models import CrimeRecord

from django import forms
from .models import CrimeRecord

class CrimeRecordForm(forms.ModelForm):

    class Meta:
        model = CrimeRecord

        fields = [
            'crime_type',
            'location_name',
            'description',
            'proof_file',
            'latitude',
            'longitude'
        ]

        widgets = {
            'description': forms.Textarea(
                attrs={
                    'rows': 3,
                    'class': 'form-control'
                }
            ),

            'latitude': forms.HiddenInput(),

            'longitude': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        for name, field in self.fields.items():

            if name not in ['latitude', 'longitude']:

                field.widget.attrs.setdefault(
                    'class',
                    'form-control'
                )


class PDFUploadForm(forms.Form):
    pdf_file = forms.FileField(
        label='Upload PDF File',
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,application/pdf'})
    )

    def clean_pdf_file(self):
        pdf_file = self.cleaned_data['pdf_file']
        if not pdf_file.name.lower().endswith('.pdf'):
            raise forms.ValidationError('Please upload a PDF file.')
        if pdf_file.content_type and pdf_file.content_type not in ['application/pdf', 'application/x-pdf']:
            raise forms.ValidationError('The selected file must be a valid PDF.')
        return pdf_file


class FilterForm(forms.Form):
    crime_type = forms.ChoiceField(
        choices=[('', 'All Types')] + list(CrimeRecord._meta.get_field('crime_type').choices),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    date_from = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}), required=False)
    date_to = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}), required=False)
    search = forms.CharField(
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Area or landmark'})
    )