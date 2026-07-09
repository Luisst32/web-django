
    // Creamos la referencia de audio UNA sola vez para poder desbloquerala
    window._chatAudioRef = new Audio(window.DjangoVars.chatAudioUrl);
    window._chatAudioRef.preload = 'auto';
    window._chatAudioRef.volume = 1.0;

    window.playNotificationSound = function() {
        try {
            window._chatAudioRef.currentTime = 0;
            var p = window._chatAudioRef.play();
            if (p) p.catch(function(e) { console.warn('[Sound] bloqueado:', e.message); });
        } catch(e) { console.warn('[Sound] error:', e); }
    };

    window.playCallRingtone = function() {
        try {
            var r = document.getElementById('call-ringtone');
            if (r) { r.currentTime = 0; r.play().catch(function(e){}); }
        } catch(e) {}
    };

    window.stopCallRingtone = function() {
        try {
            var r = document.getElementById('call-ringtone');
            if (r) { r.pause(); r.currentTime = 0; }
        } catch(e) {}
    };

    // Desbloquear en primer toque/click
    (function() {
        var unlocked = false;
        function unlock() {
            if (unlocked) return;
            unlocked = true;
            window._chatAudioRef.play().then(function() {
                window._chatAudioRef.pause();
                window._chatAudioRef.currentTime = 0;
                console.log('[Sound] audio desbloqueado OK');
            }).catch(function(e) { console.warn('[Sound] unlock failed:', e.message); });
        }
        document.addEventListener('click', unlock, { once: true });
        document.addEventListener('touchstart', unlock, { once: true });
        document.addEventListener('keydown', unlock, { once: true });
    })();


    document.addEventListener('DOMContentLoaded', function () {
        const protocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';

        // Elemento de audio base para obtener la URL
        const chatAudioUrl = window.DjangoVars.chatAudioUrl;

        // ---- NOTI SOCKET CON AUTO-RECONEXIÓN Y KEEPALIVE ----
        let notiSocket = null;
        let notiReconnectTimer = null;
        let notiHeartbeat = null;

        function connectNotiSocket() {
            // Limpiar reconexión pendiente
            if (notiReconnectTimer) {
                clearTimeout(notiReconnectTimer);
                notiReconnectTimer = null;
            }

            notiSocket = new WebSocket(protocol + window.location.host + '/ws/notifications/');

            notiSocket.onopen = function () {
                console.log('[NotiSocket] Conectado');
                // Keepalive ping cada 25 segundos para evitar timeout del servidor
                notiHeartbeat = setInterval(function () {
                    if (notiSocket && notiSocket.readyState === WebSocket.OPEN) {
                        notiSocket.send(JSON.stringify({ action: 'heartbeat' }));
                    }
                }, 25000);
            };

            notiSocket.onmessage = function (e) {
                const data = JSON.parse(e.data);
                if (data.type === 'notification') {
                    updateNotiBadge(1);
                    const bell = document.querySelector('#notiDropdown i');
                    if (bell) {
                        bell.classList.add('bell-animate');
                        setTimeout(() => bell.classList.remove('bell-animate'), 500);
                    }
                    const notiList = document.getElementById('notiList');
                    if (notiList && notiList.classList.contains('show')) {
                        htmx.trigger('#notiDropdown', 'click');
                    }
                } else if (data.type === 'chat_count_update') {
                    // Reproducir sonido siempre que llegue un mensaje nuevo (count > 0)
                    if (data.count > 0) {
                        window.playNotificationSound();
                    }

                    // 1. Badge Global
                    updateChatBadge(data.count);

                    // 2. Badge Individual (Si existe en la lista)
                    if (data.sender_id) {
                        updateUserBadge(data.sender_id);
                    }
                }
            };

            notiSocket.onerror = function (e) {
                console.warn('[NotiSocket] Error:', e);
            };

            notiSocket.onclose = function (e) {
                console.warn('[NotiSocket] Cerrado (code ' + e.code + '). Reconectando en 3s...');
                if (notiHeartbeat) { clearInterval(notiHeartbeat); notiHeartbeat = null; }
                // Reconectar automáticamente a los 3 segundos
                notiReconnectTimer = setTimeout(connectNotiSocket, 3000);
            };
        }

        // Conectar al iniciar
        connectNotiSocket();

        function updateChatBadge(count) {
            const badge = document.getElementById('chat-badge');
            if (badge) {
                badge.textContent = count;
                if (count > 0) badge.classList.remove('d-none');
                else badge.classList.add('d-none');
            }
        }

        function updateUserBadge(senderId) {
            // Buscar badge específico del usuario en la lista de contactos
            const userBadge = document.getElementById('unread-badge-' + senderId);
            const userMsgPreview = document.getElementById('msg-preview-' + senderId);

            if (userBadge) {
                // Incrementar visualmente
                let current = parseInt(userBadge.textContent) || 0;
                userBadge.textContent = current + 1;
                userBadge.classList.remove('d-none');
            }

            if (userMsgPreview) {
                userMsgPreview.classList.add('fw-bold', 'text-dark');
                userMsgPreview.classList.remove('text-muted');
                userMsgPreview.textContent = "Nuevo mensaje..."; // Opcional: cambiar texto momentáneamente
            }
        }

        function updateNotiBadge(count) {
            const badge = document.getElementById('noti-badge');
            if (badge) {
                let current = parseInt(badge.textContent) || 0;
                let total = current + count;
                badge.textContent = total;
                if (total > 0) {
                    badge.classList.remove('d-none');
                } else {
                    badge.classList.add('d-none');
                }
            }
        }

        // Clear badge when opening dropdown
        const notiBtn = document.getElementById('notiDropdown');
        if (notiBtn) {
            notiBtn.addEventListener('click', function () {
                const badge = document.getElementById('noti-badge');
                if (badge) {
                    badge.textContent = '0';
                    badge.classList.add('d-none');
                }
            });
        }
    });

    function toggleMessagePanel() {
        const panel = document.getElementById('message-panel');
        const trigger = document.getElementById('chat-compact-trigger');
        const badge = document.getElementById('chat-badge');

        // Determinar si estamos cerrando
        const closing = panel && panel.classList.contains('active');

        // Toggle Visual
        if (closing) {
            panel.classList.remove('active');
            if (trigger) trigger.classList.remove('hidden');
        } else {
            if (panel) panel.classList.add('active');
            if (trigger) trigger.classList.add('hidden');

            // LIMPIAR BADGE Y LLAMAR BACKEND
            if (badge) {
                badge.classList.add('d-none');
                badge.innerText = '0';

                // Intento robusto de obtener CSRF
                let token = '';
                const input = document.querySelector('[name=csrfmiddlewaretoken]');
                if (input) token = input.value;

                if (token) {
                    fetch("{% url 'update_messages_check_time' %}", {
                        method: 'POST',
                        headers: {
                            'X-CSRFToken': token,
                            'Content-Type': 'application/json'
                        }
                    })
                        .then(r => {
                            if (r.ok) console.log('✅ Badge reset OK');
                            else console.error('❌ Badge reset failed', r.status);
                        })
                        .catch(console.error);
                } else {
                    console.error('⚠️ CSRF Token not found for badge reset');
                }
            }
        }
    }

    function clearUserBadgeAndBold(userId) {
        // 3. Clear Badge & Bold
        const badge = document.getElementById('unread-badge-' + userId);
        const msgPreview = document.getElementById('msg-preview-' + userId);

        if (badge) {
            badge.classList.add('d-none');
            badge.textContent = '0';
        }
        if (msgPreview) {
            // Remover negrita y color oscuro
            msgPreview.classList.remove('fw-bold', 'text-dark');
            // Agregar color gris (leído)
            msgPreview.classList.add('text-muted');
        }
    }
