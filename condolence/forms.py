from django import forms
from .models import *
from chema.models import *


class ContributionForm(forms.ModelForm):
    class Meta:
        model = Contribution
        fields = ['contributing_member', 'amount', 'deceased_member']

    # def __init__(self, *args, **kwargs):
    #     super(ContributionForm, self).__init__(*args, **kwargs)
    #     # Filter the choices for deceased members to only include those marked as deceased
    #     self.fields['contributing_member'].queryset = Profile.objects.filter(groups__is_active=True)
    #     self.fields['deceased_member'].queryset = Deceased.objects.filter(group__is_active=True)

    #     # Exclude the contributing member if already in the contribution
    #     self.fields['contributing_member'].queryset = Profile.objects.exclude(
    #         pk__in=Contribution.objects.filter(group__is_active=True).values_list('contributing_member', flat=True)
    #     )



class DeceasedForm(forms.ModelForm):
    class Meta:
        model = Deceased
        fields =['deceased']
        
    def __init__(self, *args, **kwargs):
        super(DeceasedForm, self).__init__(*args, **kwargs)
        # Filter the choices for deceased members to only include those marked as deceased
        self.fields['deceased'].queryset = Profile.objects.filter(groups__is_active=True )