# -*- coding: utf-8 -*-
import xbmc
from xbmcaddon import Addon
from resources.lib.tmdbscraper import settings as tmdb_default_settings

TAG = "[MediaBridge][SettingsReader]"

def _safe_bool(addon, key, default=False):
    """Legge un bool in modo sicuro su qualsiasi piattaforma Kodi/Android"""
    try:
        return addon.getSettingBool(key)
    except Exception:
        val = addon.getSetting(key)
        if val == '': return default
        return val.lower() in ('true', '1', 'yes')

def get_tmdb_settings():
    xbmc.log(f"{TAG} Lettura impostazioni TMDB", xbmc.LOGDEBUG)
    addon = Addon()
    try:
        defaults = tmdb_default_settings.getSourceSettings()
    except Exception as e:
        xbmc.log(f"{TAG} Errore lettura defaults: {e}", xbmc.LOGWARNING)
        defaults = {}

    lang_details  = addon.getSetting("tmdb_lang_details")  or defaults.get("LANG_DETAILS")  or "it-IT"
    lang_images   = addon.getSetting("tmdb_lang_images")   or defaults.get("LANG_IMAGES")   or "it"
    cert_country  = addon.getSetting("tmdb_cert_country")  or defaults.get("CERT_COUNTRY")  or "IT"

    result = {
        "LANG_DETAILS":       lang_details,
        "LANG_IMAGES":        lang_images,
        "SEARCH_LANG":        lang_details,
        "CERT_COUNTRY":       cert_country,
        "CERT_PREFIX":        defaults.get("CERT_PREFIX"),
        "ENABTRAILER":        _safe_bool(addon, "tmdb_enable_trailer",  default=True),
        "FANARTTV_ENABLE":    _safe_bool(addon, "tmdb_fanarttv_enable", default=False),
        "FANARTTV_CLIENTKEY": addon.getSetting("tmdb_fanarttv_key") or defaults.get("FANARTTV_CLIENTKEY"),
        "SAVETAGS":           defaults.get("SAVETAGS"),
        "STUDIOCOUNTRY":      defaults.get("STUDIOCOUNTRY"),
        "CATLANDSCAPE":       defaults.get("CATLANDSCAPE"),
        "CATKEYART":          defaults.get("CATKEYART"),
        "VERBOSELOG":         defaults.get("VERBOSELOG"),
        "RATING_TYPES":       ["tmdb"],
    }
    xbmc.log(f"{TAG} Settings OK: lang={lang_details} cert={cert_country}", xbmc.LOGDEBUG)
    return result
