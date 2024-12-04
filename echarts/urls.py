# echarts/urls.py
from django.urls import path
from ControlUsuarios.views import dashboard  # Importa desde ControlUsuarios.views
from . import views

urlpatterns = [
    path('', dashboard, name='index'),  # Usa la vista dashboard desde ControlUsuarios
    path('get_echart/', views.get_chart, name='get_echart'),
    path('get_rendimiento_general/', views.obtener_rendimiento_general, name='get_rendimiento_general'),
]
