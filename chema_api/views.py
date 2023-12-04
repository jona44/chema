# views.py in your existing app

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from chema.models import *
from .serializers import *
from condolence.models import Profile, Group, Deceased, Contribution
from .serializers import ProfileSerializer, GroupSerializer 
from condolence_api. serializers import DeceasedSerializer, ContributionSerializer



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
    


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def edit_post_api(request, post_id):
    post = Post.objects.get(id=post_id)

    # Check if the requesting user is the author of the post
    if request.user.profile != post.author:
        return Response({"detail": "You don't have permission to edit this post."}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'PUT':
        serializer = PostSerializer(post, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_post_api(request, post_id):
    post = Post.objects.get(id=post_id)

    # Check if the requesting user is the author of the post
    if request.user.profile != post.author:
        return Response({"detail": "You don't have permission to delete this post."}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'DELETE':
        post.delete()
        return Response({"detail": "Post deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
    
    

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_comment_api(request, post_id):
    # Retrieve the post based on the post_id
    post = Post.objects.get(id=post_id, approved=True)

    if request.method == 'POST':
        # Process the form submission
        serializer = CommentSerializer(data=request.data)
        if serializer.is_valid():
            # Set the comment's author and post
            serializer.validated_data['author'] = request.user.profile
            serializer.validated_data['post'] = post

            # Save the comment
            serializer.save()

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def edit_comment_api(request, comment_id):
    comment = Comment.objects.get(id=comment_id)

    # Check if the requesting user is the author of the comment
    if request.user.profile != comment.author:
        return Response({"detail": "You don't have permission to edit this comment."}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'PUT':
        serializer = CommentSerializer(comment, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
   

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_comment_api(request, comment_id):
    comment = Comment.objects.get(id=comment_id)

    # Check if the requesting user is the author of the comment
    if request.user.profile != comment.author:
        return Response({"detail": "You don't have permission to delete this comment."}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'DELETE':
        comment.delete()
        return Response({"detail": "Comment deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
    
   
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_member_api(request, group_id):
    # Get the group
    group = Group.objects.get(id=group_id)

    # Check if the current user is a member of the group
    if request.user.profile not in group.members.all():
        return Response({"detail": "You don't have permission to add a member to this group."}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'POST':
        # Process the form submission
        serializer = GroupMembershipSerializer(data=request.data)
        if serializer.is_valid():
            # Set the group and member based on the request
            serializer.validated_data['group'] = group
            serializer.validated_data['member'] = serializer.validated_data['member'].profile

            # Save the membership
            serializer.save()

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_dependent_api(request):
    user_profile = request.user.profile

    if request.method == 'POST':
        # Process the form submission
        serializer = DependentSerializer(data=request.data)
        if serializer.is_valid():
            # Set the guardian and user based on the request
            serializer.validated_data['guardian'] = user_profile

            # Save the dependent
            serializer.save()

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
   
 
    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_reply_api(request, comment_id):
    comment = Comment.objects.get(id=comment_id)

    if request.method == 'POST':
        # Process the form submission
        serializer = ReplySerializer(data=request.data)
        if serializer.is_valid():
            # Set the author and comment based on the request
            serializer.validated_data['author'] = request.user.profile
            serializer.validated_data['comment'] = comment

            # Save the reply
            serializer.save()

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# views.py in your existing app
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_reply_api(request, reply_id):
    reply = Reply.objects.get(id=reply_id)

    if request.user.profile == reply.author:
        reply.delete()
        return Response({"detail": "Reply deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
    return Response({"detail": "You don't have permission to delete this reply."}, status=status.HTTP_403_FORBIDDEN)




@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def edit_reply_api(request, reply_id):
    reply = Reply.objects.get(id=reply_id)

    if request.user.profile == reply.author:
        if request.method == 'PUT':
            # Process the form submission
            serializer = ReplySerializer(reply, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    return Response({"detail": "You don't have permission to edit this reply."}, status=status.HTTP_403_FORBIDDEN)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def group_detail_api(request, group_id):
    group = Group.objects.get(pk=group_id)
    deceased = Deceased.objects.filter(group__is_active=True, group=group).order_by('-date')

    # Use the reverse relationship to get the admin members
    group_admins = group.members.filter(groupmembership__is_admin=True)

    # Serialize the data
    group_serializer = GroupSerializer(group)
    deceased_serializer = DeceasedSerializer(deceased, many=True)

    # Construct the response data
    response_data = {
        'group': group_serializer.data,
        'group_admins': group_admins.values_list('id', flat=True),  # Assuming you want to include only the IDs of admins
        'members': group.members.values_list('id', flat=True),  # Assuming you want to include only the IDs of members
        'count_members': group.members.count(),
        'count_admins': group_admins.count(),
        'deceased': deceased_serializer.data,
    }

    return Response(response_data)


# views.py in your existing app


from .serializers import GroupSerializer, ProfileSerializer
from django.db.models import Q

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_api(request):
    query = request.GET.get('q', '')

    # Perform a search for both groups and members using Q objects
    groups = Group.objects.filter(Q(name__icontains=query) | Q(members__user__username__icontains=query))
    profiles = Profile.objects.filter(user__username__icontains=query)

    # Serialize the data
    group_serializer = GroupSerializer(groups, many=True)
    profile_serializer = ProfileSerializer(profiles, many=True)

    # Construct the response data
    response_data = {
        'groups': group_serializer.data,
        'profiles': profile_serializer.data,
    }

    return Response(response_data)
# views.py in your existing app



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def member_detail_api(request, group_id, member_id):
    member = Profile.objects.get(id=member_id)
    groups = member.groups.all()
    deceased = Deceased.objects.filter(deceased_id=member_id, group_id=group_id)
    contribution = Contribution.objects.filter(contributing_member=member_id, group__is_active=True)

    # Serialize the data
    member_serializer = ProfileSerializer(member)
    group_serializer = GroupSerializer(groups, many=True)
    deceased_serializer = DeceasedSerializer(deceased, many=True)
    contribution_serializer = ContributionSerializer(contribution, many=True)

    # Construct the response data
    response_data = {
        'member': member_serializer.data,
        'groups': group_serializer.data,
        'deceased': deceased_serializer.data,
        'contribution': contribution_serializer.data,
    }

    return Response(response_data)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_admin_api(request, group_id):
    group = Group.objects.get(id=group_id)

    # Check if the user is an admin of the group
    group_admins = group.get_admins()

    # Check if the current user is not in the list of admins
    if request.user.profile not in [admin.user.profile for admin in group_admins]:
        return Response({'detail': 'You do not have permission to add an admin to this group.'}, status=403)

    # Process the form submission
    serializer = GroupMembershipSerializer(data=request.data)
    if serializer.is_valid():
        user_id = serializer.validated_data['member']

        # Check if the selected user is a member of the group
        if group.members.filter(id=user_id).exists():
            # Check if the user is already an admin
            if not group.groupmembership_set.filter(member__id=user_id, is_admin=True).exists():
                # If not an admin, make the user an admin
                group_membership = group.groupmembership_set.get(member__id=user_id)
                group_membership.is_admin = True
                group_membership.save()

                return Response({'detail': 'User added as an admin successfully.'}, status=200)
            else:
                return Response({'detail': 'User is already an admin of the group.'}, status=400)
        else:
            return Response({'detail': 'Selected user is not a member of the group.'}, status=400)

    return Response(serializer.errors, status=400)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_group_api(request, group_id):
    # Get the group being toggled
    group_to_toggle = get_object_or_404(Group, id=group_id)

    # Toggle the group by setting it to active
    group_to_toggle.is_active = not group_to_toggle.is_active
    group_to_toggle.save()

    # Deactivate all other groups
    Group.objects.exclude(id=group_id).update(is_active=False)

    # Serialize the updated group
    group_serializer = GroupSerializer(group_to_toggle)

    # Construct the response data
    response_data = {
        'detail': 'Group toggled successfully.',
        'group': group_serializer.data,
    }

    return Response(response_data)

