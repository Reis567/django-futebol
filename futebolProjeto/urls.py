from django.contrib import admin
from django.urls import path, include  # Importa a função include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('app1.urls')),  # Inclui as URLs do app1
]
