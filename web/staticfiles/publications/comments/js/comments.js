/**
 * comments_app.js
 * Lógica de frontend para el sistema de comentarios.
 */

window.CommentsApp = (function () {

    function init(postId) {
        if (!postId) return;
        console.log(`💬 [CommentsApp] Inicializando para Post #${postId}`);
        _setupWebSocket(postId);
        _setupReplyUI(postId);
        _setupAutoResize(postId);
        _setupImageUpload(postId);
    }

    function _setupWebSocket(postId) {
        if (!window.WSManager) {
            console.error("❌ WSManager not found.");
            return;
        }

        const wsProtocol = window.location.protocol === "https:" ? "wss://" : "ws://";
        const wsUrl = `${wsProtocol}${window.location.host}/ws/post/${postId}/comments/`;
        const channelId = `post_${postId}`;

        window.WSManager.connect(channelId, wsUrl);
        window.WSManager.unsubscribe(channelId);
        window.WSManager.subscribe(channelId, (data) => _handleNewComment(postId, data));
    }

    function _handleNewComment(postId, data) {
        if (data.type === 'comment_deleted') {
            const commentId = data.comment_id;
            const element = document.getElementById(`comment-${commentId}`); // ID was comment-{{ pk }} in template
            if (element) {
                element.remove();
                console.log(`🗑️ Comentario ${commentId} eliminado via WebSocket`);
            } else {
                console.warn(`⚠️ No se encontró el elemento comentario-${commentId} para eliminar`);
            }
            return;
        }

        if (data.type !== 'new_comment') return;

        const commentHtml = data.html;
        const parentId = data.parent_id;
        const isMain = (!parentId || parentId === 'main');

        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = commentHtml.trim();
        const newElement = tempDiv.firstElementChild;
        if (!newElement) return;

        const newId = newElement.id;
        if (document.getElementById(newId)) return;

        let containerId;
        if (isMain) {
            containerId = `comentarios-container-${postId}`;
        } else {
            containerId = `replies-for-${parentId}`;
        }

        const container = document.getElementById(containerId);

        if (container) {
            if (isMain) {
                const emptyMsg = container.querySelector('.empty-comments');
                if (emptyMsg) emptyMsg.remove();

                container.insertAdjacentHTML("afterbegin", commentHtml);
                container.scrollTop = 0;

                // Process only the new first child for HTMX
                htmx.process(container.firstElementChild);
            } else {
                container.insertAdjacentHTML("beforeend", commentHtml);
                // Process the new last child
                htmx.process(container.lastElementChild);
            }
        }
    }

    function _setupReplyUI(postId) {
        const form = document.getElementById(`comment-form-${postId}`);
        const input = document.getElementById(`input-comentario-${postId}`);
        const hiddenInput = document.getElementById(`id_comentario_padre_id_${postId}`);
        const replyWrapper = document.getElementById(`reply-info-wrapper-${postId}`);
        const replyLabel = document.getElementById(`reply-target-name-${postId}`);
        const cancelBtn = document.getElementById(`cancel-reply-btn-${postId}`);

        if (!form) return;

        window[`resetReplyState_${postId}`] = function () {
            form.dataset.parentId = "";
            if (hiddenInput) hiddenInput.value = "";
            if (replyWrapper) replyWrapper.style.display = "none";
            if (replyLabel) replyLabel.innerText = "";
            if (input) input.value = '';
            // Clear image
            window[`removeImage_${postId}`]();
        };

        window[`setReplyTarget_${postId}`] = function (parentId, username) {
            form.dataset.parentId = parentId;
            if (hiddenInput) hiddenInput.value = parentId;
            if (replyWrapper) replyWrapper.style.display = "block";
            if (replyLabel) replyLabel.innerText = `@${username}`;
            if (input) input.focus();
        };

        if (cancelBtn) cancelBtn.onclick = window[`resetReplyState_${postId}`];
    }

    function _setupImageUpload(postId) {
        const fileInput = document.getElementById(`imagen-comentario-${postId}`);
        const previewContainer = document.getElementById(`preview-container-${postId}`);
        const previewImage = document.getElementById(`image-preview-${postId}`);

        if (!fileInput || !previewContainer || !previewImage) return;

        fileInput.addEventListener('change', function () {
            const file = this.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function (e) {
                    previewImage.src = e.target.result;
                    previewContainer.classList.remove('d-none');
                }
                reader.readAsDataURL(file);
            }
        });

        window[`removeImage_${postId}`] = function () {
            fileInput.value = '';
            previewImage.src = '';
            previewContainer.classList.add('d-none');
        };
    }

    function _setupAutoResize(postId) {
        const input = document.getElementById(`input-comentario-${postId}`);
        if (!input) return;

        input.addEventListener('input', function () {
            this.style.height = 'auto';
            const newHeight = Math.min(this.scrollHeight, 120);
            this.style.height = newHeight + 'px';
            if (this.value === '') this.style.height = '40px';
        });
    }

    function requestDelete(url) {
        const confirmBtn = document.getElementById('confirmDeleteBtn');
        if (!confirmBtn) return;

        // Establecer la URL de eliminación en el botón del modal
        confirmBtn.setAttribute('hx-delete', url);

        // Reprocesar el botón con HTMX para que reconozca el nuevo atributo
        htmx.process(confirmBtn);

        // Mostrar el modal (usando la API de Bootstrap 5)
        const modalElement = document.getElementById('deleteCommentModal');
        const modal = new bootstrap.Modal(modalElement);
        modal.show();
    }

    return {
        init: init,
        requestDelete: requestDelete
    };
})();
