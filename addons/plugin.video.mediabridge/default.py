# -*- coding: utf-8 -*-
"""
MediaBridge - Entry Point
plugin://plugin.video.mediabridge/
"""

import sys
import urllib.parse
import xbmcplugin
import xbmc

from resources.lib.navigator import Navigator

HANDLE = int(sys.argv[1]) if len(sys.argv) > 1 else -1


def main():
    # Parsing parametri URL
    args = {}
    if len(sys.argv) > 2:
        query_string = sys.argv[2].lstrip('?')
        args = dict(urllib.parse.parse_qsl(query_string))

    action = args.get('action', 'main_menu')
    xbmc.log(f"[MediaBridge] Azione: {action} | Params: {args}", xbmc.LOGINFO)

    nav = Navigator(HANDLE)

    if action == 'main_menu':
        nav.show_main_menu()

    elif action == 'search_title':
        query = args.get('query', '')
        nav.search_title(query=query or None)

    elif action == 'search_person':
        query = args.get('query', '')
        nav.search_person(query=query or None)

    elif action == 'browse_genre':
        media_type = args.get('media_type', None)
        nav.browse_genre(media_type=media_type)

    elif action == 'browse_year':
        nav.browse_year()

    elif action == 'from_clipboard':
        nav.from_clipboard()

    elif action == 'favorites':
        nav.show_favorites()

    elif action == 'history':
        nav.show_history()

    else:
        xbmc.log(f"[MediaBridge] Azione sconosciuta: {action}", xbmc.LOGWARNING)
        nav.show_main_menu()


if __name__ == '__main__':
    main()
