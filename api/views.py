from django.contrib.auth.models import User  # import the User model
from rest_framework import generics
from .serializers import UserSerializer
from rest_framework.permissions import AllowAny
from django.http import FileResponse, Http404
from django.views.static import serve
import os
import logging

TILES_DIRECTORY = 'image_data/tiles/'

def tile_serving(request, path):
    tile_dir = os.path.join(os.path.dirname(__file__), '../image_data/tiles')
    tile_path = os.path.join(TILES_DIRECTORY, path)

    # Log the absolute paths
    logging.info(f'Tile directory: {os.path.abspath(tile_dir)}')
    logging.info(f'Requested tile: {os.path.abspath(tile_path)}')

    return serve(request, path, document_root=TILES_DIRECTORY)

def serve_image(request):
    try:
        # Get the absolute path of the image file
        img_path = os.path.join(os.path.dirname(__file__), '../image_data/compressed.webp')

        # Open the image file in binary mode
        img = open(img_path, 'rb')

        # Return the image as a response
        return FileResponse(img, content_type='image/webp')
    except FileNotFoundError:
        raise Http404

class CreateUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]
