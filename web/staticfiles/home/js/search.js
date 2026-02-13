// search.js

/**
 * Función que realiza la búsqueda de usuarios utilizando AJAX.
 * Depende de las variables globales SEARCH_URL y DEFAULT_PROFILE_PIC
 * definidas en el script de la plantilla HTML.
 */
function searchUsers() {
    var input = document.getElementById("userSearch");
    var filter = input.value.toUpperCase();
    var ul = document.getElementById("userList");

    if (filter === "") {
        ul.style.display = "none";
        return;
    }

    // Usando jQuery para la llamada AJAX
    $.ajax({
        // La URL se obtiene de la constante global inyectada por Django
        url: SEARCH_URL, 
        data: { 'q': filter },
        dataType: 'json',
        success: function(data) {
            ul.innerHTML = '';
            if (data.results.length > 0) {
                data.results.forEach(function(user) {
                    var li = document.createElement('li');
                    li.classList.add('search-result-item');
                    li.onclick = function() {
                        window.location.href = '/perfil/' + user.username;
                    };

                    var img = document.createElement('img');
                    // Usando la constante global si no hay imagen de perfil
                    img.src = user.profile_picture ? user.profile_picture : DEFAULT_PROFILE_PIC; 
                    img.classList.add('rounded-circle');
                    img.style.width = '30px';
                    img.style.marginRight = '10px';

                    var username = document.createElement('span');
                    username.textContent = user.username;

                    li.appendChild(img);
                    li.appendChild(username);
                    ul.appendChild(li);
                });
                ul.style.display = "block";
            } else {
                ul.style.display = "none";
            }
        },
        error: function() {
            console.error('Error al realizar la búsqueda AJAX');
        }
    });
}