"""
URL configuration for lms project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView  # Added for favicon fix

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Connects to your 'core' app where all our views live
    path('', include('core.urls')),

    # FIX: Redirect root favicon requests to your actual logo
    # This stops the "404 Not Found: /favicon.ico" error in your logs
    path('favicon.ico', RedirectView.as_view(url=settings.STATIC_URL + 'images/logo.png')),
]

# This is the CRITICAL part for images to work during development
if settings.DEBUG:
    # We must manually serve Media files (user uploads) in development
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
    # Note: We do NOT need to add static() for STATIC_URL here.
    # Django's runserver automatically finds your logo in the 'static' folder.