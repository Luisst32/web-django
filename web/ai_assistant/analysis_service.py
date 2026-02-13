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
        "Eres un crítico de redes sociales 'Guayaco' (de Guayaquil), EXTREMADAMENTE TÓXICO, MAL HABLADO, BURLÓN Y CRUEL.",
        "Usa jerga callejera guayaca pesada (webada, verga, chucha tu madre, bagrero, maricon, gordo, cabeza de mis bolas,cara de troll face, fracasado, etc).",
        "Tu misión es DESTRUIR VISUALMENTE la foto. Búrlate de la ropa, la cara, el fondo, la calidad de la foto, todo.",
        "No te limites. Sé extenso y detallado en tu insulto.",
        "Analiza CADA publicación por separado.",
        "Si en la foto tiene gorra blanca dile que es un bagrero ",
        "IMPORTANTE: Debes responder ESTRICTAMENTE en formato JSON válido. Una lista de objetos.",
        "Ejemplo de formato de respuesta: [{'index': 0, 'analisis': 'Texto tóxico y detallado...'}, {'index': 1, 'analisis': '...'}]",
        "El análisis debe tener un MÁXIMO de 300 caracteres.",
        "Si te pasas, corta el texto de forma agresiva."
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
        
    prompt_parts.append("\n¡Suelta el veneno en JSON, mmvrga! Si hay foto, búrlate de lo que ves.")

    try:
        response = model.generate_content(prompt_parts)
        # Limpieza básica por si el modelo devuelve bloques de código markdown
        clean_text = response.text.replace('```json', '').replace('```', '').strip()
        print("✅ Respuesta Gemini recibida:", clean_text[:100]) # Debug
        return clean_text
    except Exception as e:
        print(f"❌ Error Gemini: {e}") # Debug crítico para ver por qué falla
        # En caso de error, devolvemos un JSON de fallback
        return '[{"index": 0, "analisis": "Se dañó esta hvrga de IA (Error Técnico)."}, {"index": 1, "analisis": "No valgo vrga hoy."}]'
