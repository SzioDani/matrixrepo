# -*- coding: utf-8 -*-
import xbmc, xbmcaddon, xbmcvfs, os

def main():
    addon = xbmcaddon.Addon()
    profile_path = xbmcvfs.translatePath(addon.getAddonInfo('profile'))

    if not xbmcvfs.exists(profile_path):
        xbmcvfs.mkdir(profile_path)

    for filename in ["history.txt", "favorites.txt"]:
        file_path = os.path.join(profile_path, filename)
        if not xbmcvfs.exists(file_path):
            with xbmcvfs.File(file_path, 'w') as f:
                f.write("")

    addon.setSetting("tmdb_lang_details", "it-IT")
    addon.setSetting("tmdb_cert_country", "US")
    xbmc.log("[MediaBridge] Servizio avviato correttamente", xbmc.LOGINFO)

if __name__ == "__main__":
    main()
