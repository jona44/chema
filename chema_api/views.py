# views.py in your existing app

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from chema.models import Group
from .serializers import *


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def home_api(request):
    user_profile = request.user.profile

    # Fetch the active group, if it exists
    active_group = Group.objects.filter(is_active=True).first()

    if active_group is None:
        return Response({"detail": "No active group found."}, status=404)

    # Serialize the active group data
    group_serializer = GroupSerializer(active_group)
    group_data = group_serializer.data

    # Fetch posts and serialize them
    active_group_posts = Post.objects.filter(group=active_group).order_by('-created_at')[:5]
    post_serializer = PostSerializer(active_group_posts, many=True)
    group_data['posts'] = post_serializer.data

    # Fetch comments and serialize them
    active_group_comments = Comment.objects.filter(post__in=active_group_posts).order_by('-created_at')
    comment_serializer = CommentSerializer(active_group_comments, many=True)
    group_data['comments'] = comment_serializer.data

    # Fetch replies and serialize them
    active_group_replies = Reply.objects.filter(comment__in=active_group_comments).order_by('-created_at')[:3]
    reply_serializer = ReplySerializer(active_group_replies, many=True)
    group_data['replies'] = reply_serializer.data

    # Fetch contributions and serialize them
    contributions = Contribution.objects.filter(deceased_member_id__contributions_open=True, group=active_group)
    contribution_serializer = ContributionSerializer(contributions, many=True)
    group_data['contributions'] = contribution_serializer.data

    # Fetch deceased members and serialize them
    deceased = Deceased.objects.filter(group=active_group)
    deceased_serializer = DeceasedSerializer(deceased, many=True)
    group_data['deceased'] = deceased_serializer.data

    return Response({"group_data": group_data})



@api_view(['POST'])
@permission_classes([IsAuthenticated])  # Ensure the user is authenticated
def create_group_api(request):
    if request.method == 'POST':
        serializer = GroupSerializer(data=request.data)
        if serializer.is_valid():
            # Set the admin of the group to the current user's profile
            serializer.validated_data['admin'] = request.user.profile

            # Save the group and create a GroupMembership instance for the current user
            group = serializer.save()
            member_instance = group.members.create(member=request.user.profile, is_admin=True)

            # Return the serialized group data
            return Response(GroupSerializer(group).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])  # Ensure the user is authenticated
def create_post_api(request, group_id):
    group = Group.objects.get(id=group_id)

    # Check if the user is a member of the group
    if not group.members.filter(id=request.user.profile.id).exists():
        return Response({"detail": "You are not a member of this group."}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'POST':
        serializer = PostSerializer(data=request.data)
        if serializer.is_valid():
            # Set the post's author and group
            serializer.validated_data['author'] = request.user.profile
            serializer.validated_data['group'] = group

            # Save the post
            serializer.save()

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@api_view(['POST'])
@permission_classes([IsAuthenticated])  # Ensure the user is authenticated
def join_active_group_api(request):
    # Assuming there is only one active group, retrieve it
    active_group = Group.objects.filter(is_active=True).first()

    if active_group:
        # Check if the user is already a member of the group
        is_member = active_group.members.filter(member=request.user.profile).exists()

        if not is_member:
            # If the user is not already a member, create a new GroupMembership
            membership = GroupMembership(member=request.user.profile, group=active_group)
            membership.save()

            # Return the serialized membership data
            serializer = GroupMembershipSerializer(membership)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response({"detail": f"You are already a member of the '{active_group.name}' group."}, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response({"detail": "No active group found to join."}, status=status.HTTP_404_NOT_FOUND)
    