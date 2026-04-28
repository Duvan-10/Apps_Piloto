import json
import time
from urllib.parse import quote_plus
from urllib.request import urlopen

NEWS_API_KEY = 'c3ce6259bb39400a912615fb57233328'
_CACHE_SENTIMIENTO = {}
_TTL_CACHE_SEGUNDOS = 2 * 60 * 60

_LEXICO_POSITIVO = {
    'en': ['win', 'victory', 'confident', 'ready', 'fit', 'boost', 'strong', 'signing', 'good form', 'unbeaten'],
    'es': ['victoria', 'confianza', 'listo', 'apto', 'fichaje', 'buen momento', 'invicto'],
    'de': ['sieg', 'erfolg', 'stark', 'fit', 'bereit', 'verstärkung', 'gute form', 'ungeschlagen'],
    'it': ['vittoria', 'fiducia', 'pronto', 'fit', 'rinforzo', 'buona forma', 'imbattuto'],
    'fr': ['victoire', 'confiance', 'prêt', 'apte', 'renfort', 'bonne forme', 'invaincu'],
}

_LEXICO_NEGATIVO = {
    'en': ['injury', 'out', 'miss', 'doubt', 'defeat', 'loss', 'crisis', 'bad', 'problem', 'ban'],
    'es': ['lesión', 'baja', 'duda', 'derrota', 'crisis', 'malo', 'problema', 'sanción'],
    'de': ['verletzung', 'ausfall', 'zweifel', 'niederlage', 'krise', 'schlecht', 'problem', 'sperre'],
    'it': ['infortunio', 'fuori', 'dubbio', 'sconfitta', 'crisi', 'male', 'problema', 'squalifica'],
    'fr': ['blessure', 'absent', 'doute', 'défaite', 'crise', 'mauvais', 'problème', 'suspension'],
}


def _clave_cache(nombre_equipo, liga, idioma):
    partes = [str(nombre_equipo or '').strip().lower(), str(liga or '').strip().lower(), str(idioma or '').strip().lower()]
    return '|'.join(partes)


def _leer_cache(clave):
    entrada = _CACHE_SENTIMIENTO.get(clave)
    if not entrada:
        return None

    marca_tiempo, valor = entrada
    if time.time() - marca_tiempo > _TTL_CACHE_SEGUNDOS:
        _CACHE_SENTIMIENTO.pop(clave, None)
        return None

    return valor


def _guardar_cache(clave, valor):
    _CACHE_SENTIMIENTO[clave] = (time.time(), valor)


def _limpiar_texto(valor):
    return str(valor or '').lower().strip()


def _contador_palabras(texto, palabras):
    puntaje = 0.0
    for palabra in palabras:
        if palabra in texto:
            puntaje += 0.25
    return puntaje


def _fallback_sentimiento(nombre_equipo, liga=''):
    base = f"{_limpiar_texto(nombre_equipo)}|{_limpiar_texto(liga)}"
    if not base.strip('|'):
        return 0.0

    import hashlib

    digest = hashlib.sha1(base.encode('utf-8')).hexdigest()
    valor_entero = int(digest[:8], 16)
    escala = (valor_entero / 0xFFFFFFFF) * 1.0 - 0.5
    return round(escala, 2)


def clasificar_sentimiento(puntaje):
    if puntaje > 0.1:
        return 'positivo'
    if puntaje < -0.1:
        return 'negativo'
    return 'estable'


def analizar_sentimiento_equipo(nombre_equipo, liga='', idioma='en', terminos_liga=(), etiqueta=''):
    clave = _clave_cache(nombre_equipo, liga, idioma)
    if not clave.split('|')[0]:
        return 0.0

    valor_cache = _leer_cache(clave)
    if valor_cache is not None:
        return valor_cache

    termino_equipo = f'"{nombre_equipo}"'
    termino_liga = ' '.join(str(termino).strip() for termino in terminos_liga if str(termino).strip())
    consulta = ' '.join(part for part in [termino_equipo, termino_liga, 'football'] if part)
    query = quote_plus(consulta)
    url = (
        'https://newsapi.org/v2/everything'
        f'?q={query}'
        f'&language={idioma}'
        '&searchIn=title,description'
        '&sortBy=publishedAt'
        '&pageSize=5'
        f'&apiKey={NEWS_API_KEY}'
    )

    positivas = _LEXICO_POSITIVO.get(idioma, _LEXICO_POSITIVO['en'])
    negativas = _LEXICO_NEGATIVO.get(idioma, _LEXICO_NEGATIVO['en'])
    nombre_normalizado = _limpiar_texto(nombre_equipo)

    try:
        with urlopen(url, timeout=7) as response:
            data = json.loads(response.read().decode('utf-8'))

        articulos = data.get('articles', [])[:5]
        if not articulos:
            valor = _fallback_sentimiento(nombre_equipo, liga)
            _guardar_cache(clave, valor)
            return valor

        puntaje = 0.0
        for art in articulos:
            titulo = _limpiar_texto(art.get('title', ''))
            descripcion = _limpiar_texto(art.get('description', ''))
            texto = f'{titulo} {descripcion}'.strip()

            if nombre_normalizado and nombre_normalizado in texto:
                puntaje += 0.15

            if termino_liga and _limpiar_texto(termino_liga) in texto:
                puntaje += 0.1

            puntaje += _contador_palabras(texto, positivas)
            puntaje -= _contador_palabras(texto, negativas)

        puntaje = max(min(round(puntaje / 2.5, 2), 1.0), -1.0)
        if puntaje == 0.0:
            puntaje = _fallback_sentimiento(nombre_equipo, liga)

        _guardar_cache(clave, puntaje)
        return puntaje
    except Exception as e:
        sufijo = f" ({etiqueta})" if etiqueta else ''
        print(f"Error en vigilante{sufijo} para {nombre_equipo}: {e}")
        valor = _fallback_sentimiento(nombre_equipo, liga)
        _guardar_cache(clave, valor)
        return valor