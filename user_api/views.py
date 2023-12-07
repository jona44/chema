from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .serializers import ProfileSerializer,UserRegistrationSerializer
from rest_framework import status

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile_api(request):
    profile = request.user.profile
    serializer = ProfileSerializer(profile)
    return Response(serializer.data)



@api_view(['POST'])
def user_register(request):
    if request.method == 'POST':
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # You can add additional logic here if needed
            return Response({'message': f'Account has been created for {user.username}!'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

