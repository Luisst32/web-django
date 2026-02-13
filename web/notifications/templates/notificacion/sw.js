// templates/sw.js

// 1. Escuchar el evento 'push' (Cuando llega la notificación del servidor)
self.addEventListener('push', function (event) {
    if (event.data) {
        // Recibimos los datos enviados desde Django
        const data = event.data.json();
        
        // Configuramos las opciones visuales
        const options = {
            body: data.body,           // El texto del mensaje
            icon: data.icon,           // El logo (ej: /static/logo/logo.png)
            image: data.image,         // Imagen grande (opcional)
            badge: data.badge,         // Icono pequeño para la barra de estado (Android)
            vibrate: [200, 100, 200],  // Vibración
            data: {
                url: data.url          // Guardamos la URL para usarla al hacer clic
            }
        };

        // Mostramos la notificación en el sistema
        event.waitUntil(
            self.registration.showNotification(data.head, options)
        );
    }
});

// 2. Escuchar el evento 'notificationclick' (Cuando el usuario hace clic)
self.addEventListener('notificationclick', function (event) {
    // Cerramos la notificación
    event.notification.close();

    // Obtenemos la URL que guardamos arriba
    var urlToOpen = event.notification.data.url || '/';

    // Abrimos la ventana o la enfocamos si ya está abierta
    event.waitUntil(
        clients.matchAll({
            type: 'window',
            includeUncontrolled: true
        }).then(function (windowClients) {
            // Si hay una pestaña abierta con esa URL, la enfocamos
            for (var i = 0; i < windowClients.length; i++) {
                var client = windowClients[i];
                if (client.url === urlToOpen && 'focus' in client) {
                    return client.focus();
                }
            }
            // Si no, abrimos una nueva
            if (clients.openWindow) {
                return clients.openWindow(urlToOpen);
            }
        })
    );
});