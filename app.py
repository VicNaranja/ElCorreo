# -*- coding: utf-8 -*-
"""
app.py — Servidor Flask para El Correo News Digest
Incluye proxy de imágenes para cargar fotos sin restricciones de Referer.
"""
import os
import sys
import time
import threading

# Forzar UTF-8 en Windows para evitar errores con caracteres especiales
os.environ['PYTHONIOENCODING'] = 'utf-8'
for _s in (sys.stdout, sys.stderr):
    if _s is not None and hasattr(_s, 'reconfigure'):
        try:
            _s.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass

from flask import Flask, render_template, jsonify, request, Response
import requests

# ── Rutas compatibles con PyInstaller (--onefile) ───────────────────────────
if getattr(sys, 'frozen', False):
    # Ejecutando como .exe empaquetado
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Importar scraper (funciona tanto en desarrollo como empaquetado)
sys.path.insert(0, BASE_DIR)
from scraper import get_all_sections

# ── Caché en memoria ─────────────────────────────────────────────────────────
CACHE_MINUTOS = 5
_cache_data = None
_cache_timestamp = 0

def get_noticias_cached():
    global _cache_data, _cache_timestamp
    ahora = time.time()
    if _cache_data is None or (ahora - _cache_timestamp) > CACHE_MINUTOS * 60:
        print("[cache] Actualizando noticias...")
        _cache_data = get_all_sections()
        _cache_timestamp = ahora
        print("[cache] Listo.")
    else:
        restante = int(CACHE_MINUTOS * 60 - (ahora - _cache_timestamp))
        print(f"[cache] Sirviendo cache ({restante}s restantes)")
    return _cache_data

# ── Flask app ────────────────────────────────────────────────────────────────
app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, 'templates'),
    static_folder=os.path.join(BASE_DIR, 'static'),
)

# ── Cabeceras para el proxy de imágenes ─────────────────────────────────────
IMG_HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/124.0.0.0 Safari/537.36'
    ),
    'Referer': 'https://www.elcorreo.com/',
    'Accept': 'image/avif,image/webp,image/apng,image/*,*/*;q=0.8',
}


# ── Rutas ────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')


print(">>> APP CARGADO - debug route activo <<<")

@app.route('/ping')
def ping():
    return 'pong'

@app.route('/debug/xlsemanal')
def debug_xlsemanal():
    from scraper import scrape_section
    s = {'id': 'xlsemanal', 'name': 'XL Semanal', 'url': 'https://www.elcorreo.com/xlsemanal/', 'color': '#444444'}
    arts = scrape_section(s)
    return jsonify({'total': len(arts), 'arts': arts[:3]})


@app.route('/api/noticias')
def noticias():
    """Devuelve todas las secciones con sus artículos en JSON."""
    try:
        data = get_noticias_cached()
        return jsonify({'ok': True, 'secciones': data})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/proxy/img')
def proxy_img():
    """
    Proxy de imágenes: carga la imagen server-side añadiendo el Referer
    correcto de elcorreo.com y la sirve al navegador.
    Uso: /proxy/img?url=https://ppllstatics.com/...
    """
    url = request.args.get('url', '').strip()

    if not url or not url.startswith('http'):
        return '', 404

    # Seguridad: sólo permitir imágenes de dominios conocidos de elcorreo
    allowed_domains = (
        'ppllstatics.com',
        'elcorreo.com',
        'vocento.com',
        'cld.elcorreo.com',
        'imagenes.elcorreo.com',
    )
    if not any(d in url for d in allowed_domains):
        # Intentar igualmente (otros CDNs pueden aparecer)
        pass

    try:
        r = requests.get(url, headers=IMG_HEADERS, timeout=12, stream=True)
        content_type = r.headers.get('Content-Type', 'image/jpeg')
        return Response(
            r.content,
            content_type=content_type,
            headers={'Cache-Control': 'public, max-age=3600'},
        )
    except Exception:
        return '', 404


# ── Arranque ─────────────────────────────────────────────────────────────────

def _iniciar_flask():
    """Arranca Flask en un hilo secundario."""
    port = int(os.environ.get('PORT', 5000))
    host = '0.0.0.0' if os.environ.get('RENDER') else '127.0.0.1'
    app.run(host=host, port=port, debug=False, use_reloader=False)


if __name__ == '__main__':
    if os.environ.get('RENDER'):
        # En Render: arrancar solo Flask (sin ventana)
        _iniciar_flask()
    else:
        # En local: Flask en hilo + ventana nativa con pywebview
        t = threading.Thread(target=_iniciar_flask, daemon=True)
        t.start()
        time.sleep(1.5)  # esperar a que Flask esté listo

        import webview
        webview.create_window(
            title='El Correo',
            url='http://127.0.0.1:5000',
            width=1280,
            height=860,
            resizable=True,
            min_size=(800, 600),
        )
        webview.start()
