from django.shortcuts import render, redirect,get_object_or_404
from ControlUsuarios.models import CustomUser
from django.contrib.auth import login, authenticate, logout,get_user_model
from .forms import CustomAuthenticationForm, CustomUserSupervisorView
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.views import View
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.paginator import Paginator
import re
from django.urls import reverse_lazy
from django import forms
from django.contrib.auth.forms import AdminPasswordChangeForm
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import make_password,check_password

def change_password(request, user_id):
    if request.method == 'POST':
        new_password1 = request.POST.get('new_password1')
        new_password2 = request.POST.get('new_password2')
        
        # Verificar que las contraseñas coincidan
        if new_password1 == new_password2:
            try:
                user = CustomUser.objects.get(id=user_id)
                user.password = make_password(new_password1)  # Cifrar la nueva contraseña
                user.save()

                # Responder con éxito y enviar la URL correcta
                return JsonResponse({
                    'success': True,
                    'message': 'Contraseña cambiada exitosamente',
                    'redirect_url': '/operator_list'  # Asegúrate de que esta URL sea la correcta
                })
            except CustomUser.DoesNotExist:
                return JsonResponse({'success': False, 'errors': 'Usuario no encontrado'})
        else:
            return JsonResponse({'success': False, 'errors': 'Las contraseñas no coinciden'})

    return JsonResponse({'success': False, 'errors': 'Método no permitido'})
# Función de prueba para verificar si el usuario es un supervisor
def is_supervisor(user):
    print(f"Verificando si {user.username} es supervisor...")
    return hasattr(user, 'role') and user.role == 'supervisor'

# Función de prueba para verificar si el usuario es un admin
def is_admin(user):
    return hasattr(user, 'role') and user.role == 'administrador'

def login_view(request):
    # Si el usuario ya está autenticado, lo redirigimos
    if request.user.is_authenticated:
        if request.user.role == 'supervisor':
            return redirect('supervisor_dashboard')
        elif request.user.role == 'administrador':
            return redirect('admin_dashboard')
        else:
            return redirect('logout')  # la vista por defecto si el rol no está definido

    if request.method == 'POST':
        rut = request.POST.get('rut')
        password = request.POST.get('password')

        # Intentamos autenticar al usuario
        user = authenticate(request, rut=rut, password=password)

        if user is not None:
            login(request, user)

            # Verificar el rol del usuario para redirigirlo
            if user.role == 'supervisor':
                return redirect('supervisor_dashboard')  # Redirige al dashboard del supervisor
            elif user.role == 'administrador':
                return redirect('admin_dashboard')  # Redirige al dashboard del operador
            else:
                messages.error(request, 'Rol no permitido.')  # Mensaje de error si el rol no está definido
                return redirect('logout')
        else:
            messages.error(request, 'RUT o contraseña incorrectos.')

    return render(request, 'index.html')


def redirect_to_dashboard(request):
    """
    Redirige al usuario a la vista correspondiente según su rol.
    """
    user = request.user
    if user.role == "supervisor":
        return redirect('supervisor_dashboard')
    elif user.role == "administrador":
        return redirect('admin_dashboard')
    else:
        logout(request)  # Cierra la sesión si el rol no es válido
        messages.error(request, 'No tienes un rol válido asignado.')
        return redirect('login')

# Vista para crear usuarios solo accesible para supervisores
class UserCreateView(View):
    def get(self, request):
        # Verificar si el usuario es supervisor antes de mostrar el formulario
        if not is_supervisor(request.user):
            messages.error(request, "No tienes permisos para acceder a esta página.")
            return redirect('supervisor_dashboard')  # Redirigir a la página del supervisor

        form = CustomUserSupervisorView()
        return render(request, 'user_create_supervisor.html', {'form': form})

    def post(self, request):
        print(request.POST)  # Imprime los datos recibidos
        if not is_supervisor(request.user):
            messages.error(request, "No tienes permisos para realizar esta acción.")
            return redirect('supervisor_dashboard')  # Redirigir a la página del supervisor
        print(f"Planta FK: {request.POST.get('planta_fk')}")
        # Obtener el RUT del formulario
        rut = request.POST.get('rut')
        
        # Expresión regular para validar el formato del RUT
        rut_pattern = r'^\d{1,2}\.\d{3}\.\d{3}[-]([0-9Kk])$'
        
        # Validar el RUT
        if not re.match(rut_pattern, rut):
            messages.error(request, "El formato del RUT es inválido. Asegúrate de seguir el formato de ejemplo: XX.XXX.XXX-X (20.300.333-k).")
            form = CustomUserSupervisorView(request.POST)
            return render(request, 'user_create_supervisor.html', {'form': form})  # Volver al formulario

        # Verificar si el RUT ya existe en la base de datos
        if CustomUser.objects.filter(rut=rut).exists():
            messages.error(request, "Este RUT ya está registrado. Por favor ingresa otro.")
            form = CustomUserSupervisorView(request.POST)
            return render(request, 'user_create_supervisor.html', {'form': form})  # Volver al formulario

        # Si el formato es válido y el RUT no existe, guardar el usuario
        form = CustomUserSupervisorView(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Usuario creado con éxito.')
            return redirect('supervisor_dashboard')
        else:
            print(form.errors)  # Esto te ayudará a ver los errores en consola
            return render(request, 'user_create_supervisor.html', {'form': form})


        # Si el formulario no es válido, mostrarlo nuevamente con los errores
        return render(request, 'user_create_supervisor.html', {'form': form})

class UserEditView(UserPassesTestMixin, View):
    # Función de prueba para verificar que solo los supervisores pueden acceder
    def test_func(self):
        return self.request.user.role == 'supervisor'

    def get(self, request, pk):
        user = get_object_or_404(CustomUser, pk=pk)  # Obtén al usuario por su ID
        
        # Verificar si el supervisor está intentando editar a otro supervisor
        if user.role == 'supervisor':
            messages.error(request, "No tienes permisos para editar a otro supervisor.")
            return redirect('supervisor_dashboard')  # Redirige al dashboard del supervisor

        form = CustomUserSupervisorView(instance=user)  # Carga el formulario con los datos del usuario
        return render(request, 'user_edit_supervisor.html', {'form': form, 'user': user})

    def post(self, request, pk):
        user = get_object_or_404(CustomUser, pk=pk)  # Obtén al usuario por su ID
        
        # Verificar si el supervisor está intentando editar a otro supervisor
        if user.role == 'supervisor':
            messages.error(request, "No tienes permisos para editar a otro supervisor.")
            return redirect('operator_list')  # Redirige al dashboard del supervisor

        form = CustomUserSupervisorView(request.POST, instance=user)  # Asocia el formulario con el usuario a editar
        if form.is_valid():
            # Asegurarse de que el rol no cambie accidentalmente
            if user.role == 'supervisor' and form.cleaned_data['role'] != 'supervisor':
                messages.error(request, "No puedes cambiar el rol de un supervisor.")
                return redirect('operator_list')  # Redirige al dashboard del supervisor
            
            form.save()  # Guarda los cambios realizados
            messages.success(request, 'Usuario actualizado con éxito.')
            return redirect('operator_list')  # Redirige al dashboard del supervisor

        return render(request, 'user_edit_supervisor.html', {'form': form, 'user': user})

class OperatorListView(UserPassesTestMixin, View):
    # Solo accesible para supervisores
    def test_func(self):
        return self.request.user.role == 'supervisor'

    def get(self, request):
        # Obtener todos los operadores
        operadores = CustomUser.objects.filter(role='operador')

        # Filtrado (si se ha enviado un parámetro de búsqueda)
        rut_filter = request.GET.get('rut', '')
        if rut_filter:
            operadores = operadores.filter(rut__icontains=rut_filter)
        
        # Paginación (10 operadores por página)
        paginator = Paginator(operadores, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        # Pasar la lista de operadores y la página actual a la plantilla
        return render(request, 'operator_list.html', {
            'page_obj': page_obj,
            'rut_filter': rut_filter,  # Para mantener el filtro de búsqueda
        })


def logout_view(request):
    # Cierra la sesión del usuario
    logout(request)
    # Redirige al usuario a la página de inicio de sesión o a la página inicial
    return redirect('login')

@login_required
def eliminar_usuario(request, pk):
    # Verificar si el usuario es un supervisor
    if request.user.role != 'supervisor':
        messages.error(request, "No tienes permisos para realizar esta acción.")
        return redirect('supervisor_dashboard')

    # Obtener al usuario a eliminar
    usuario = get_object_or_404(CustomUser, pk=pk)

    # Eliminar el usuario
    usuario.delete()
    messages.success(request, "Operador eliminado con éxito.")
    return redirect('operator_list')

@login_required
@user_passes_test(lambda u: is_supervisor(u) or is_admin(u))
def dashboard(request):
    # Verificar a qué tipo de dashboard redirigir
    if is_admin(request.user):
        return render(request, 'admin_dashboard.html', {'show_welcome': True})
    elif is_supervisor(request.user):
        return render(request, 'supervisor_dashboard.html', {'show_welcome': True})
    else:
        # En caso de un rol no permitido, redirigir al inicio o logout
        return redirect('logout')