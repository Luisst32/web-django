
/* =========================================
   feed_managers.js
   Maneja la lógica global del feed: Audio, Reacciones, WebSockets, Modales.
   ========================================= */

// --- 1. GESTOR DE AUDIO IMPLÍCITO ---
let currentAudio = null;
let currentBtnIcon = null;

function toggleAudio(btn, postId, start, end) {
    var audio = document.getElementById('audio-post-' + postId);
    var icon = document.getElementById('icon-audio-' + postId);

    if (audio.paused) {
        // Pausar otro audio si existe
        if (currentAudio && currentAudio !== audio) {
            currentAudio.pause();
            if (currentBtnIcon) currentBtnIcon.className = 'bi bi-volume-mute-fill';
        }

        // Asegurar que los datos estén en el dataset (por si no estaban en el HTML)
        audio.dataset.start = start;
        audio.dataset.end = end;

        // Ajustar tiempo si es necesario
        if (audio.currentTime < start || audio.currentTime >= end) {
            audio.currentTime = start;
        }

        audio.play().then(() => {
            icon.className = 'bi bi-volume-up-fill';
            currentAudio = audio;
            currentBtnIcon = icon;
        }).catch(e => console.log("Error play:", e));

    } else {
        audio.pause();
        icon.className = 'bi bi-volume-mute-fill';
        currentAudio = null;
        currentBtnIcon = null;
    }
}

// Bucle de audio (Global)
document.addEventListener('timeupdate', function (e) {
    if (e.target.tagName === 'AUDIO') {
        var audio = e.target;
        var start = parseFloat(audio.dataset.start);
        var end = parseFloat(audio.dataset.end);

        if (!isNaN(start) && !isNaN(end)) {
            if (audio.currentTime >= end) {
                audio.currentTime = start;
                // No llamamos a play() aquí para evitar recursion innecesaria, 
                // el navegador seguirá reproduciendo si ya lo estaba.
            }
        }
    }
}, true);


// --- 2. INTERSECTION OBSERVER (Auto Pausa + VIRTUALIZACIÓN) ---
let audioObserver = null;

function initAudioObserver() {
    if (audioObserver) return;

    let observerOptions = { root: null, rootMargin: '100px', threshold: 0.1 }; // Margin amplio
    audioObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            let audio = entry.target.querySelector('audio');
            if (!audio) return;

            // --- A) SALIENDO DE PANTALLA (Descargar) ---
            if (!entry.isIntersecting) {
                // 1. Pausar si suena
                if (!audio.paused) {
                    audio.pause();
                    let postId = audio.id.replace('audio-post-', '');
                    let icon = document.getElementById('icon-audio-' + postId);
                    if (icon) icon.className = 'bi bi-volume-mute-fill';
                    if (currentAudio === audio) {
                        currentAudio = null;
                        currentBtnIcon = null;
                    }
                }

                // (Virtualización eliminada para estabilidad)
                // Resetear tiempo al inicio
                var startPosition = parseFloat(audio.dataset.start) || 0;
                audio.currentTime = startPosition;
            }

            // --- B) ENTRANDO A PANTALLA (Recargar) ---
            else {
                // (Virtualización eliminada para estabilidad)
            }
        });
    }, observerOptions);
}

function observeAudioWrappers(container) {
    if (!audioObserver) initAudioObserver();

    let scope = container || document;

    // CASO 1: El container mismo es un wrapper
    if (scope.classList && scope.classList.contains('media-wrapper')) {
        audioObserver.observe(scope);
    }

    // CASO 2: Buscar dentro del container
    if (scope.querySelectorAll) {
        let wrappers = scope.querySelectorAll('.media-wrapper');
        wrappers.forEach(el => audioObserver.observe(el));
    }
}


// --- 3. REACCIONES (Delegación de eventos Global) ---
function getCSRFToken() { return $('input[name=csrfmiddlewaretoken]').val() || ''; }

$(document).on('click', '.btn-accion', function (e) {
    e.preventDefault();
    var boton = $(this);
    var tipo = boton.data('tipo');
    var postId = boton.data('id');
    var container = boton.closest('.acciones-container');

    if (!tipo || !postId) return;

    $.ajax({
        url: `/publicaciones/${postId}/reaccion/${tipo}/`,
        type: 'POST',
        headers: { 'X-CSRFToken': getCSRFToken() },
        success: function (data) {
            if (data.success) {
                container.find('.love-count').text(data.love_count);
                container.find('.fun-count').text(data.fun_count);
                container.find('.btn-accion').removeClass('active');

                if (data.user_reaction !== undefined) {
                    if (data.user_reaction == 1) container.find('.btn-love').addClass('active');
                    else if (data.user_reaction == 2) container.find('.btn-dislike').addClass('active');
                }

                // Efecto visual
                boton.find('i').css('transform', 'scale(1.3)');
                setTimeout(() => boton.find('i').css('transform', 'scale(1)'), 200);
            }
        }
    });
});


// --- 4. MODALES COMENTARIOS (Global) ---
function abrirModalComentarios() {
    const modal = document.getElementById('modal-comentarios-global');
    const contenido = document.getElementById('contenido-modal-comentarios');
    if (modal && contenido) {
        modal.style.display = 'flex';
        contenido.innerHTML = '<div style="padding:40px; text-align:center;">Cargando...</div>';
    }
}

function cerrarModalComentarios() {
    const modal = document.getElementById('modal-comentarios-global');
    if (modal) modal.style.display = 'none';
}

document.addEventListener("DOMContentLoaded", function () {
    const modal = document.getElementById('modal-comentarios-global');
    if (modal) {
        modal.addEventListener('click', function (e) {
            if (e.target === this) cerrarModalComentarios();
        });
    }
});


// --- 5. WEBSOCKET FEED (Singleton) ---
let feedSocket = null;

function initFeedSocket() {
    if (feedSocket && (feedSocket.readyState === WebSocket.OPEN || feedSocket.readyState === WebSocket.CONNECTING)) return;

    const wsProto = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
    feedSocket = new WebSocket(`${wsProto}${window.location.host}/ws/feed/`);

    feedSocket.onmessage = function (e) {
        const data = JSON.parse(e.data);
        if (data.type === 'reaction_update') {
            const container = $(`.btn-accion[data-id="${data.post_id}"]`).closest('.acciones-container');
            if (container.length) {
                container.find('.love-count').text(data.love_count);
                container.find('.fun-count').text(data.fun_count);
                container.find('.count').addClass('updated');
                setTimeout(() => container.find('.count').removeClass('updated'), 500);
            }
        }
    };

    feedSocket.onclose = function (e) {
        console.log("Feed socket closed.");
    };
}


// --- 6. INICIALIZACIÓN FINAL ---
document.addEventListener('DOMContentLoaded', function () {
    initAudioObserver();
    observeAudioWrappers(document);
    initFeedSocket();
});

// Hook para HTMX (Infinite Scroll)
if (typeof htmx !== 'undefined') {
    htmx.onLoad(function (elt) {
        observeAudioWrappers(elt);
    });
}
