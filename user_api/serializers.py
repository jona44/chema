from rest_framework import serializers
from user.models import Profile
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ('id', 'user', 'profile_pic', 'bio', 'phone', 'address', 'first_name', 'surname')

    def to_representation(self, instance):
        # Override the to_representation method to include the profile picture URL
        representation = super().to_representation(instance)
        representation['profile_pic'] = instance.profile_pic.url if instance.profile_pic else None
        return representation



class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    email = serializers.EmailField(required=True)
    username = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1','password2')

    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data.get('password'))
        return super(UserRegistrationSerializer, self).create(validated_data)

    def update(self, instance, validated_data):
        instance.email = validated_data.get('email', instance.email)
        instance.username = validated_data.get('username', instance.username)
        if validated_data.get('password'):
            instance.password = make_password(validated_data.get('password'))
        instance.save()
        return instance
