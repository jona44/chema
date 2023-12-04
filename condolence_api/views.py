from rest_framework import serializers
from condolence.models import Contribution, Deceased
from chema.models import Group
from user.models import Profile
from rest_framework import serializers, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import ContributionSerializer
from condolence.forms import DeceasedForm
from .serializers import DeceasedSerializer
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages



@api_view(['GET', 'POST'])
def create_contribution_api(request):
    if request.method == 'POST':
        serializer = ContributionSerializer(data=request.data)
        if serializer.is_valid():
            # Perform the admin check and other logic here
            serializer.save(group_admin=request.user.profile)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    else:
        # Handle GET request logic, if necessary
        contributions = Contribution.objects.all()
        serializer = ContributionSerializer(contributions, many=True)
        return Response(serializer.data)

# Make sure to update the URL configuration to point to this view

@api_view(['GET'])
def contribution_detail_api(request, contribution_id):
    # Retrieve the specific contribution instance
    contribution = get_object_or_404(Contribution, id=contribution_id)
    # Serialize the contribution instance
    serializer = ContributionSerializer(contribution)
    # Return the serialized data in the response
    return Response(serializer.data)




@api_view(['GET', 'POST'])
def deceased_api(request):
    active_group = Group.objects.filter(is_active=True).first()
    group_admin = Profile.objects.filter(groupmembership__is_admin=True, groups=active_group)
    
    if request.method == 'POST':
        serializer = DeceasedSerializer(data=request.data)
        if serializer.is_valid():
            deceased = serializer.save(group=active_group, group_admin=request.user.profile)
            messages.success(request, "Group member has been marked as Deceased!")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    else:
        # Handle GET request logic, if necessary
        deceased_members = Deceased.objects.filter(group=active_group)
        serializer = DeceasedSerializer(deceased_members, many=True)
        return Response(serializer.data)


@api_view(['POST'])
def toggle_deceased_api(request, deceased_id):
    # Get the deceased being toggled
    deceased_to_toggle = get_object_or_404(Deceased, id=deceased_id)
    
    # Toggle the deceased by setting it to True
    deceased_to_toggle.contributions_open = True
    deceased_to_toggle.save()

    # Deactivate all other deceased
    Deceased.objects.exclude(id=deceased_id).update(contributions_open=False)

    # Return a success status response
    return Response({'status': 'success', 'message': 'Deceased status toggled successfully'}, status=status.HTTP_200_OK)



@api_view(['POST'])
def stop_contributions_api(request, deceased_id):
    # Get the Deceased instance
    deceased = get_object_or_404(Deceased, pk=deceased_id)

    # Call the method to stop contributions
    deceased.stop_contributions()

    # Return a JSON response indicating success
    return Response({'status': 'success', 'message': 'Contributions for this deceased member have been closed'}, status=status.HTTP_200_OK)
