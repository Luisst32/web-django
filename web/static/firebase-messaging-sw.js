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
    console.log('[firebase-messaging-sw.js] Mensaje recibido en segundo plano ', payload);
    // FCM SDK automatically displays a notification if the payload contains a 'notification' object.
    // We shouldn't call self.registration.showNotification manually here to avoid duplicates.
});
