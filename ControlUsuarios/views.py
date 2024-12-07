from django.shortcuts import render, redirect,get_object_or_404
from ControlUsuarios.models import CustomUser,PlantaModel,RegistroAciertos,PlantaModel,ErroresModel
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
from reportlab.lib import colors
from datetime import datetime
from django.db.models import Count
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics import renderPDF
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import Image
from PIL import Image
from reportlab.lib.utils import ImageReader
from reportlab.lib.units import inch
from echarts.views import crear_grafico_barras, crear_grafico_pastel, crear_grafico_lineas,crear_grafico_barras_planta,crear_grafico_lineas_planta,crear_grafico_pastel_planta
from django.db.models.functions import TruncDay

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
    planta_id = request.GET.get('planta')
    mes = int(request.GET.get('mes'))  # Asegúrate de convertir 'mes' a entero
    anio = int(request.GET.get('anio'))  # Convertir a entero

    # Verificar que los parámetros están presentes
    if not planta_id or not mes or not anio:
        return HttpResponse("Error: Los parámetros 'planta', 'mes' y 'anio' son necesarios.", status=400)

    # Verificar que la planta existe y obtener el nombre
    try:
        planta = PlantaModel.objects.get(id_planta=planta_id)
    except PlantaModel.DoesNotExist:
        return HttpResponse("Error: Planta no válida.", status=400)

    # Obtener el nombre de la planta
    planta_nombre = planta.nombre_planta

    # Convertir el número del mes a su nombre correspondiente
    meses = [
        "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
    ]
    nombre_mes = meses[mes - 1]

    # Filtrar registros de aciertos
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

    # Filtrar errores por planta, mes y año
    registros_errores = ErroresModel.objects.filter(
        fecha__month=mes,
        fecha__year=anio,
        planta_fk=planta
    )

    # Contar los errores por tipo
    errores_por_tipo = registros_errores.values('tipo_error').annotate(cantidad_error=Count('id_error'))

    # Crear el contenido del informe
    informe_texto = (
        f"Informe de Rendimiento de Detección de {nombre_mes} del {anio}\n\n"
        f"Planta: {planta_nombre}\n\n"  
        f"Resumen del rendimiento de detección de la planta durante el mes de {nombre_mes} del año {anio}:\n\n"
        f"Durante el mes de {nombre_mes} de {anio}, la planta {planta_nombre} procesó un total de {cantidad_total} envases. "
        f"De este total, {cantidad_perdida} envases fueron identificados como errores. Esto nos proporciona un "
        f"porcentaje de acierto de {round(porcentaje_correcta, 2)}%, lo que refleja la eficiencia del sistema de "
        f"detección. Por otro lado, el porcentaje de error observado fue de {round(porcentaje_perdida, 2)}%, lo cual "
        f"indica el porcentaje de error del mes.\n\n"
        f"Este informe está basado en los registros de la planta durante el mes de {nombre_mes} y tiene como objetivo "
        f"proporcionar un análisis detallado de los errores detectados en el proceso de producción.\n\n"
        f"Errores Identificados:\n\n"
        f"En cuanto a los errores, se identificaron los siguientes tipos de incidencias durante el mes de {nombre_mes} del {anio}:\n\n"
    )

    for error in errores_por_tipo:
        informe_texto += f"- {error['tipo_error']}: {error['cantidad_error']} errores\n"

    # Generar el PDF
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.setFont("Helvetica", 12)

    # Márgenes de la página
    margin_left = 50
    margin_right = 50
    margin_top = 750
    line_height = 14

    y_position = margin_top
    for line in informe_texto.split('\n'):
        # Verificar el largo del texto para ajustarlo dentro de los márgenes
        max_line_width = letter[0] - margin_left - margin_right
        line_width = c.stringWidth(line, "Helvetica", 12)

        if line_width > max_line_width:
            # Dividir el texto largo en varias líneas
            words = line.split(' ')
            current_line = ""
            for word in words:
                test_line = f"{current_line} {word}".strip()
                test_line_width = c.stringWidth(test_line, "Helvetica", 12)
                if test_line_width <= max_line_width:
                    current_line = test_line
                else:
                    c.drawString(margin_left, y_position, current_line)
                    y_position -= line_height
                    current_line = word
            # Dibujar la última línea
            c.drawString(margin_left, y_position, current_line)
            y_position -= line_height
        else:
            c.drawString(margin_left, y_position, line)
            y_position -= line_height

        if y_position <= 100:
            c.showPage()  # Crear nueva página
            c.setFont("Helvetica", 12)
            y_position = margin_top  # Reiniciar la posición Y

    # Aquí añadimos espacio para el gráfico de barras en la primera página
    y_position -= 210  # Espacio extra para evitar que se solapen los gráficos con el texto

    # **Generar Gráfico de Barras**
    buffer_barras = crear_grafico_barras(errores_por_tipo)
    c.drawImage(ImageReader(buffer_barras), 50, y_position, width=500, height=230)


    # **Nueva página para gráficos 2 y 3 (pastel y evolución)**
    c.showPage()

    # Configurar un margen superior para la segunda página
    margen_superior_segunda_hoja = 710  # Ajusta el espacio en la parte superior

    # **Gráfico de Pastel**
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, margen_superior_segunda_hoja, "Gráfico de Proporción de Errores")
    buffer_pastel = crear_grafico_pastel(errores_por_tipo)
    y_position_pastel = margen_superior_segunda_hoja - 320  # Ajuste de la posición para el gráfico de pastel
    # Calcular la posición centrada para el gráfico de pastel
    x_position_pastel = (595 - 400) / 2  # Centrado en la página
    c.drawImage(ImageReader(buffer_pastel), x_position_pastel, y_position_pastel, width=400, height=300)

    # **Gráfico de Evolución**
    # Calcular la posición para el gráfico de evolución, dejando un margen adicional
    margen_extra = 20  # Espacio entre los gráficos
    y_position_lineas = y_position_pastel - 220 - margen_extra  # Posición debajo del gráfico de pastel

    # Asegurarse de que hay suficiente espacio en la página (por ejemplo, la posición no puede ser negativa)
    if y_position_lineas < 100:  # Si no hay suficiente espacio en la página, reiniciar el margen superior
        c.showPage()
        y_position_lineas = 600  # Reiniciar la posición en la nueva página

    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y_position_lineas + 230, "Gráfico de Evolución de Errores")  # Título del gráfico de evolución

    # Datos de evolución de errores
    datos_evolucion = registros_errores.annotate(trunc_fecha=TruncDay('fecha')).values('trunc_fecha').annotate(cantidad_error=Count('id_error')).order_by('trunc_fecha')
    buffer_lineas = crear_grafico_lineas(datos_evolucion)
    c.drawImage(ImageReader(buffer_lineas), 50, y_position_lineas, width=500, height=220)

    # Liberar recursos de los buffers
    buffer_pastel.close()
    buffer_lineas.close()

    # Guardar el PDF
    c.save()
    buffer.seek(0)

    # Devolver el PDF como respuesta
    return HttpResponse(buffer, content_type='application/pdf')

def generar_reporte_supervisor(request):
    # Obtener la planta asignada al supervisor
    planta_asignada = request.user.planta_fk  # Asegúrate de que `planta_fk` es el campo que enlaza la planta asignada.

    if not planta_asignada:
        return HttpResponse("Error: No tienes una planta asignada.", status=403)

    mes_default = "1"
    anio_default = 2024

    mes = request.GET.get('mes', mes_default)
    anio = request.GET.get('anio', anio_default)

    # Obtener los años disponibles
    anios = RegistroAciertos.objects.filter(planta_fk=planta_asignada).values_list('fecha__year', flat=True).distinct()

    # Validar los parámetros
    if not mes or not anio:
        return render(request, 'informes_supervisor.html', {
            "error": "Los parámetros 'mes' y 'anio' son requeridos.",
            "anios": anios,
        })

    # Filtrar los registros por planta asignada, mes y año
    registros = RegistroAciertos.objects.filter(
        fecha__month=mes,
        fecha__year=anio,
        planta_fk=planta_asignada
    )

    if not registros.exists():
        return render(request, 'informes_supervisor.html', {
            "error": "No hay datos disponibles para los parámetros seleccionados.",
            "anios": anios,
        })

    # Calcular totales y porcentajes
    cantidad_total = sum([registro.cantidad_total for registro in registros])
    cantidad_perdida = sum([registro.cantidad_perdida for registro in registros])
    porcentaje_correcta = (cantidad_total - cantidad_perdida) / cantidad_total * 100 if cantidad_total > 0 else 0
    porcentaje_perdida = 100 - porcentaje_correcta

    context = {
        "cantidad_total": cantidad_total,
        "cantidad_perdida": cantidad_perdida,
        "porcentaje_correcta": porcentaje_correcta,
        "porcentaje_perdida": porcentaje_perdida,
        "anio": anio,
        "mes": mes,
        "planta_asignada": planta_asignada.nombre_planta,
        "anios": anios,
    }

    return render(request, 'informes_supervisor.html', context)

def generar_pdf_supervisor(request):
    # Obtener la planta asignada al usuario logueado
    planta_asignada = request.user.planta_fk

    if not planta_asignada:
        return HttpResponse("Error: No tienes una planta asignada.", status=403)

    mes = int(request.GET.get('mes'))  # Asegúrate de convertir 'mes' a entero
    anio = int(request.GET.get('anio'))  # Convertir a entero

    # Verificar que los parámetros 'mes' y 'anio' están presentes
    if not mes or not anio:
        return HttpResponse("Error: Los parámetros 'mes' y 'anio' son necesarios.", status=400)

    # Obtener el nombre de la planta asignada
    planta_nombre = planta_asignada.nombre_planta

    # Convertir el número del mes a su nombre correspondiente
    meses = [
        "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
    ]
    nombre_mes = meses[mes - 1]

    # Filtrar registros de aciertos para la planta asignada
    registros = RegistroAciertos.objects.filter(
        fecha__month=mes,
        fecha__year=anio,
        planta_fk=planta_asignada
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

    # Filtrar errores por planta, mes y año
    registros_errores = ErroresModel.objects.filter(
        fecha__month=mes,
        fecha__year=anio,
        planta_fk=planta_asignada
    )

    # Contar los errores por tipo
    errores_por_tipo = registros_errores.values('tipo_error').annotate(cantidad_error=Count('id_error'))

    # Crear el contenido del informe
    informe_texto = (
        f"Informe de Rendimiento de Detección de {nombre_mes} del {anio}\n\n"
        f"Planta: {planta_nombre}\n\n"  
        f"Resumen del rendimiento de detección de la planta durante el mes de {nombre_mes} del año {anio}:\n\n"
        f"Durante el mes de {nombre_mes} de {anio}, la planta {planta_nombre} procesó un total de {cantidad_total} envases. "
        f"De este total, {cantidad_perdida} envases fueron identificados como errores. Esto nos proporciona un "
        f"porcentaje de acierto de {round(porcentaje_correcta, 2)}%, lo que refleja la eficiencia del sistema de "
        f"detección. Por otro lado, el porcentaje de error observado fue de {round(porcentaje_perdida, 2)}%, lo cual "
        f"indica el porcentaje de error del mes.\n\n"
        f"Este informe está basado en los registros de la planta durante el mes de {nombre_mes} y tiene como objetivo "
        f"proporcionar un análisis detallado de los errores detectados en el proceso de producción.\n\n"
        f"Errores Identificados:\n\n"
        f"En cuanto a los errores, se identificaron los siguientes tipos de incidencias durante el mes de {nombre_mes} del {anio}:\n\n"
    )

    for error in errores_por_tipo:
        informe_texto += f"- {error['tipo_error']}: {error['cantidad_error']} errores\n"

    # Generar el PDF
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.setFont("Helvetica", 12)

    # Márgenes de la página
    margin_left = 50
    margin_right = 50
    margin_top = 750
    line_height = 14

    y_position = margin_top
    for line in informe_texto.split('\n'):
        # Verificar el largo del texto para ajustarlo dentro de los márgenes
        max_line_width = letter[0] - margin_left - margin_right
        line_width = c.stringWidth(line, "Helvetica", 12)

        if line_width > max_line_width:
            # Dividir el texto largo en varias líneas
            words = line.split(' ')
            current_line = ""
            for word in words:
                test_line = f"{current_line} {word}".strip()
                test_line_width = c.stringWidth(test_line, "Helvetica", 12)
                if test_line_width <= max_line_width:
                    current_line = test_line
                else:
                    c.drawString(margin_left, y_position, current_line)
                    y_position -= line_height
                    current_line = word
            # Dibujar la última línea
            c.drawString(margin_left, y_position, current_line)
            y_position -= line_height
        else:
            c.drawString(margin_left, y_position, line)
            y_position -= line_height

        if y_position <= 100:
            c.showPage()  # Crear nueva página
            c.setFont("Helvetica", 12)
            y_position = margin_top  # Reiniciar la posición Y

    # Aquí añadimos espacio para el gráfico de barras en la primera página
    y_position -= 210  # Espacio extra para evitar que se solapen los gráficos con el texto

    # Filtrar errores por planta del usuario
    errores_por_tipo_planta = registros_errores.filter(planta_fk=planta_asignada).values('tipo_error').annotate(cantidad_error=Count('id_error'))
    # **Generar Gráfico de Barras**
    buffer_barras_planta = crear_grafico_barras_planta(errores_por_tipo_planta)
    c.drawImage(ImageReader(buffer_barras_planta), 50, y_position, width=500, height=230)

    # **Nueva página para gráficos 2 y 3 (pastel y evolución)**
    c.showPage()

    # Configurar un margen superior para la segunda página
    margen_superior_segunda_hoja = 710  # Ajusta el espacio en la parte superior

    # **Gráfico de Pastel**
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, margen_superior_segunda_hoja, "Gráfico de Proporción de Errores")
    buffer_pastel_planta = crear_grafico_pastel_planta(errores_por_tipo_planta)
    y_position_pastel = margen_superior_segunda_hoja - 320  # Ajuste de la posición para el gráfico de pastel
    # Calcular la posición centrada para el gráfico de pastel
    x_position_pastel = (595 - 400) / 2  # Centrado en la página
    c.drawImage(ImageReader(buffer_pastel_planta), x_position_pastel, y_position_pastel, width=400, height=300)

    # **Gráfico de Evolución**
    # Calcular la posición para el gráfico de evolución, dejando un margen adicional
    margen_extra = 20  # Espacio entre los gráficos
    y_position_lineas = y_position_pastel - 220 - margen_extra  # Posición debajo del gráfico de pastel

    # Asegurarse de que hay suficiente espacio en la página (por ejemplo, la posición no puede ser negativa)
    if y_position_lineas < 100:  # Si no hay suficiente espacio en la página, reiniciar el margen superior
        c.showPage()
        y_position_lineas = 600  # Reiniciar la posición en la nueva página

    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y_position_lineas + 230, "Gráfico de Evolución de Errores")  # Título del gráfico de evolución

    # Gráfico de Evolución Filtrado por Planta
    datos_evolucion_planta = registros_errores.filter(planta_fk=planta_asignada).annotate(trunc_fecha=TruncDay('fecha')).values('trunc_fecha').annotate(cantidad_error=Count('id_error')).order_by('trunc_fecha')
    buffer_lineas_planta = crear_grafico_lineas_planta(datos_evolucion_planta)
    c.drawImage(ImageReader(buffer_lineas_planta), 50, y_position_lineas, width=500, height=220)

    # Liberar recursos de los buffers
    buffer_barras_planta.close()
    buffer_pastel_planta.close()
    buffer_lineas_planta.close()

    # Guardar el PDF
    c.save()
    buffer.seek(0)

    # Devolver el PDF como respuesta
    return HttpResponse(buffer, content_type='application/pdf')


def agregar_imagen_al_pdf(c, buffer, x, y, width, height):
    img = Image.open(buffer)
    img = img.resize((width, height), Image.ANTIALIAS)
    img_buffer = BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)

    c.drawImage(ImageReader(img_buffer), x, y, width, height)


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
        # Obtener la planta asignada al supervisor
        planta_asignada = request.user.planta_fk  # Ajustar según el nombre exacto del campo en el modelo de usuario

        if planta_asignada:
            # Pasar la planta asignada al contexto
            return render(request, 'supervisor_dashboard.html', {
                'show_welcome': True,
                'planta_asignada': planta_asignada
            })
        else:
            # Si no tiene planta asignada, redirigir a una página de error o mostrar mensaje
            return render(request, 'supervisor_dashboard.html', {
                'show_welcome': True,
                'error': "No tienes una planta asignada."
            })

    else:
        # En caso de un rol no permitido, redirigir al inicio o logout
        return redirect('logout')
