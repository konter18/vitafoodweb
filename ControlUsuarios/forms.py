from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm,PasswordChangeForm,AdminPasswordChangeForm
from django.contrib.auth.models import User
from .models import CustomUser,PlantaModel
from django.core.exceptions import ValidationError

class CustomAuthenticationForm(forms.Form):
    rut = forms.CharField(max_length=12, label="RUT", widget=forms.TextInput(attrs={'autofocus': 'autofocus'}))
    password = forms.CharField(widget=forms.PasswordInput)

    def clean_rut(self):
        rut = self.cleaned_data.get("rut")
        User = get_user_model()  # Usamos el modelo de usuario personalizado
        try:
            user = User.objects.get(rut=rut)
        except User.DoesNotExist:
            raise forms.ValidationError("El RUT no está registrado.")
        return rut  

    def get_user(self):
        rut = self.cleaned_data.get('rut')
        User = get_user_model()
        return User.objects.get(rut=rut)


class CustomUserSupervisorView(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['rut', 'first_name', 'last_name', 'planta_fk']

    rut = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    planta_fk = forms.ModelChoiceField(
        queryset=PlantaModel.objects.all(),
        empty_label="Seleccione una planta",
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True,
        label="Ubicación de Planta"
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False,
        label="Contraseña"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # Si el usuario ya existe (estamos editando), no mostramos el campo de contraseña
            self.fields['password'].required = False
        else:
            # Si es un nuevo usuario, el campo contraseña debe ser obligatorio
            self.fields['password'].required = True

    def save(self, commit=True):
        user = super().save(commit=False)
        if not self.instance.pk:
            # Solo asignamos el rol a nuevos usuarios
            user.role = 'operador'

        # Si la contraseña fue cambiada, la asignamos al objeto user
        if self.cleaned_data.get('password'):
            user.set_password(self.cleaned_data['password'])

        if commit:
            user.save()
        return user

class AdminPasswordChangeForm(forms.Form):
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label="Nueva contraseña"
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label="Confirmar nueva contraseña"
    )

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('new_password1')
        password2 = cleaned_data.get('new_password2')

        if password1 and password2 and password1 != password2:
            raise ValidationError("Las contraseñas no coinciden.")

        if len(password1) < 8:
            raise ValidationError("La contraseña debe tener al menos 8 caracteres.")

        if password1.isdigit():
            raise ValidationError("La contraseña no puede ser completamente numérica.")

        return cleaned_data