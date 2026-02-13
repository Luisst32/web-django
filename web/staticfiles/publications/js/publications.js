$(document).ready(function() {
    $('.reacciones button').click(function() {
      var button = $(this);
      
      // Extraemos los datos del atributo onclick
      // Asegúrate de que tu HTML sea: onclick="darReaccion(this, '1', 99)"
      var tipo = button.attr('onclick').match(/'([0-9])'/)[1]; 
      var postId = button.attr('onclick').match(/,\s*(\d+)\)/)[1];
  
      $.ajax({
        url: `/publicaciones/${postId}/reaccion/${tipo}/`,
        type: 'POST',
        headers: { 'X-CSRFToken': getCSRFToken() },
        success: function(data) {
          if (data.success) {
            var reaccionesDiv = button.closest('.reacciones');
            
            // 1. Actualizar los contadores de texto
            reaccionesDiv.find('.love-count').text(data.love_count);
            reaccionesDiv.find('.fun-count').text(data.fun_count);
            
            // 2. Limpiar las clases de color anteriores de TODOS los botones de esa publicación
            reaccionesDiv.find('button').removeClass('active-love active-fun');
            
            // 3. Si la reacción se activó (el backend no la quitó), pintamos el botón
            // Verificamos si data.user_reaction viene del backend, si no, asumimos que se activó
            var reactionType = data.user_reaction ? data.user_reaction : tipo;

            // Si el backend dice que hay reacción (o asumimos que sí), añadimos la clase correcta
            // Nota: Si tu backend hace "toggle" (quita la reacción al dar click de nuevo), 
            // data.user_reaction debería venir vacío o null, y no entraríamos aquí.
            
            if (reactionType == '1') {
                button.addClass('active-love'); // Clase para el Corazón Rojo
            } else if (reactionType == '2') {
                button.addClass('active-fun');  // Clase para la Cara Amarilla
            }
            
          } else {
            console.error('Error en la reacción:', data.message);
          }
        },
        error: function(error) {
          console.error('Error de conexión:', error);
        }
      });
    });
  
    function getCSRFToken() {
      return $('input[name=csrfmiddlewaretoken]').val();
    }
});

// Funciones para el Modal de Imagen
function mostrarImagen(img) {
    var modal = document.getElementById('modal-imagen');
    var imagenAmpliada = document.getElementById('imagen-ampliada');
    
    // Asignamos la fuente de la imagen clickeada al modal
    imagenAmpliada.src = img.src;
    modal.style.display = 'flex'; // Usamos flex para centrar gracias al CSS
}

function cerrarImagen() {
    document.getElementById('modal-imagen').style.display = 'none';
}