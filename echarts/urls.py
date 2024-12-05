# echarts/urls.py
from django.urls import path
from ControlUsuarios.views import dashboard  # Importa desde ControlUsuarios.views
from . import views

urlpatterns = [
    path('', dashboard, name='index'),  # Usa la vista dashboard desde ControlUsuarios
    path('get_echart/', views.get_chart, name='get_echart'),
    path('obtener_rendimiento_general/', views.obtener_rendimiento_general, name='obtener_rendimiento_general'),
    path('echarts/get_admin_chart/', views.get_supervisor_chart, name='get_admin_chart'),
    # Nuevas rutas para los gráficos filtrados por planta
    path('get_admin_chart_barras/', views.get_admin_chart_barras, name='get_admin_chart_barras'),
    path('get_admin_chart_rendimiento/', views.get_admin_chart_rendimiento, name='get_admin_chart_rendimiento'),
    path('echarts/get_admin_chart_extra/', views.get_admin_chart_extra, name='get_admin_chart_extra'),
]
