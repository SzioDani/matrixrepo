# -*- coding: utf-8 -*-

"""
Modulo API minimalista per TMDb.
Compatibile con:
- tmdb_utils.py
- tmdb_settings_reader.py
- scraper TMDb originali

Funzione principale:
    load_info(url, params=None, verboselog=False)
"""

from __future__ import absolute_import, unicode_literals

import json
import urllib.parse
import urllib.request
import urllib.error
import xbmc


def log(msg):
    xbmc.log("[TMDb API] " + str(msg), xbmc.LOGINFO)


def build_url(base_url, params):
    """
    Costruisce un URL completo con parametri GET.
    """
    if not params:
        return base_url

    query = urllib.parse.urlencode(params)
    return f"{base_url}?{query}"


def load_info(url, params=None, verboselog=False):
    """
    Esegue una richiesta HTTP verso TMDb e ritorna un dict JSON.

    Ritorna:
        - dict con i dati TMDb
        - None in caso di errore
    """

    full_url = build_url(url, params)

    if verboselog:
        log("Richiesta: " + full_url)

    try:
        req = urllib.request.Request(
            full_url,
            headers={
                "User-Agent": "Mozilla/5.0 (Kodi TMDb Scraper)",
                "Accept": "application/json"
            }
        )

        with urllib.request.urlopen(req, timeout=6) as response:
            data = response.read().decode("utf-8")
            return json.loads(data)

    except urllib.error.HTTPError as e:
        log(f"HTTPError: {e.code} - {e.reason}")
    except urllib.error.URLError as e:
        log(f"URLError: {e.reason}")
    except Exception as e:
        log(f"Errore generico: {e}")

    return None