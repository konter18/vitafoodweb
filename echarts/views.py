from django.db.models import Count
from django.db.models.functions import TruncDate
from datetime import datetime
from django.http import JsonResponse
from ControlUsuarios.models import ErroresModel,RegistroAciertos

def get_chart(request):
    # Obtener los parámetros de la URL
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')

    # Verificación de que las fechas están presentes
    if not fecha_inicio or not fecha_fin:
        return JsonResponse({"error": "Las fechas 'fecha_inicio' y 'fecha_fin' son requeridas."}, status=400)

    try:
        # Convertir las fechas a objetos datetime
        fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d')
        fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d')
    except ValueError:
        return JsonResponse({"error": "Formato de fecha inválido. Use 'YYYY-MM-DD'."}, status=400)

    # Verificación adicional para mostrar las fechas recibidas
    print(f"Fecha de inicio recibida: {fecha_inicio}, Fecha de fin recibida: {fecha_fin}")

    # Consultar la base de datos con las fechas truncadas (sin hora)
    query = ErroresModel.objects.filter(fecha__range=[fecha_inicio, fecha_fin])

    # Truncar la fecha a solo día, sin hora, para que las comparaciones sean correctas
    query = query.annotate(fecha_truncada=TruncDate('fecha')) 

    # Verificación de la cantidad de registros
    print(f"Registros encontrados: {query.count()}")

    # Agrupar por tipo de error y contar cuántos registros hay de cada tipo
    data = (
        query.values('tipo_error')  # Agrupar por tipo de error
        .annotate(total=Count('id_error'))  # Contar los errores de cada tipo
        .order_by('tipo_error')  # Ordenar por tipo de error
    )

    # Preparar los datos para el gráfico
    chart = {
        "xAxis": [item['tipo_error'] for item in data],  # Tipos de error como etiquetas en el eje X
        "yAxis": [item['total'] for item in data],  # Totales como valores en el eje Y
    }

    # Verificación para mostrar los datos preparados
    print(f"Datos del gráfico: {chart}")

    return JsonResponse(chart)


def obtener_rendimiento_general(request):
    # Obtiene el mes actual
    mes_actual = datetime.now().month
    anio_actual = datetime.now().year

    # Filtra los registros por el mes y año actuales
    registros = RegistroAciertos.objects.filter(fecha__month=mes_actual, fecha__year=anio_actual)

    # Sumar las cantidades totales y perdidas
    cantidad_total = sum([registro.cantidad_total for registro in registros])
    cantidad_perdida = sum([registro.cantidad_perdida for registro in registros])

    # Calcular el porcentaje de detección correcta
    if cantidad_total > 0:
        porcentaje_correcta = (cantidad_total - cantidad_perdida) / cantidad_total * 100
    else:
        porcentaje_correcta = 0

    # Datos para el gráfico circular
    data = {
        "correcta": porcentaje_correcta,
        "perdida": 100 - porcentaje_correcta
    }

    return JsonResponse(data)