importScripts("https://www.gstatic.com/firebasejs/10.12.2/firebase-app-compat.js");
importScripts("https://www.gstatic.com/firebasejs/10.12.2/firebase-messaging-compat.js");

const firebaseConfig = {
    apiKey: "AIzaSyB29uXCTf2xtf-qqPLfLSOYjLUW1mQ3enI",
    authDomain: "app1-29128.firebaseapp.com",
    projectId: "app1-29128",
    storageBucket: "app1-29128.firebasestorage.app",
    messagingSenderId: "582131743674",
    appId: "1:582131743674:web:b7f90ed11490ad8f19bb83"
};

firebase.initializeApp(firebaseConfig);
const messaging = firebase.messaging();

messaging.onBackgroundMessage(function(payload) {
    console.log('[sw.js] Mensaje recibido en segundo plano ', payload);
    const notificationTitle = payload.notification.title || 'Nuevo mensaje';
    const notificationOptions = {
        body: payload.notification.body,
        icon: '/static/icons/icon-192x192.png',
        data: payload.data || {}
    };

    self.registration.showNotification(notificationTitle, notificationOptions);
});

self.addEventListener('notificationclick', function (event) {
    event.notification.close();
    var urlToOpen = (event.notification.data && event.notification.data.url) ? event.notification.data.url : '/chat/';
    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true }).then(function (windowClients) {
            for (var i = 0; i < windowClients.length; i++) {
                var client = windowClients[i];
                if (client.url.includes(urlToOpen) && 'focus' in client) {
                    return client.focus();
                }
            }
            if (clients.openWindow) {
                return clients.openWindow(urlToOpen);
            }
        })
    );
});