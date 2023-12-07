from rest_framework import serializers
from condolence.models import Contribution, Deceased
from chema_api.serializers import GroupMembershipSerializer, GroupSerializer  
from user_api.serializers import ProfileSerializer 

class ContributionSerializer(serializers.ModelSerializer):
    contributing_member = ProfileSerializer()
    group = GroupMembershipSerializer()

    class Meta:
        model = Contribution
        fields = '__all__'

class DeceasedSerializer(serializers.ModelSerializer):
    deceased = ProfileSerializer()
    group_admin = ProfileSerializer()

    class Meta:
        model = Deceased
        fields = '__all__'
