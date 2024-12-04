from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.conf import settings


class CustomUserManager(BaseUserManager):
    def create_user(self, rut, password=None, **extra_fields):
        """
        Crea y devuelve un usuario con un RUT y una contraseña.
        """
        if not rut:
            raise ValueError('El RUT debe ser establecido')

        user = self.model(rut=rut, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, rut, password=None, **extra_fields):
        """
        Crea y devuelve un superusuario con un RUT.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(rut=rut, password=password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):  # Heredando de PermissionsMixin
    # Campos básicos
    rut = models.CharField(max_length=12, unique=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    is_superuser = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    # Campo para el rol de usuario
    ROLE_CHOICES = [
        ('supervisor', 'Supervisor'),
        ('operador', 'Operador'),
        ('administrador','Administrador'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='operador')
    
    # Relación con PlantaModel
    planta_fk = models.ForeignKey(
        'ControlUsuarios.PlantaModel',  # Referencia usando el formato 'app_label.ModelName'
        on_delete=models.CASCADE,  # Define qué pasa si la planta se elimina
        null=False,  # Permite valores nulos
        blank=True,  # Permite que el campo sea opcional en formularios
        db_column="planta_fk",
        verbose_name="Planta Asociada",
    )
    
    objects = CustomUserManager()

    USERNAME_FIELD = 'rut'
    REQUIRED_FIELDS = []

    @property
    def username(self):
        return self.rut  # Devuelve el RUT como si fuera el username

    def __str__(self):
        return f'{self.first_name} {self.last_name}'


class PlantaModel(models.Model):
    id_planta = models.AutoField(primary_key=True)
    nombre_planta = models.CharField(max_length=100, verbose_name="Nombre de la Planta", null=True, blank=False)

    class Meta:
        db_table = "planta"
        verbose_name = "Planta"
        verbose_name_plural = "Plantas"

    def __str__(self):
        return self.nombre_planta


class ErroresModel(models.Model):
    id_error = models.AutoField(primary_key=True)
    fecha = models.DateField(verbose_name="Fecha del error", null=False, blank=True)
    tipo_error = models.CharField(verbose_name="Tipo de error", null=False, blank=True, max_length=40)
    rut_fk = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, db_column='rut_fk')
    link_error = models.CharField(verbose_name="Link del error", null=False, blank=True, max_length=255)
    planta_fk = models.ForeignKey('ControlUsuarios.PlantaModel', on_delete=models.CASCADE, db_column='planta_fk')
    
    class Meta:
        db_table = "errores"
        verbose_name = "Error"
        verbose_name_plural = "Errores"
        
    def __str__(self):
        return self.tipo_error

class ConfigEnvasesModel(models.Model):
    id_cfg = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=30, verbose_name="Nombre del envase", null=False, blank=False)
    valor_mask = models.IntegerField(verbose_name="Mask", null=False, blank=False)
    dilatation = models.IntegerField(verbose_name="Dilatation", null=False, blank=False)
    x_offset = models.DecimalField(verbose_name="x_offset", max_digits=5, decimal_places=2, null=False, blank=False)
    y_offset = models.DecimalField(verbose_name="y_offset", max_digits=5, decimal_places=2, null=False, blank=False)
    width_ratio = models.DecimalField(verbose_name="Width ratio", max_digits=5, decimal_places=2, null=False, blank=False)
    height_ratio = models.DecimalField(verbose_name="Height ratio", max_digits=5, decimal_places=2, null=False, blank=False)
    date_format = models.CharField(verbose_name="Formato de Fecha", max_length=30, null=False, blank=False)

    class Meta:
        db_table = "configenvases"
        verbose_name = "ConfigEnvase"
        verbose_name_plural = "ConfigEnvases"
        
    def __str__(self):
        return self.nombre

    
class RegistroAciertos(models.Model):
    id_registroacierto = models.AutoField(primary_key=True)
    cantidad_total = models.IntegerField(verbose_name="Cantidad total", null=False, blank=False)
    cantidad_perdida = models.IntegerField(verbose_name="Cantidad perdida", null=False, blank=False)
    fecha = models.DateField(verbose_name="Fecha de registro", null=False, blank=False, auto_now_add=True)
    planta_fk = models.ForeignKey('ControlUsuarios.PlantaModel', on_delete=models.CASCADE, db_column='planta_fk', related_name='registros_aciertos')

    class Meta:
        db_table = "registroaciertos"
        verbose_name = "Registro de Aciertos"
        verbose_name_plural = "Registros de Aciertos"
        
    def __str__(self):
        return str(self.id_registroacierto)
