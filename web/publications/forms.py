from django import forms
from .models import Post, Musica,Comentario
from users.models import Usuarios

class MusicaForm(forms.ModelForm):
    class Meta:
        model = Musica
        fields = ['nombre', 'archivo_musica']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de la canción'}),
            'archivo_musica': forms.FileInput(attrs={'class': 'form-control'}),
        }

class PostForm(forms.ModelForm):
    usuarios_etiquetados = forms.ModelMultipleChoiceField(
        queryset=Usuarios.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Etiquetar usuarios"
    )

    musica = forms.ModelChoiceField(
        queryset=Musica.objects.all(),
        required=False,
        label="Agregar música",
        empty_label="-- Sin música --",
        # CAMBIO AQUÍ: Quitamos el 'id': 'select-musica' para que use el default 'id_musica'
        widget=forms.Select(attrs={'class': 'form-control'}) 
    )

    class Meta:
        model = Post
        # Agregamos musica_inicio y musica_fin
        fields = ['descripcion', 'imagen', 'tipo', 'usuarios_etiquetados', 'musica', 'musica_inicio', 'musica_fin']
        
        widgets = {
            'descripcion': forms.Textarea(attrs={'placeholder': '¿Qué estás pensando?', 'rows': 3, 'class': 'form-control border-0 fs-5'}),
            'tipo': forms.Select(choices=[('publico', 'Público'), ('privado', 'Privado')]),
            
            # Usamos HiddenInput porque normalmente esto lo controla un slider con JavaScript
            # Si quieres que se vean los números para probar, cambia HiddenInput por NumberInput
            'musica_inicio': forms.HiddenInput(attrs={'id': 'musica-inicio'}),
            'musica_fin': forms.HiddenInput(attrs={'id': 'musica-fin'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['descripcion'].required = False

    def clean(self):
        cleaned_data = super().clean()
        descripcion = cleaned_data.get('descripcion')
        imagen = cleaned_data.get('imagen')

        if not descripcion and not imagen:
            raise forms.ValidationError('Debes agregar una descripción o subir una imagen/video.')
        return cleaned_data



class ComentarioForm(forms.ModelForm):
    """
    Formulario simple para agregar comentarios a un Post.
    Contiene únicamente el campo de descripción.
    """
    class Meta:
        model = Comentario
        # Los campos 'usuario' y 'post' se asignan en la vista (o Consumer).
        # El campo 'comentario_padre' para anidamiento se asigna en la vista si es una respuesta.
        fields = ['descripcion', 'imagen'] 
        
        widgets = {
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control', 
                'placeholder': 'Escribe un comentario...', 
                'rows': 2,
                'required': False 
            }),
            'imagen': forms.FileInput(attrs={'class': 'd-none', 'id': 'comment-image-input'}),
        }