# serializers.py in your existing app

from rest_framework import serializers
from chema.models import *  # Import your model
from user_api.serializers import ProfileSerializer


           

class GroupSerializer(serializers.ModelSerializer):
    admin = ProfileSerializer(read_only=True)

    class Meta:
        model = Group
        fields = '__all__'
        
class GroupMembershipSerializer(serializers.ModelSerializer):
    member = ProfileSerializer(read_only=True)
    group = GroupSerializer(read_only=True)
    class Meta:
        model = GroupMembership
        fields = ['member', 'group', 'is_admin', 'date_joined']
        

class PostSerializer(serializers.ModelSerializer):
    author = ProfileSerializer(read_only=True)

    class Meta:
        model = Post
        fields = '__all__'

class CommentSerializer(serializers.ModelSerializer):
    author = ProfileSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = '__all__'

class ReplySerializer(serializers.ModelSerializer):
    author = ProfileSerializer(read_only=True)

    class Meta:
        model = Reply
        fields = '__all__'

class DependentSerializer(serializers.ModelSerializer):
    guardian = ProfileSerializer(read_only=True)

    class Meta:
        model = Dependent
        fields = '__all__'