from rest_framework import serializers
from user.models import Profile


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ('id', 'user', 'profile_pic', 'bio', 'phone', 'address', 'first_name', 'surname')

    def to_representation(self, instance):
        # Override the to_representation method to include the profile picture URL
        representation = super().to_representation(instance)
        representation['profile_pic'] = instance.profile_pic.url if instance.profile_pic else None
        return representation
