from django import forms
from users.models import Usuarios, TipoUser
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ObjectDoesNotExist

class UserRegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput())
    confirm_password = forms.CharField(widget=forms.PasswordInput(), label="Confirmar Contraseña")

    class Meta:
        model = Usuarios
        fields = {'first_name', 'last_name', 'fech_nacimiento', 'sexo', 'email','password','username'}

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Las contraseñas no coinciden")

        return cleaned_data

    def save(self, commit=True):
        usuarios = super().save(commit=False)  
        try:
            tipo_cliente = TipoUser.objects.get(tipo_usuario="Cliente")
            usuarios.tipo_user = tipo_cliente  
            usuarios.password = make_password(usuarios.password)
        except ObjectDoesNotExist:
            usuarios.tipo_user = None  

        if commit:
            usuarios.save()
        return usuarios


class LoginForm(forms.Form):
    username = forms.CharField(max_length=150, label="Usuario")
    password = forms.CharField(widget=forms.PasswordInput(), label="Contraseña")

