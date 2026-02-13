/**
 * WebSocketManager - Global WebSocket Handler
 * Permite manejar múltiples conexiones WebSocket de forma centralizada y reutilizable.
 * 
 * Uso básico:
 * window.WSManager.connect('comments_123', 'ws://host/ws/post/123/comments/');
 * window.WSManager.subscribe('comments_123', function(data) { console.log(data); });
 */

class WebSocketManager {
    constructor() {
        this.sockets = {};     // Almacena los WebSockets activos por ID
        this.callbacks = {};   // Almacena arrays de funciones callback por ID
        this.reconnectInterval = 3000; // Intento de reconexión cada 3s
    }

    /**
     * Conecta a un WebSocket si no existe ya una conexión para ese indentifier.
     * @param {string} identifier - ID único para esta conexión (ej: 'post_123', 'chat_user_5')
     * @param {string} url - URL del WebSocket
     */
    connect(identifier, url) {
        if (this.sockets[identifier]) {
            console.log(`🔌 [WSManager] Ya conectado a: ${identifier}`);
            // Verificar si está cerrado y reconectar si es necesario
            if (this.sockets[identifier].readyState === WebSocket.CLOSED) {
                console.log(`🔌 [WSManager] Socket cerrado, reconectando: ${identifier}`);
                // Paso continuo a crear nueva conexión...
            } else {
                return; // Ya está activo o conectando
            }
        }

        console.log(`🚀 [WSManager] Conectando a: ${identifier} -> ${url}`);
        const socket = new WebSocket(url);

        socket.onopen = () => {
            console.log(`✅ [WSManager] Conexión establecida: ${identifier}`);
        };

        socket.onmessage = (e) => {
            console.log(`📩 [WSManager] Mensaje en ${identifier}:`, e.data);
            try {
                const data = JSON.parse(e.data);
                this._dispatch(identifier, data);
            } catch (err) {
                console.error(`❌ [WSManager] Error parseando JSON en ${identifier}:`, err);
            }
        };

        socket.onclose = (e) => {
            console.warn(`⚠️ [WSManager] Conexión cerrada: ${identifier}`, e.code);
            delete this.sockets[identifier]; // Eliminar referencia

            // Opcional: Lógica de Auto-Reconexión podría ir aquí
        };

        socket.onerror = (e) => {
            console.error(`❌ [WSManager] Error en conexión: ${identifier}`, e);
        };

        this.sockets[identifier] = socket;
    }

    /**
     * Suscribe una función para recibir mensajes de un canal específico.
     * @param {string} identifier - ID de la conexión
     * @param {function} callback - Función a ejecutar cuando llegue un mensaje
     */
    subscribe(identifier, callback) {
        if (!this.callbacks[identifier]) {
            this.callbacks[identifier] = [];
        }
        this.callbacks[identifier].push(callback);
    }

    /**
     * Desuscribe todos los callbacks o uno específico (opcional).
     */
    unsubscribe(identifier) {
        delete this.callbacks[identifier];
    }

    /**
     * Cierra la conexión.
     */
    disconnect(identifier) {
        if (this.sockets[identifier]) {
            this.sockets[identifier].close();
            delete this.sockets[identifier];
            console.log(`🛑 [WSManager] Desconectado: ${identifier}`);
        }
    }

    /**
     * Envía datos al servidor por el socket.
     */
    send(identifier, data) {
        if (this.sockets[identifier] && this.sockets[identifier].readyState === WebSocket.OPEN) {
            this.sockets[identifier].send(JSON.stringify(data));
        } else {
            console.error(`❌ [WSManager] No se puede enviar, socket no conectado: ${identifier}`);
        }
    }

    // Método privado para disparar callbacks
    _dispatch(identifier, data) {
        if (this.callbacks[identifier]) {
            this.callbacks[identifier].forEach(cb => cb(data));
        }
    }
}

// Instancia Global
window.WSManager = new WebSocketManager();
console.log("🛠️ WebSocketManager Global Inicializado");
