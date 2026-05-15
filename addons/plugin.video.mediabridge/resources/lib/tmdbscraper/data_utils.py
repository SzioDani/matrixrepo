# -*- coding: utf-8 -*-

"""
Modulo di utilità per TMDb:
- pulizia testi
- normalizzazione titoli
- riconoscimento ID diretti (tmdb/123, tt1234567, tvdb/12345)
"""

from __future__ import absolute_import, unicode_literals

import re
import xbmc


def log(msg):
    xbmc.log("[TMDb data_utils] " + str(msg), xbmc.LOGINFO)


# ============================================================
#   PULIZIA TESTI
# ============================================================

def _clean_plot(text):
    """
    Pulisce la trama rimuovendo caratteri strani, doppi spazi,
    tag HTML e ritorni inutili.
    """
    if not text:
        return ""

    text = re.sub(r"<.*?>", "", text)          # rimuove HTML
    text = text.replace("\r", " ").replace("\n", " ")
    text = re.sub(r"\s+", " ", text).strip()   # normalizza spazi

    return text


def normalize_title(title):
    """
    Normalizza un titolo rimuovendo caratteri strani.
    """
    if not title:
        return ""

    title = title.strip()
    title = title.replace("–", "-").replace("—", "-")
    title = re.sub(r"\s+", " ", title)

    return title


# ============================================================
#   RICONOSCIMENTO ID DIRETTI
# ============================================================

TMDB_MOVIE_REGEX = re.compile(r"tmdb[/\- ]?movie[/\- ]?(\d+)", re.IGNORECASE)
TMDB_TV_REGEX    = re.compile(r"tmdb[/\- ]?tv[/\- ]?(\d+)", re.IGNORECASE)
TMDB_PERSON_REGEX = re.compile(r"tmdb[/\- ]?person[/\- ]?(\d+)", re.IGNORECASE)

IMDB_REGEX = re.compile(r"(tt\d{7,10})", re.IGNORECASE)
TVDB_REGEX = re.compile(r"tvdb[/\- ]?(\d+)", re.IGNORECASE)


def parse_media_id(query):
    """
    Riconosce ID diretti come:
    - tmdb/movie/123
    - tmdb/tv/456
    - tmdb/person/789
    - tt1234567 (IMDb)
    - tvdb/12345

    Ritorna:
        { "type": "...", "title": "ID" }
    oppure:
        None
    """

    if not query:
        return None

    q = query.strip()

    # TMDb Movie
    m = TMDB_MOVIE_REGEX.search(q)
    if m:
        return {"type": "tmdb_movie", "title": m.group(1)}

    # TMDb TV
    m = TMDB_TV_REGEX.search(q)
    if m:
        return {"type": "tmdb_tv", "title": m.group(1)}

    # TMDb Person
    m = TMDB_PERSON_REGEX.search(q)
    if m:
        return {"type": "tmdb_person", "title": m.group(1)}

    # IMDb
    m = IMDB_REGEX.search(q)
    if m:
        return {"type": "imdb", "title": m.group(1)}

    # TVDB
    m = TVDB_REGEX.search(q)
    if m:
        return {"type": "tvdb", "title": m.group(1)}

    return None