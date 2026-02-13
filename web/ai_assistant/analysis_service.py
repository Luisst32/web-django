import google.generativeai as genai
from django.conf import settings
import os

def analyze_trending_posts(posts_data):
    """
    Analiza posts (texto e imágenes) usando Gemini con acento Guayaco.
    posts_data: lista de dicts con:
        - descripcion (str)
        - imagen_url (str o None)
        - comentarios (list of str)
        - likes (int)
    """
    
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        return "¡Chuta! No encuentro la llave de Gemini, ñaño. Revisa el .env."

    genai.configure(api_key=api_key)
    
    # Modelo a usar (Gemini 1.5 Flash es el estándar actual y rápido)
    model = genai.GenerativeModel('gemini-3-flash-preview')

    prompt_parts = [
        "Eres un crítico de redes sociales 'Guayaco' (de Guayaquil)."

    ]

    import PIL.Image

    for i, post in enumerate(posts_data):
        prompt_parts.append(f"\n--- Publicación {i} ---")
        prompt_parts.append(f"Descripción: {post.get('descripcion', '')}")
        prompt_parts.append(f"Likes: {post.get('likes', 0)}")
        prompt_parts.append(f"Comentarios: {', '.join(post.get('comentarios', []))}")
        
        # Procesamiento de imagen real
        img_url = post.get('imagen_url')
        if img_url:
            try:
                # Convertir URL relativa (/media/...) a ruta absoluta del sistema
                # Asumimos que img_url empieza con /media/
                relative_path = img_url.lstrip('/')
                image_path = os.path.join(settings.BASE_DIR, relative_path)
                
                if os.path.exists(image_path):
                    img = PIL.Image.open(image_path)
                    prompt_parts.append("Mira la foto asociada a esta publicación:")
                    prompt_parts.append(img)
                else:
                    prompt_parts.append(f"[Imagen no encontrada en ruta: {image_path}]")
            except Exception as e:
                prompt_parts.append(f"[Error cargando imagen: {str(e)}]")
        
    prompt_parts.append("\nResponde SOLAMENTE en JSON con este formato exacto: [{\"index\": 0, \"analisis\": \"...\"}, ...]. Si hay foto, comenta sobre ella con tu estilo guayaco pero en nota suave, nada de ser grosero.")

    try:
        response = model.generate_content(prompt_parts)
        
        # Check if response is valid (not blocked by safety)
        if not response.parts:
             print(f"⚠️ Gemini Safety Block or Empty Response: {response.prompt_feedback}")
             return '[{"index": 0, "analisis": "La IA se puso tímida (Contenido bloqueado por seguridad)."}]'

        # Limpieza básica por si el modelo devuelve bloques de código markdown
        clean_text = response.text.replace('```json', '').replace('```', '').strip()
        print("✅ Respuesta Gemini recibida:", clean_text[:100]) # Debug
        return clean_text
    except Exception as e:
        print(f"❌ Error Gemini: {e}") # Debug crítico para ver por qué falla
        # En caso de error, devolvemos un JSON de fallback
        return '[{"index": 0, "analisis": "Se dañó esta hvrga de IA (Error Técnico)."}, {"index": 1, "analisis": "No valgo vrga hoy."}]'
