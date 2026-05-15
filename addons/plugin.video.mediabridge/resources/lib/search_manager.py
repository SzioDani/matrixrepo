# -*- coding: utf-8 -*-
import xbmcgui, xbmc, xbmcvfs, xbmcaddon, os

ADDON_OBJ = xbmcaddon.Addon()
ADDON_PATH = xbmcvfs.translatePath(ADDON_OBJ.getAddonInfo('path'))
MEDIA_PATH = os.path.join(ADDON_PATH, "resources", "media")
ICON_SEARCH = os.path.join(MEDIA_PATH, "search_neon.png")

class SearchManager(xbmcgui.WindowXMLDialog):

    def __init__(self, *args, **kwargs):
        super(SearchManager, self).__init__(*args, **kwargs)
        self.items = kwargs.get("items", [])
        self.selected = set()
        self.result = ("close", None)

    def onInit(self):
        try:
            self.get_list = self.getControl(1000)
            self.get_list.reset()
            for res in self.items:
                li = xbmcgui.ListItem(label=res)
                li.setArt({'icon': ICON_SEARCH, 'thumb': ICON_SEARCH})
                li.setLabel(f"[COLOR FFFFFFFF]{res}[/COLOR]")
                self.get_list.addItem(li)
            self.update_buttons()
            self.setFocus(self.get_list)
        except: pass

    def onClick(self, controlId):
        if controlId == 1000:
            index = self.get_list.getSelectedPosition()
            if index < 0: return
            if index in self.selected:
                self.selected.discard(index)
                self.get_list.getListItem(index).setLabel(f"[COLOR FFFFFFFF]{self.items[index]}[/COLOR]")
            else:
                self.selected.add(index)
                self.get_list.getListItem(index).setLabel(f"[COLOR FF00FFFF]{self.items[index]}[/COLOR]")
            self.update_buttons()
        elif controlId == 2000:
            if len(self.selected) == 1:
                idx = list(self.selected)[0]
                self.result = ("open", self.items[idx])
                self.close()
        elif controlId == 2001:
            self.result = ("go_to_favorites", None)
            self.close()
        elif controlId == 2002:
            if self.selected:
                to_delete = [self.items[i] for i in self.selected]
                self.result = ("delete", to_delete)
                self.close()
        elif controlId == 2003:
            if xbmcgui.Dialog().yesno("[B][COLOR FFFF00FF]Conferma[/COLOR][/B]",
                                      "[COLOR FFFF0000]Vuoi eliminare tutta la cronologia?[/COLOR]"):
                self.result = ("clear", None)
                self.close()
        elif controlId == 2004:
            self.result = ("close", None)
            self.close()

    def update_buttons(self):
        try:
            count = len(self.selected)
            for cid, enabled in [(2000, count == 1), (2001, True),
                                  (2002, count >= 1), (2003, len(self.items) > 0), (2004, True)]:
                ctrl = self.getControl(cid)
                if ctrl: ctrl.setEnabled(enabled)
        except: pass

    def onAction(self, action):
        if action.getId() in [xbmcgui.ACTION_PREVIOUS_MENU, xbmcgui.ACTION_NAV_BACK]:
            self.result = ("close", None)
            self.close()
