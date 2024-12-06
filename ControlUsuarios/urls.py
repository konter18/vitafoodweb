from django.urls import path
from .views import login_view,dashboard,UserCreateView,UserEditView,OperatorListView,eliminar_usuario,change_password,logout_view,plantas_dashboard,generar_reporte,generar_pdf
from django.contrib.auth import views as auth_views
urlpatterns = [
    path('logout/', logout_view, name='logout'),
    path('', login_view, name='login'),
    path('supervisor_dashboard/', dashboard, name='supervisor_dashboard'),
    path('crear-usuario/', UserCreateView.as_view(), name='crear_usuario'),
    path('editar-usuario/<int:pk>/', UserEditView.as_view(), name='editar_usuario'),
    path('eliminar_usuario/<int:pk>', eliminar_usuario, name='eliminar_usuario'),
    path('operator_list',OperatorListView.as_view(),name='operator_list'),
    path('admin_dashboard/', dashboard, name='admin_dashboard'),
    path('change-password/<int:user_id>/', change_password, name='change_password'),
    path('plantas_dashboard/', plantas_dashboard, name='plantas_dashboard'),
    path('informes_admin/', generar_reporte, name='informes_admin'),
    path('generar_pdf/', generar_pdf, name='generar_pdf'),
]
