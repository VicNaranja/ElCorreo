"""
scraper.py — Extrae noticias de elcorreo.com por secciones
"""
import requests
from bs4 import BeautifulSoup
import re

# Regex para detectar y filtrar anuncios / contenido promocional
AD_REGEX = re.compile(
    r'suscri[pbó]|publicidad|nueva app|descarga|oferplan|jantour|'
    r'patrocin|anuncio|promo[^t]|regístrate|dating|encuentros|'
    r'accede gratis|hazte socio|boletín|newsletter|oferta|especial publicitario',
    re.IGNORECASE
)

SECTIONS = [
    {'id': 'bizkaia',    'name': 'Bizkaia',       'url': 'https://www.elcorreo.com/bizkaia/',              'color': '#0055aa'},
    {'id': 'politica',   'name': 'Política',       'url': 'https://www.elcorreo.com/politica/',             'color': '#cc2200'},
    {'id': 'mundo',      'name': 'Mundo',          'url': 'https://www.elcorreo.com/internacional/',        'color': '#cc5500'},
    {'id': 'economia',   'name': 'Economía',       'url': 'https://www.elcorreo.com/economia/',             'color': '#007744'},
    {'id': 'deportes',   'name': 'Deportes',       'url': 'https://www.elcorreo.com/deportes/',             'color': '#006633'},
    {'id': 'athletic',   'name': 'Athletic',       'url': 'https://www.elcorreo.com/athletic/',             'color': '#cc0011'},
    {'id': 'sociedad',   'name': 'Sociedad',       'url': 'https://www.elcorreo.com/sociedad/',             'color': '#7700aa'},
    {'id': 'salud',      'name': 'Salud',          'url': 'https://www.elcorreo.com/sociedad/salud/',       'color': '#009977'},
    {'id': 'tecnologia', 'name': 'Tecnología',     'url': 'https://www.elcorreo.com/tecnologia/',           'color': '#0077cc'},
    {'id': 'cultura',    'name': 'Cultura',        'url': 'https://www.elcorreo.com/culturas/',             'color': '#884400'},
    {'id': 'vivir',      'name': 'Vivir',          'url': 'https://www.elcorreo.com/vivir/',                'color': '#aa6600'},
    {'id': 'gente',      'name': 'Gente & Estilo', 'url': 'https://www.elcorreo.com/gente-estilo/',         'color': '#aa0077'},
    {'id': 'xlsemanal',  'name': 'XL Semanal',     'url': 'https://www.elcorreo.com/xlsemanal/',            'color': '#444444'},
]

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/124.0.0.0 Safari/537.36'
    ),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Referer': 'https://www.google.com/',
    'DNT': '1',
}


def _normalizar_url(url):
    """Convierte URLs relativas de protocolo (//...) a https://"""
    if url.startswith('//'):
        return 'https:' + url
    return url

def _get_image(art_tag):
    """Intenta extraer la URL de imagen de un <article> con múltiples estrategias."""
    for attr in ('data-src', 'data-lazy-src', 'data-original', 'src'):
        img = art_tag.find('img', attrs={attr: True})
        if img:
            url = _normalizar_url(img[attr].strip())
            if url and not url.endswith('.gif') and 'placeholder' not in url and url.startswith('http'):
                return url
    img = art_tag.find('img')
    if img:
        for attr in ('data-src', 'data-lazy-src', 'src'):
            url = _normalizar_url(img.get(attr, '').strip())
            if url and url.startswith('http') and not url.endswith('.gif'):
                return url
    return ''


def scrape_section(section):
    """Scrape una sección y devuelve lista de artículos."""
    try:
        resp = requests.get(section['url'], headers=HEADERS, timeout=20)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'lxml')
    except Exception as e:
        print(f"[scraper] Error en {section['url']}: {e}")
        return []

    articles = []
    seen_titles = set()
    seen_urls = set()

    for art in soup.find_all('article'):
        h_tag = art.find(['h1', 'h2', 'h3', 'h4'])
        if not h_tag:
            continue
        title = h_tag.get_text(strip=True)
        if not title or len(title) < 12:
            continue
        if AD_REGEX.search(title):
            continue
        if title in seen_titles:
            continue

        a_tag = h_tag.find('a') or art.find('a', href=True)
        url = ''
        if a_tag and a_tag.get('href'):
            href = a_tag['href']
            if href.startswith('http'):
                url = href
            elif href.startswith('/'):
                url = 'https://www.elcorreo.com' + href
        if url and '?' in url:
            url = url.split('?')[0]
        if url in seen_urls and url:
            continue

        p_tag = art.find('p')
        summary = p_tag.get_text(strip=True) if p_tag else ''
        if summary and AD_REGEX.search(summary):
            continue
        if len(summary) > 220:
            summary = summary[:217] + '...'

        img_url = _get_image(art)

        seen_titles.add(title)
        if url:
            seen_urls.add(url)

        articles.append({
            't':   title,
            'res': summary,
            'url': url,
            'img': img_url,
        })

    return articles


def get_all_sections():
    """Extrae todas las secciones en paralelo y devuelve la estructura completa."""
    from concurrent.futures import ThreadPoolExecutor, as_completed

    def fetch(s):
        print(f"[scraper] Extrayendo {s['name']}...")
        arts = scrape_section(s)
        print(f"[scraper]   -> {len(arts)} articulos")
        return s, arts

    results_map = {}
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {executor.submit(fetch, s): s for s in SECTIONS}
        for future in as_completed(futures):
            s, arts = future.result()
            results_map[s['id']] = arts

    return [
        {
            'id':    s['id'],
            'name':  s['name'],
            'color': s['color'],
            'arts':  results_map.get(s['id'], []),
        }
        for s in SECTIONS
    ]


if __name__ == '__main__':
    data = get_all_sections()
    total = sum(len(s['arts']) for s in data)
    print(f"\nTotal articulos: {total}")
    for s in data:
        print(f"  {s['name']}: {len(s['arts'])} articulos")
