# -*- coding: utf-8 -*-

"""
Cache minimalista per TMDb.
Compatibile con:
- tmdb_utils.py
- tmdb.py

Funzioni:
    load_show_info_from_cache(id)
    cache_show_info(data)
"""

from __future__ import absolute_import, unicode_literals

import json
import os
import xbmc
import xbmcvfs


def log(msg):
    xbmc.log("[TMDb cache] " + str(msg), xbmc.LOGINFO)


# ============================================================
#   PERCORSO CACHE
# ============================================================

ADDON_DATA = xbmc.translatePath("special://profile/addon_data")
CACHE_DIR = os.path.join(ADDON_DATA, "script.clipboard.text_plus", "tmdb_cache")

if not xbmcvfs.exists(CACHE_DIR):
    xbmcvfs.mkdirs(CACHE_DIR)


# ============================================================
#   FUNZIONI CACHE
# ============================================================

def _get_cache_path(show_id):
    """
    Ritorna il percorso del file cache per un ID TMDb.
    """
    return os.path.join(CACHE_DIR, f"{show_id}.json")


def load_show_info_from_cache(show_id):
    """
    Carica i dettagli TMDb da cache locale.
    Ritorna:
        - dict con i dati
        - None se non esiste
    """
    path = _get_cache_path(show_id)

    if not xbmcvfs.exists(path):
        return None

    try:
        with xbmcvfs.File(path, "r") as f:
            data = f.read()
            return json.loads(data)
    except Exception as e:
        log(f"Errore lettura cache: {e}")
        return None


def cache_show_info(show_info):
    """
    Salva i dettagli TMDb in cache locale.
    Richiede che show_info contenga almeno:
        - "id"
    """
    if not show_info or "id" not in show_info:
        return

    show_id = show_info["id"]
    path = _get_cache_path(show_id)

    try:
        with xbmcvfs.File(path, "w") as f:
            f.write(json.dumps(show_info))
        log(f"Cache salvata per ID {show_id}")
    except Exception as e:
        log(f"Errore salvataggio cache: {e}")