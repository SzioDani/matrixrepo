# -*- coding: utf-8 -*-

"""
Modulo TMDb per ClipboardPlus.
Gestisce:
- ricerca film / serie / persone
- popup dettagliati
- riconoscimento ID diretto
- integrazione con tmdbscraper
"""

from __future__ import absolute_import, unicode_literals

import xbmc
import xbmcgui

# Moduli TMDb
from resources.lib.tmdbscraper import data_utils
from resources.lib.tmdbscraper import api_utils
from resources.lib.tmdbscraper import cache as tmdb_cache
from resources.lib.tmdbscraper import tmdb as tmdb_api
from resources.lib.tmdb_settings_reader import get_tmdb_settings


# ============================================================
#   SETTINGS
# ============================================================

SETTINGS = get_tmdb_settings()
TMDB_API_KEY = "af3a53eb387d57fc935e9128468b1899"
BASE_URL = "https://api.themoviedb.org/3"


# ============================================================
#   SUPPORTO
# ============================================================

def log(msg):
    xbmc.log("[ClipboardPlus TMDb] " + str(msg), xbmc.LOGINFO)


def clean_text(text):
    return data_utils._clean_plot(text)


def show_notification(title, message):
    xbmcgui.Dialog().notification(title, message, xbmcgui.NOTIFICATION_INFO, 3000)


# ============================================================
#   CACHE
# ============================================================

def cache_get(show_id):
    return tmdb_cache.load_show_info_from_cache(show_id)


def cache_set(show_info):
    tmdb_cache.cache_show_info(show_info)


# ============================================================
#   RICERCA TMDb
# ============================================================

def search_movie(query):
    url = f"{BASE_URL}/search/movie"
    params = {
        "api_key": TMDB_API_KEY,
        "query": query,
        "language": SETTINGS["LANG_DETAILS"]
    }
    return (api_utils.load_info(url, params=params) or {}).get("results", [])


def search_tv(query):
    url = f"{BASE_URL}/search/tv"
    params = {
        "api_key": TMDB_API_KEY,
        "query": query,
        "language": SETTINGS["LANG_DETAILS"]
    }
    return (api_utils.load_info(url, params=params) or {}).get("results", [])


def search_person(query):
    url = f"{BASE_URL}/search/person"
    params = {
        "api_key": TMDB_API_KEY,
        "query": query,
        "language": SETTINGS["LANG_DETAILS"]
    }
    return (api_utils.load_info(url, params=params) or {}).get("results", [])


# ============================================================
#   RICONOSCIMENTO AUTOMATICO
# ============================================================

def detect_media_type(query):
    parsed = data_utils.parse_media_id(query)
    if parsed:
        return {
            "type": "id",
            "id_type": parsed["type"],
            "id_value": parsed["title"]
        }

    movies = search_movie(query)
    tvshows = search_tv(query)
    persons = search_person(query)

    if movies:
        return {"type": "movie", "results": movies}
    if tvshows:
        return {"type": "tv", "results": tvshows}
    if persons:
        return {"type": "person", "results": persons}

    return {"type": "none", "results": []}


# ============================================================
#   SCELTA MULTIPLA
# ============================================================

def choose_from_results(results, media_type):
    if not results:
        return None

    if len(results) == 1:
        return results[0]["id"]

    dialog = xbmcgui.Dialog()
    items = []

    for r in results:
        title = r.get("title") or r.get("name")
        year = ""

        if r.get("release_date"):
            year = f" ({r['release_date'][:4]})"
        if r.get("first_air_date"):
            year = f" ({r['first_air_date'][:4]})"

        items.append(f"{title}{year}")

    index = dialog.select(f"Scegli {media_type}", items)
    return results[index]["id"] if index != -1 else None


# ============================================================
#   POPUP FILM (VERSIONE FIXED)
# ============================================================

def show_movie_popup(movie_id):
    try:
        data = tmdb_api.get_movie(movie_id)
        if not data:
            show_notification("TMDb", "Impossibile ottenere dettagli film.")
            return

        cache_set(data)

        title = data.get("title") or data.get("name") or "Titolo sconosciuto"
        year = (data.get("release_date") or "")[:4]
        plot = clean_text(data.get("overview") or "Nessuna trama disponibile.")
        rating = data.get("vote_average") or 0
        votes = data.get("vote_count") or 0

        text = (
            f"[B]{title}[/B] ({year})\n\n"
            f"[B]Rating TMDb:[/B] {rating} ({votes} voti)\n\n"
            f"[B]Trama:[/B]\n{plot}"
        )

        safe_text = text.encode("utf-8", "ignore").decode("utf-8")
        safe_title = f"TMDb – {title}".encode("utf-8", "ignore").decode("utf-8")

        xbmcgui.Dialog().textviewer(safe_title, safe_text)

    except Exception as e:
        log(f"Errore popup film: {e}")
        show_notification("TMDb", "Errore durante l'apertura del popup.")


# ============================================================
#   POPUP SERIE TV
# ============================================================

def show_tv_popup(tv_id):
    data = tmdb_api.get_tv(tv_id)
    if not data:
        show_notification("TMDb", "Impossibile ottenere dettagli serie.")
        return

    cache_set(data)

    title = data.get("name")
    year = data.get("first_air_date", "")[:4]
    plot = clean_text(data.get("overview", ""))
    rating = data.get("vote_average", 0)
    votes = data.get("vote_count", 0)

    text = f"[B]{title}[/B] ({year})\n\n"
    text += f"[B]Rating TMDb:[/B] {rating} ({votes} voti)\n\n"
    text += f"[B]Trama:[/B]\n{plot}"

    xbmcgui.Dialog().textviewer(f"TMDb – {title}", text)


# ============================================================
#   POPUP PERSONA
# ============================================================

def show_actor_popup(person_id):
    data = tmdb_api.get_person(person_id)
    if not data:
        show_notification("TMDb", "Impossibile ottenere dettagli attore.")
        return

    name = data.get("name")
    bio = clean_text(data.get("biography", ""))

    text = f"[B]{name}[/B]\n\n"
    text += f"[B]Biografia:[/B]\n{bio[:800]}..."

    xbmcgui.Dialog().textviewer(f"TMDb – {name}", text)


# ============================================================
#   FUNZIONE PRINCIPALE
# ============================================================

def handle_tmdb_query(query):
    if not query or not query.strip():
        return False

    query = query.strip()
    result = detect_media_type(query)
    media_type = result.get("type")

    # ID diretti
    if media_type == "id":
        id_type = result["id_type"]
        id_value = result["id_value"]

        if id_type == "tmdb_movie":
            show_movie_popup(id_value)
            return True

        if id_type == "tmdb_tv":
            show_tv_popup(id_value)
            return True

        if id_type == "tmdb_person":
            show_actor_popup(id_value)
            return True

        return False

    # Film
    if media_type == "movie":
        movie_id = choose_from_results(result["results"], "film")
        if movie_id:
            show_movie_popup(movie_id)
            return True
        return False

    # Serie TV
    if media_type == "tv":
        tv_id = choose_from_results(result["results"], "serie TV")
        if tv_id:
            show_tv_popup(tv_id)
            return True
        return False

    # Attore
    if media_type == "person":
        person_id = choose_from_results(result["results"], "attore")
        if person_id:
            show_actor_popup(person_id)
            return True
        return False

    return False