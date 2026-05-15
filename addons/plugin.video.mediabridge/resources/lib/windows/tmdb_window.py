# -*- coding: utf-8 -*-
import xbmcgui
import xbmc

class TMDBWindow(xbmcgui.WindowXMLDialog):

    def __init__(self, *args, **kwargs):
        super(TMDBWindow, self).__init__(*args, **kwargs)
        self.items = []
        self.selected_tmdb_id = None
        self.selected_media_type = None

    def set_items(self, results):
        self.items = results or []

    def onInit(self):
        try:
            panel = self.getControl(1000)
        except:
            xbmc.log("[TMDBWindow] ERRORE: Control 1000 non trovato", xbmc.LOGERROR)
            return

        panel.reset()

        for r in self.items:
            title = r.get("title", "")
            li = xbmcgui.ListItem(label=title)

            # --- SISTEMAZIONE IMMAGINI ---
            poster = r.get("poster") or ""
            # Prendiamo 'fanart' che è il nome che abbiamo usato nel Bridge
            fanart = r.get("fanart") or "" 

            li.setArt({
                "poster": poster,
                "thumb": poster,
                "fanart": fanart
            })

            # PROPRIETÀ PER L'XML
            li.setProperty("thumbnail", poster)
            li.setProperty("fanart", fanart) # <--- FONDAMENTALE per lo sfondo
            li.setProperty("plot", r.get("plot") or "Nessuna trama disponibile.")
            li.setProperty("year", str(r.get("year") or ""))
            li.setProperty("rating", str(r.get("rating") or "0.0"))
            li.setProperty("cast", r.get("cast") or "")
            li.setProperty("genre", r.get("genre") or "")
            li.setProperty("media_type", r.get("media_type") or "")
            li.setProperty("tmdb_id", str(r.get("tmdb_id") or ""))

            # --- INFO SERIE TV / FILM ---
            # Usiamo stringhe pulite senza simboli speciali che possono bloccare il font
            runtime = str(r.get("runtime") or "")
            li.setProperty("runtime", runtime if runtime else "")

            seasons = str(r.get("seasons") or "")
            li.setProperty("seasons", seasons if (seasons and seasons != "0") else "")

            episodes = str(r.get("episodes") or "")
            li.setProperty("episodes", episodes if (episodes and episodes != "0") else "")

            panel.addItem(li)

        if panel.size() > 0:
            try:
                self.setFocusId(1000)
            except:
                pass

    def onClick(self, controlId):
        if controlId == 1000:
            try:
                panel = self.getControl(1000)
                li = panel.getSelectedItem()
                if li:
                    self.selected_tmdb_id = li.getProperty("tmdb_id")
                    self.selected_media_type = li.getProperty("media_type")
            except:
                pass
            self.close()

    def get_selected(self):
        return self.selected_tmdb_id, self.selected_media_type
        