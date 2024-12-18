from django.urls import path
from . import views

urlpatterns = [
    # connecting serve image function
    path("image/", views.serve_image, name="serve-image"),
]
