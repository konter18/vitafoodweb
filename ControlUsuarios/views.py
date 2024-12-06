from django.shortcuts import render, redirect,get_object_or_404
from ControlUsuarios.models import CustomUser,PlantaModel,RegistroAciertos,PlantaModel
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
from django.http import JsonResponse,HttpResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import make_password,check_password
from .models import ErroresModel
import os
from io import BytesIO
from reportlab.pdfgen import canvas
import tempfile
from reportlab.lib.pagesizes import letter
from datetime import datetime


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

def plantas_dashboard(request):
    # Obtén las plantas de la base de datos
    plantas = PlantaModel.objects.all()  # Asegúrate de usar el modelo correcto
    planta_default = request.GET.get('planta') or (plantas.first().id_planta if plantas.exists() else None)

    context = {
        'plantas': plantas,
        'planta_default': planta_default,
    }
    return render(request, 'plantas_dashboard.html', context)

def logout_view(request):
    # Cierra la sesión del usuario
    logout(request)
    # Redirige al usuario a la página de inicio de sesión o a la página inicial
    return redirect('login')

def generar_reporte(request):
    planta_default = 1
    mes_default = "1"
    anio_default = 2024
    
    planta = request.GET.get('planta',planta_default)
    mes = request.GET.get('mes',mes_default)
    anio = request.GET.get('anio',anio_default)

    # Obtener las plantas y años disponibles
    plantas = PlantaModel.objects.all()
    anios = RegistroAciertos.objects.values_list('fecha__year', flat=True).distinct()

    # Validar que los parámetros están presentes
    if not planta or not mes or not anio:
        return render(request, 'informes_admin.html', {
            "error": "Los parámetros 'planta', 'mes' y 'anio' son requeridos.",
            "plantas": plantas,
            "anios": anios,
        })

    # Validar que la planta seleccionada existe
    if not PlantaModel.objects.filter(id_planta=planta).exists():
        return render(request, 'informes_admin.html', {
            "error": "La planta seleccionada no es válida.",
            "plantas": plantas,
            "anios": anios,
        })

    # Filtrar los registros según los parámetros
    registros = RegistroAciertos.objects.filter(
        fecha__month=mes,
        fecha__year=anio,
        planta_fk=planta
    )

    # Si no hay registros, mostrar un mensaje de error
    if not registros.exists():
        return render(request, 'informes_admin.html', {
            "error": "No hay datos disponibles para los parámetros seleccionados.",
            "plantas": plantas,
            "anios": anios,
        })

    # Calcular totales y porcentajes
    cantidad_total = sum([registro.cantidad_total for registro in registros])
    cantidad_perdida = sum([registro.cantidad_perdida for registro in registros])
    porcentaje_correcta = (cantidad_total - cantidad_perdida) / cantidad_total * 100 if cantidad_total > 0 else 0
    porcentaje_perdida = 100 - porcentaje_correcta

    # Pasar los datos al contexto
    context = {
        "cantidad_total": cantidad_total,
        "cantidad_perdida": cantidad_perdida,
        "porcentaje_correcta": porcentaje_correcta,
        "porcentaje_perdida": porcentaje_perdida,
        "plantas": plantas,
        "anios": anios,
        "planta_default": planta,
        "mes": mes,
        "anio": anio,
    }

    return render(request, 'informes_admin.html', context)

def generar_pdf(request):
    planta = request.GET.get('planta')
    mes = request.GET.get('mes')
    anio = request.GET.get('anio')

    # Verificar que los parámetros están presentes
    if not planta or not mes or not anio:
        return HttpResponse("Error: Los parámetros 'planta', 'mes' y 'anio' son necesarios.", status=400)

    # Verificar que la planta existe
    if not PlantaModel.objects.filter(id_planta=planta).exists():
        return HttpResponse("Error: Planta no válida.", status=400)

    # Filtrar registros
    registros = RegistroAciertos.objects.filter(
        fecha__month=mes,
        fecha__year=anio,
        planta_fk=planta
    )

    # Calcular los totales y porcentajes
    cantidad_total = sum([registro.cantidad_total for registro in registros])
    cantidad_perdida = sum([registro.cantidad_perdida for registro in registros])

    if cantidad_total == 0:
        porcentaje_correcta = 0
        porcentaje_perdida = 0
    else:
        porcentaje_correcta = (cantidad_total - cantidad_perdida) / cantidad_total * 100
        porcentaje_perdida = 100 - porcentaje_correcta

    # Generar el PDF
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.setFont("Helvetica", 12)
    c.drawString(100, 750, f"Informe de Rendimiento de Detección ({mes}/{anio})")
    c.drawString(100, 730, f"Planta: {planta}")
    c.drawString(100, 710, f"Cantidad Total: {cantidad_total}")
    c.drawString(100, 690, f"Cantidad Perdida: {cantidad_perdida}")
    c.drawString(100, 670, f"Porcentaje Correcto: {round(porcentaje_correcta, 2)}%")
    c.drawString(100, 650, f"Porcentaje Perdida: {round(porcentaje_perdida, 2)}%")
    c.save()

    buffer.seek(0)
    return HttpResponse(buffer, content_type='application/pdf')

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
        plantas = PlantaModel.objects.all()
        planta_default = plantas.first().id_planta if plantas else None

        return render(request, 'admin_dashboard.html', {
            'show_welcome': True,
            'plantas': plantas,
            'planta_default': planta_default
        })

    elif is_supervisor(request.user):
        return render(request, 'supervisor_dashboard.html', {'show_welcome': True})
    else:
        # En caso de un rol no permitido, redirigir al inicio o logout
        return redirect('logout')

