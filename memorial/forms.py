from django import forms
from .models import Memorial


class MemorialForm(forms.ModelForm):
    """Form for creating and editing memorials"""
    
    class Meta:
        model = Memorial
        fields = [
            'photo',
            'biography',
            'location_of_death',
            'burial_location',
            'funeral_date',
            'funeral_venue',
            'funeral_details',
            'is_public',
            'allow_condolences',
            'allow_memories',
            'allow_photos',
        ]
        
        widgets = {
            'biography': forms.Textarea(attrs={
                'rows': 6,
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'placeholder': 'Share their story, achievements, and the impact they had on others...'
            }),
            'location_of_death': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'placeholder': 'e.g., Cape Town, South Africa'
            }),
            'burial_location': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'placeholder': 'e.g., Maitland Cemetery'
            }),
            'funeral_date': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
            }),
            'funeral_venue': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'placeholder': 'e.g., St. Mary\'s Church, Main Road'
            }),
            'funeral_details': forms.Textarea(attrs={
                'rows': 4,
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'placeholder': 'Service details, dress code, parking information, etc.'
            }),
            'photo': forms.FileInput(attrs={
                'class': 'mt-1 block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100',
                'accept': 'image/*'
            }),
            'is_public': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-500 focus:ring-blue-500'
            }),
            'allow_condolences': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-500 focus:ring-blue-500'
            }),
            'allow_memories': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-500 focus:ring-blue-500'
            }),
            'allow_photos': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-500 focus:ring-blue-500'
            }),
        }
        
        labels = {
            'photo': 'Memorial Photo',
            'biography': 'Biography / Life Story',
            'location_of_death': 'Location of Death',
            'burial_location': 'Burial / Resting Place',
            'funeral_date': 'Funeral Date & Time',
            'funeral_venue': 'Funeral Venue',
            'funeral_details': 'Additional Funeral Details',
            'is_public': 'Make memorial publicly visible',
            'allow_condolences': 'Allow visitors to post condolences',
            'allow_memories': 'Allow visitors to share memories',
            'allow_photos': 'Allow visitors to upload photos',
        }
    
    def clean_biography(self):
        biography = self.cleaned_data.get('biography')
        if biography and len(biography) < 20:
            raise forms.ValidationError("Please provide a more detailed biography (at least 20 characters).")
        return biography    