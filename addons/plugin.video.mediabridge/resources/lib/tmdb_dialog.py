# -*- coding: utf-8 -*-
import xbmc, xbmcgui, xbmcaddon, xbmcvfs
import requests
import urllib.parse
import os

ADDON = xbmcaddon.Addon()
ADDON_PATH = xbmcvfs.translatePath(ADDON.getAddonInfo('path'))

API_KEY = ADDON.getSetting("tmdb_api_key")
TMDB_SEARCH_URL = "https://api.themoviedb.org/3/search/multi?api_key={}&query={}"

# ============================================================
#   FINESTRA TMDb PERSONALIZZATA
# ============================================================
class TMDBWindow(xbmcgui.WindowXML):
    def __init__(self, *args, **kwargs):
        self.results = kwargs.get("results", [])
        self.selected = None

    def onInit(self):
        xbmc.log("[TMDB DEBUG] Finestra TMDb inizializzata", xbmc.LOGINFO)

        self.list_control = self.getControl(1000)

        for item in self.results:
            li = xbmcgui.ListItem(label=item["title"])
            li.setArt({
                "thumb": item["poster"],
                "icon": item["poster"],
                "poster": item["poster"]
            })
            self.list_control.addItem(li)

    def onClick(self, controlId):
        if controlId == 1000:
            index = self.list_control.getSelectedPosition()
            self.selected = self.results[index]["title"]
            xbmc.log(f"[TMDB DEBUG] Titolo selezionato: {self.selected}", xbmc.LOGINFO)
            self.close()

# ============================================================
#   FUNZIONE PRINCIPALE TMDb
# ============================================================
def tmdb_search_and_select(query):

    xbmc.log(f"[TMDB DEBUG] Query ricevuta: {query}", xbmc.LOGINFO)

    # Query vuota → non fare nulla
    if not query or query.strip() == "":
        xbmc.log("[TMDB DEBUG] Query vuota, esco", xbmc.LOGINFO)
        return None

    # API key mancante
    if not API_KEY:
        xbmc.log("[TMDB DEBUG] API KEY mancante", xbmc.LOGINFO)
        return None

    # Costruzione URL
    url = TMDB_SEARCH_URL.format(API_KEY, urllib.parse.quote(query))
    xbmc.log(f"[TMDB DEBUG] URL richiesta: {url}", xbmc.LOGINFO)

    # Richiesta TMDb
    try:
        r = requests.get(url)
        data = r.json()
        xbmc.log(f"[TMDB DEBUG] Risposta TMDb: {data}", xbmc.LOGINFO)
    except Exception as e:
        xbmc.log(f"[TMDB DEBUG] Errore richiesta TMDb: {e}", xbmc.LOGINFO)
        return None

    # Parsing risultati
    results = []
    for item in data.get("results", []):
        title = item.get("title") or item.get("name")
        poster = item.get("poster_path")

        if not title:
            continue

        results.append({
            "title": title,
            "poster": f"https://image.tmdb.org/t/p/w500{poster}" if poster else ""
        })

    xbmc.log(f"[TMDB DEBUG] Risultati trovati: {len(results)}", xbmc.LOGINFO)

    # Nessun risultato
    if not results:
        xbmc.log("[TMDB DEBUG] Nessun risultato TMDb", xbmc.LOGINFO)
        return None

    # Un solo risultato → ritorna direttamente
    if len(results) == 1:
        xbmc.log(f"[TMDB DEBUG] Unico risultato: {results[0]['title']}", xbmc.LOGINFO)
        return results[0]["title"]

    # Più risultati → apri finestra
    xbmc.log("[TMDB DEBUG] Apro finestra TMDb", xbmc.LOGINFO)

    win = TMDBWindow("TMDBWindow.xml", ADDON_PATH, "default", results=results)
    win.doModal()
    selected = win.selected
    del win

    xbmc.log(f"[TMDB DEBUG] Selezionato dalla finestra: {selected}", xbmc.LOGINFO)

    return selected