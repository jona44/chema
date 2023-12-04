from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .serializers import ProfileSerializer

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile_api(request):
    profile = request.user.profile
    serializer = ProfileSerializer(profile)
    return Response(serializer.data)
