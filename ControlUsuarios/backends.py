from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model

class RutAuthenticationBackend(BaseBackend):
    def authenticate(self, request, rut=None, password=None):
        print("Intentando autenticar con RUT:", rut)  # Mensaje de depuración
        UserModel = get_user_model()
        try:
            user = UserModel.objects.get(rut=rut)  # Asegúrate de que 'rut' es el campo correcto
            if user.check_password(password):
                print("Autenticación exitosa para el usuario:", user)  # Mensaje de éxito
                return user
            else:
                print("Contraseña incorrecta para el usuario:", user)
        except UserModel.DoesNotExist:
            print("Usuario no encontrado para el RUT:", rut)
            return None

    def get_user(self, user_id):
        UserModel = get_user_model()
        try:
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None
