from django.contrib import admin
from django.urls import path, include
from ControlUsuarios import views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('',include("ControlUsuarios.urls"))
]
