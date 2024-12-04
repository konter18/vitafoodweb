from django.contrib import admin
from .models import ErroresModel, CustomUser,PlantaModel

# Clase de administración para el modelo de errores
class ErroresAdmin(admin.ModelAdmin):
    fields = ["fecha", "tipo_error", "rut_fk", "link_error"]
    list_display = ["tipo_error", "fecha","link_error"]

# Clase de administración para el modelo de usuarios personalizados
class CustomUserAdmin(admin.ModelAdmin):
    model = CustomUser
    list_display = ('rut', 'first_name', 'last_name', 'role', 'planta_fk', 'is_active')
    search_fields = ('rut', 'first_name', 'last_name')

    def save_model(self, request, obj, form, change):
        # Si la contraseña ha sido cambiada, encriptarla
        if form.cleaned_data.get('password'):
            obj.set_password(form.cleaned_data['password'])
        obj.save()

class PlantaAdmin(admin.ModelAdmin):
    fields = ["nombre_planta"]
    list_display = ["id_planta", "nombre_planta"]


# Registra CustomUser con su clase de configuración personalizada
admin.site.register(CustomUser, CustomUserAdmin)

# Registra ErroresModel con su clase de configuración personalizada
admin.site.register(ErroresModel, ErroresAdmin)

# Registra PlantaModel con su clase de configuración personalizada
admin.site.register(PlantaModel, PlantaAdmin)