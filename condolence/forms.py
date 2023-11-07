from django import forms
from .models import Contribution
from chema.models import *


class ContributionForm(forms.ModelForm):
    class Meta:
        model = Contribution
        fields = [ 'contributing_member', 'amount', 'deceased_member']

    def __init__(self, *args, **kwargs):
        super(ContributionForm, self).__init__(*args, **kwargs)
        # Filter the choices for deceased members to only include those marked as deceased
        self.fields['contributing_member'].queryset = Profile.objects.filter(groups__is_active=True )
        self.fields['deceased_member'].queryset = Profile.objects.filter(deceased=True)
