

from django import forms
from users.models import Usuarios
from .models import Perfil
class EditFrom(forms.ModelForm):
    class Meta:
        model=Usuarios
        fields={
            'first_name','last_name','username','sexo','foto_perfil'
        }

class EditPerfil(forms.ModelForm):
    class Meta:
        model=Perfil
        fields={
            'bio','foto_portada'
        }
      