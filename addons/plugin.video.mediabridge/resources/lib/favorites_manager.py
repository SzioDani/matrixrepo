# -*- coding: utf-8 -*-
import xbmcgui
import xbmc
import xbmcvfs
import xbmcaddon # Fondamentale per Kodi 21
import os

# --- DEFINIZIONE PERCORSI KODI 21 (VERSIONE CORRETTA) 
ADDON_OBJ = xbmcaddon.Addon() 
# Ora usiamo l'oggetto per prendere il percorso
ADDON_PATH_RAW = ADDON_OBJ.getAddonInfo('path')
ADDON_PATH = xbmcvfs.translatePath(ADDON_PATH_RAW)

MEDIA_PATH = os.path.join(ADDON_PATH, "resources", "media")
ICON_STAR = os.path.join(MEDIA_PATH, "star_neon.png")

class FavoritesManager(xbmcgui.WindowXMLDialog):

    def __init__(self, *args, **kwargs):
        super(FavoritesManager, self).__init__(*args, **kwargs)
        self.items = kwargs.get("items", [])
        self.selected = set()
        self.result = ("close", None) 

    def onInit(self):
        """Popola la lista con icone e testi bianchi"""
        self.get_list = self.getControl(1000)
        self.get_list.reset()
        
        for fav in self.items:
            li = xbmcgui.ListItem(label=fav)
            # Imposta l'icona stella per l'XML
            li.setArt({'icon': ICON_STAR, 'thumb': ICON_STAR}) 
            # Colore bianco iniziale
            li.setLabel(f"[COLOR FFFFFFFF]{fav}[/COLOR]") 
            self.get_list.addItem(li)

        self.update_buttons()
        self.setFocus(self.get_list)

    def onClick(self, controlId):
        if controlId == 1000:
            index = self.get_list.getSelectedPosition()
            if index < 0: return

            if index in self.selected:
                self.selected.discard(index)
                # Torna Bianco
                self.get_list.getListItem(index).setLabel(f"[COLOR FFFFFFFF]{self.items[index]}[/COLOR]")
            else:
                self.selected.add(index)
                # Diventa Blù elettrico quando selezionato
                self.get_list.getListItem(index).setLabel(f"[COLOR FF00FFFF]{self.items[index]}[/COLOR]")

            self.update_buttons()

        elif controlId == 2000: # APRI
            if len(self.selected) == 1:
                idx = list(self.selected)[0]
                self.result = ("open", self.items[idx])
                self.close()

        elif controlId == 2001: # ELIMINA
            if self.selected:
                to_delete = [self.items[i] for i in self.selected]
                self.result = ("delete", to_delete)
                self.close()

        elif controlId == 2002: # SVUOTA TUTTO
            if xbmcgui.Dialog().yesno("[B][COLOR FFFF00FF]Conferma[/COLOR][/B]", "[COLOR FFFF0000]Vuoi Eliminare tutti i preferiti?[/COLOR]", yeslabel="Svuota", nolabel="Indietro"):
                self.result = ("clear", None)
                self.close()

        elif controlId == 2003: # CHIUDI
            self.result = ("close", None)
            self.close()

    def update_buttons(self):
        """Gestisce l'attivazione dei bottoni e i relativi colori (tramite XML)"""
        count = len(self.selected)
        # Il metodo setEnabled cambierà il colore in base al 'disabledcolor' dell'XML
        self.getControl(2000).setEnabled(count == 1)
        self.getControl(2001).setEnabled(count >= 1)
        self.getControl(2002).setEnabled(len(self.items) > 0)
        self.getControl(2003).setEnabled(True)

    def onAction(self, action):
        if action.getId() in [xbmcgui.ACTION_PREVIOUS_MENU, xbmcgui.ACTION_NAV_BACK]:
            self.result = ("close", None)
            self.close()
            