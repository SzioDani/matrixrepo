# -*- coding: utf-8 -*-

"""
Modulo TMDb di alto livello.
Aggiornato con supporto lingua nella ricerca e Fallback Inglese.
"""

from __future__ import absolute_import, unicode_literals
import xbmc
from xbmcaddon import Addon
from resources.lib.tmdbscraper import api_utils
from resources.lib.tmdbscraper import settings as tmdb_default_settings
from resources.lib.tmdb_settings_reader import get_tmdb_settings

def log(msg):
    xbmc.log("[TMDb tmdb_custom] " + str(msg), xbmc.LOGINFO)

# ============================================================
#   SETTINGS
# ============================================================

addon = Addon()
USER_SETTINGS = get_tmdb_settings()
DEFAULTS = tmdb_default_settings.getSourceSettings()

API_KEY = addon.getSetting("tmdb_api_key") or "af3a53eb387d57fc935e9128468b1899"
BASE_URL = "https://api.themoviedb.org/3"

LANG_DETAILS = USER_SETTINGS.get("LANG_DETAILS", "it-IT")
LANG_IMAGES = USER_SETTINGS.get("LANG_IMAGES", "it")
SEARCH_LANG = USER_SETTINGS.get("SEARCH_LANG", LANG_DETAILS)
CERT_COUNTRY = USER_SETTINGS.get("CERT_COUNTRY", "IT")
ENABLE_TRAILER = USER_SETTINGS.get("ENABTRAILER", True)

# ============================================================
#   FUNZIONI DI ALTO LIVELLO
# ============================================================

def get_movie(movie_id, lang=None):
    url = f"{BASE_URL}/movie/{movie_id}"
    target_lang = lang if lang else LANG_DETAILS
    append = ["credits", "images", "keywords", "release_dates", "external_ids"]
    if ENABLE_TRAILER:
        append.append("videos")

    params = {
        "api_key": API_KEY,
        "language": target_lang,
        "include_image_language": f"{LANG_IMAGES},en,null",
        "append_to_response": ",".join(append)
    }

    log(f"Carico dettagli film {movie_id} (lang={target_lang})")
    return api_utils.load_info(url, params=params)

def get_tv(tv_id, lang=None):
    url = f"{BASE_URL}/tv/{tv_id}"
    target_lang = lang if lang else LANG_DETAILS
    append = ["credits", "images", "keywords", "content_ratings", "external_ids"]
    if ENABLE_TRAILER:
        append.append("videos")

    params = {
        "api_key": API_KEY,
        "language": target_lang,
        "include_image_language": f"{LANG_IMAGES},en,null",
        "append_to_response": ",".join(append)
    }

    log(f"Carico dettagli serie {tv_id} (lang={target_lang})")
    return api_utils.load_info(url, params=params)

def get_person(person_id, lang=None):
    url = f"{BASE_URL}/person/{person_id}"
    target_lang = lang if lang else LANG_DETAILS

    params = {
        "api_key": API_KEY,
        "language": target_lang,
        "append_to_response": "images,combined_credits"
    }

    log(f"Carico dettagli persona {person_id} (lang={target_lang})")
    data = api_utils.load_info(url, params=params)

    if not data or not data.get("biography") or not data.get("name"):
        log(f"Dati incompleti per {person_id} in {target_lang}. Provo fallback en-US...")
        params["language"] = "en-US"
        data_en = api_utils.load_info(url, params=params)
        if data_en:
            return data_en
            
    return data

# ============================================================
#   RICERCA (CORRETTA)
# ============================================================

def search_multi(query, lang=None):
    """
    Ricerca mista. Ora accetta il parametro lang per evitare TypeError nel bridge.
    """
    url = f"{BASE_URL}/search/multi"
    # Se il bridge passa una lingua, usiamo quella, altrimenti usiamo il default dei settings
    target_lang = lang if lang else SEARCH_LANG
    
    params = {
        "api_key": API_KEY,
        "query": query,
        "language": target_lang
    }

    log(f"Ricerca multi: '{query}' (lang={target_lang})")
    data = api_utils.load_info(url, params=params)
    results = data.get("results", []) if data else []

    if not results:
        log("Nessun risultato. Provo ricerca globale...")
        params.pop("language", None)
        data = api_utils.load_info(url, params=params)
        results = data.get("results", []) if data else []

    return results
    