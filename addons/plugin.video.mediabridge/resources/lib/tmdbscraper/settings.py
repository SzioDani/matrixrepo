# -*- coding: utf-8 -*-

"""
Valori di default per gli scraper TMDb.
Questi valori vengono combinati con quelli scelti dall'utente
nel settings.xml tramite tmdb_settings_reader.py.
"""

from __future__ import absolute_import, unicode_literals


def getSourceSettings():
    """
    Restituisce un dizionario con i valori di default TMDb.
    L'utente può sovrascriverli tramite settings.xml.
    """

    settings = {
        # -------------------------------------------------------
        # LINGUE
        # -------------------------------------------------------
        "LANG_DETAILS": "it-IT",   # Lingua predefinita per trame e titoli
        "LANG_IMAGES": "it",       # Lingua preferita per poster/fanart

        # -------------------------------------------------------
        # CERTIFICAZIONI
        # -------------------------------------------------------
        "CERT_COUNTRY": "IT",      # Paese certificazione
        "CERT_PREFIX": "",         # Prefisso certificazione (non usato)

        # -------------------------------------------------------
        # TRAILER
        # -------------------------------------------------------
        "ENABTRAILER": True,       # Trailer abilitati di default

        # -------------------------------------------------------
        # FANART.TV
        # -------------------------------------------------------
        "FANARTTV_ENABLE": False,  # Artwork avanzati disabilitati
        "FANARTTV_CLIENTKEY": "",  # Nessuna API key di default

        # -------------------------------------------------------
        # OPZIONI EXTRA
        # -------------------------------------------------------
        "SAVETAGS": False,         # Non salva tag TMDb
        "STUDIOCOUNTRY": "IT",     # Paese studio preferito
        "CATLANDSCAPE": True,      # Usa landscape se disponibile
        "CATKEYART": False,        # Keyart disabilitato

        # -------------------------------------------------------
        # LOG
        # -------------------------------------------------------
        "VERBOSELOG": False,       # Log dettagliati disattivati
    }

    return settings