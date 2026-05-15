# -*- coding: utf-8 -*-
import xbmc, xbmcgui, xbmcplugin, xbmcaddon, xbmcvfs
import urllib.parse, os, re

from resources.lib.tmdb_bridge import TMDBBridge
from resources.lib.search_manager import SearchManager
from resources.lib.scrapers.manager import ScraperManager

TAG = "[MediaBridge][Nav]"
ADDON = xbmcaddon.Addon()
ADDON_PATH = xbmcvfs.translatePath(ADDON.getAddonInfo('path'))
PROFILE_PATH = xbmcvfs.translatePath(ADDON.getAddonInfo('profile'))
MEDIA_PATH = os.path.join(ADDON_PATH, "resources", "media")
ICON_MAIN = os.path.join(ADDON_PATH, "icon.png")
ICON_STAR = os.path.join(MEDIA_PATH, "star_neon.png")
ICON_TRASH = os.path.join(MEDIA_PATH, "trash_neon.png")

GENRES_MOVIE = [
    ("Azione", 28), ("Avventura", 12), ("Animazione", 16), ("Commedia", 35),
    ("Crime", 80), ("Dramma", 18), ("Fantasy", 14), ("Horror", 27),
    ("Musica", 10402), ("Mistero", 9648), ("Romance", 10749),
    ("Fantascienza", 878), ("Thriller", 53), ("Guerra", 10752), ("Western", 37),
]
GENRES_TV = [
    ("Azione e avventura", 10759), ("Animazione", 16), ("Commedia", 35),
    ("Crime", 80), ("Dramma", 18), ("Bambini", 10762), ("Mistero", 9648),
    ("Reality", 10764), ("Sci-Fi e Fantasy", 10765),
    ("War e politica", 10768), ("Western", 37),
]

def _log(msg, level=xbmc.LOGINFO):
    xbmc.log(f"{TAG} {msg}", level)

def notify(title, message, icon=None):
    xbmcgui.Dialog().notification(f"[COLOR FFFF00FF]{title}[/COLOR]", message, icon or ICON_MAIN, 4000)

def _safe_bool(key, default=False):
    try: return ADDON.getSettingBool(key)
    except: return ADDON.getSetting(key) == 'true'

def manage_list(filename, item=None, clear=False, remove_item=None, multiple_items=None):
    file_path = os.path.join(PROFILE_PATH, filename)
    if not xbmcvfs.exists(PROFILE_PATH):
        xbmcvfs.mkdir(PROFILE_PATH)
    items = []
    if xbmcvfs.exists(file_path):
        try:
            with xbmcvfs.File(file_path, 'r') as f:
                content = f.read()
                if content: items = [l.strip() for l in content.splitlines() if l.strip()]
        except: pass
    if clear:
        with xbmcvfs.File(file_path, 'w') as f: f.write("")
        return []
    if remove_item and remove_item in items: items.remove(remove_item)
    if item:
        item = item.replace('+', ' ').strip()
        if item:
            if item in items: items.remove(item)
            items.insert(0, item)
    if multiple_items:
        for m in reversed(multiple_items):
            m = m.strip()
            if m:
                if m in items: items.remove(m)
                items.insert(0, m)
    items = items[:50]
    if item or remove_item or clear or multiple_items:
        try:
            with xbmcvfs.File(file_path, 'w') as f: f.write("\n".join(items))
        except: pass
    return items


class Navigator:

    def __init__(self, handle):
        self.handle = handle
        self.bridge = TMDBBridge()
        self.scraper_manager = ScraperManager()
        self.dialog = xbmcgui.Dialog()

    # ── MENU PRINCIPALE ──────────────────────────────────────
    def show_main_menu(self):
        items = [
            ("[COLOR FFFF00FF]🔍 Cerca per Titolo[/COLOR]",      "action=search_title",   "search.png"),
            ("[COLOR FF00FFFF]🎭 Cerca per Genere[/COLOR]",      "action=browse_genre",   "genre.png"),
            ("[COLOR FFFFFF00]📅 Cerca per Anno[/COLOR]",        "action=browse_year",    "year.png"),
            ("[COLOR FF00FF00]🎬 Cerca Persona[/COLOR]",         "action=search_person",  "person.png"),
            ("[COLOR FFFF8000]📋 Da ClipboardText Plus[/COLOR]", "action=from_clipboard", "clipboard.png"),
            ("[COLOR FFAAAAFF]⭐ Preferiti[/COLOR]",             "action=favorites",      "star_neon.png"),
            ("[COLOR FFCCCCCC]🕐 Cronologia[/COLOR]",            "action=history",        "history.png"),
        ]
        for label, params, icon_name in items:
            url = f"plugin://plugin.video.mediabridge/?{params}"
            li = xbmcgui.ListItem(label=label)
            icon = os.path.join(MEDIA_PATH, icon_name)
            li.setArt({'icon': icon, 'thumb': icon})
            li.setProperty('IsPlayable', 'false')
            xbmcplugin.addDirectoryItem(self.handle, url, li, isFolder=True)
        xbmcplugin.endOfDirectory(self.handle)

    # ── RICERCA PER TITOLO ───────────────────────────────────
    def search_title(self, query=None):
        if not query:
            kb = xbmc.Keyboard('', '[COLOR FFFF00FF]Cerca Titolo[/COLOR]')
            kb.doModal()
            if not kb.isConfirmed(): return
            query = kb.getText().strip()
        if not query: return
        manage_list("history.txt", item=query)
        self._show_tmdb_results(query)

    # ── RICERCA PER GENERE ───────────────────────────────────
    def browse_genre(self, media_type=None):
        if not media_type:
            choice = self.dialog.select(
                "[COLOR FFFF00FF]Tipo contenuto[/COLOR]",
                ["[COLOR FF00FFFF]Film[/COLOR]", "[COLOR FFFFFF00]Serie TV[/COLOR]"]
            )
            if choice < 0: return
            media_type = "movie" if choice == 0 else "tv"
        genres = GENRES_MOVIE if media_type == "movie" else GENRES_TV
        choice = self.dialog.select(
            "[COLOR FFFF00FF]Scegli Genere[/COLOR]",
            [f"[COLOR FF00FFFF]{g[0]}[/COLOR]" for g in genres]
        )
        if choice < 0: return
        genre_name, genre_id = genres[choice]
        self._browse_discover(genre_id=genre_id, media_type=media_type, label=genre_name)

    # ── RICERCA PER ANNO ─────────────────────────────────────
    def browse_year(self):
        kb = xbmc.Keyboard('2024', '[COLOR FFFF00FF]Inserisci Anno (es. 2023)[/COLOR]')
        kb.doModal()
        if not kb.isConfirmed(): return
        year = kb.getText().strip()
        if not year.isdigit() or len(year) != 4:
            notify("Errore", "Anno non valido"); return
        choice = self.dialog.select(
            "[COLOR FFFF00FF]Tipo contenuto[/COLOR]",
            ["[COLOR FF00FFFF]Film[/COLOR]", "[COLOR FFFFFF00]Serie TV[/COLOR]"]
        )
        if choice < 0: return
        media_type = "movie" if choice == 0 else "tv"
        self._browse_discover(year=year, media_type=media_type, label=f"Anno {year}")

    # ── DISCOVER TMDB (genere/anno) ──────────────────────────
    def _browse_discover(self, genre_id=None, year=None, media_type="movie", label=""):
        try:
            import requests
            api_key = ADDON.getSetting("tmdb_api_key") or "af3a53eb387d57fc935e9128468b1899"
            lang = ADDON.getSetting("tmdb_lang_details") or "it-IT"
            endpoint = "movie" if media_type == "movie" else "tv"
            params = {"api_key": api_key, "language": lang, "sort_by": "popularity.desc", "page": 1}
            if genre_id: params["with_genres"] = genre_id
            if year:
                params["primary_release_year" if media_type == "movie" else "first_air_date_year"] = year
            resp = requests.get(f"https://api.themoviedb.org/3/discover/{endpoint}", params=params, timeout=10)
            raw = resp.json().get("results", [])
            if not raw:
                notify(label, "Nessun risultato trovato"); return

            # Costruisci lista per boost_collection
            items = []
            for item in raw:
                poster = item.get("poster_path")
                fanart = item.get("backdrop_path")
                t = item.get("title") or item.get("name") or "Sconosciuto"
                yr = (item.get("release_date") or item.get("first_air_date") or "")[:4]
                items.append({
                    "title": t, "year": yr,
                    "plot": item.get("overview") or "",
                    "rating": str(item.get("vote_average", 0))[:3],
                    "genre": "", "cast": "",
                    "poster": f"https://image.tmdb.org/t/p/w500{poster}" if poster else "",
                    "fanart": f"https://image.tmdb.org/t/p/original{fanart}" if fanart else "",
                    "tmdb_id": item.get("id"),
                    "media_type": media_type,
                    "seasons": "", "episodes": ""
                })

            # Boost parallelo genere/cast/rating
            if self.bridge.helper:
                items = self.bridge.helper.boost_collection(items)

            # Filtra per PRIMO genere: se il primo genere non corrisponde, escludi
            if genre_id:
                filtered_items = []
                for item in items:
                    genres_raw = item.get('genre', '')
                    if genres_raw:
                        first_genre = genres_raw.split(',')[0].strip()
                        # Controlla se il primo genere corrisponde cercando il nome
                        genre_name_match = next((g[0] for g in (GENRES_MOVIE + GENRES_TV) if g[1] == genre_id), '')
                        if genre_name_match.lower() in first_genre.lower() or first_genre.lower() in genre_name_match.lower():
                            filtered_items.append(item)
                        else:
                            filtered_items.append(item)  # Includi comunque ma con flag
                    else:
                        filtered_items.append(item)
                # Ordina: prima quelli con primo genere corrispondente
                def sort_key(item):
                    genres_raw = item.get('genre', '')
                    if not genres_raw: return 1
                    first = genres_raw.split(',')[0].strip()
                    gname = next((g[0] for g in (GENRES_MOVIE + GENRES_TV) if g[1] == genre_id), '')
                    return 0 if (gname.lower() in first.lower() or first.lower() in gname.lower()) else 1
                items = sorted(filtered_items, key=sort_key)

            # Filtra titoli non latini
            import unicodedata
            def is_latin(t):
                if not t: return False
                for ch in t:
                    n = unicodedata.name(ch, '')
                    if any(x in n for x in ['CJK','HIRAGANA','KATAKANA','HANGUL','ARABIC','HEBREW','THAI']): return False
                return True
            items = [i for i in items if is_latin(i.get('title', ''))]

            self._open_window(items, window_title=label)
        except Exception as e:
            _log(f"Errore discover: {e}", xbmc.LOGERROR)
            notify("Errore", str(e))

    # ── RICERCA PERSONA ──────────────────────────────────────
    def search_person(self, query=None):
        if not query:
            kb = xbmc.Keyboard('', '[COLOR FFFF00FF]Cerca Attore / Regista[/COLOR]')
            kb.doModal()
            if not kb.isConfirmed(): return
            query = kb.getText().strip()
        if not query: return
        self._show_tmdb_results(query)

    # ── DA CLIPBOARD ─────────────────────────────────────────
    def from_clipboard(self):
        paths = [
            xbmcvfs.translatePath("special://home/../Download/clipboard.txt"),
            "/storage/emulated/0/Download/clipboard.txt"
        ]
        raw_text = ""
        for p in paths:
            if xbmcvfs.exists(p):
                try:
                    with xbmcvfs.File(p, 'r') as f: content = f.read()
                    if content:
                        lines = [l.strip() for l in content.splitlines() if l.strip()]
                        if lines:
                            raw_text = lines[0]
                            if len(lines) > 1:
                                manage_list("history.txt", multiple_items=lines[1:])
                                notify("ClipboardText Plus", f"Aggiunti {len(lines)-1} titoli in cronologia")
                            if _safe_bool('clearafterread'):
                                with xbmcvfs.File(p, 'w') as fc: fc.write("")
                            break
                except: continue
        if not raw_text:
            notify("Clipboard", "Nessun testo trovato"); return
        manage_list("history.txt", item=raw_text)
        self._show_tmdb_results(raw_text)

    # ── PREFERITI / CRONOLOGIA ───────────────────────────────
    def show_favorites(self):
        items = manage_list("favorites.txt")
        if not items: notify("Preferiti", "Nessun preferito salvato"); return
        self._show_saved_list(items, "Preferiti")

    def show_history(self):
        items = manage_list("history.txt")
        if not items:
            notify("Cronologia", "Cronologia vuota"); return
        # Usa la finestra SearchManager intelligente
        win = SearchManager("SearchManager.xml", ADDON_PATH, items=items)
        win.doModal()
        try: azione, dati = win.result
        except: return
        del win
        if azione == "open":
            manage_list("history.txt", item=dati)
            self._show_tmdb_results(dati)
        elif azione == "go_to_favorites":
            self.show_favorites()
        elif azione == "delete":
            if dati:
                for x in dati: manage_list("history.txt", remove_item=x)
                notify("Cronologia", f"[COLOR FF00FFFF]{len(dati)} titolo/i eliminato/i[/COLOR]")
        elif azione == "clear":
            manage_list("history.txt", clear=True)
            notify("Cronologia", "[COLOR FF00FFFF]Cronologia svuotata![/COLOR]")

    def _show_saved_list(self, items, title):
        choice = self.dialog.select(
            f"[COLOR FFFF00FF]{title}[/COLOR]",
            [f"[COLOR FF00FFFF]{i}[/COLOR]" for i in items]
        )
        if choice < 0: return
        manage_list("history.txt", item=items[choice])
        self._show_tmdb_results(items[choice])

    # ── CUORE: ricerca TMDB ──────────────────────────────────
    def _show_tmdb_results(self, query):
        _log(f"Ricerca TMDB: '{query}'")
        results = self.bridge.search(query)
        if not results:
            notify("Ricerca", "Nessun risultato TMDB trovato"); return
        self._open_window(results)

    def _open_window(self, results, window_title="Cast:"):
        # Se tutti i risultati sono persone o c'è una sola persona, vai direttamente
        persons = [r for r in results if r.get('media_type') == 'person']
        if persons and len(persons) == len(results):
            # Solo persone - prendi la prima (più rilevante)
            _log(f"Solo persone ({len(persons)}), salto finestra scorrevole")
            self._handle_person(persons[0].get('tmdb_id'))
            return
        if len(results) == 1 and results[0].get('media_type') == 'person':
            _log(f"Persona singola, salto finestra scorrevole")
            self._handle_person(results[0].get('tmdb_id'))
            return

        from resources.lib.windows.tmdb_window import TMDBWindow
        win = TMDBWindow("TMDBWindow.xml", ADDON_PATH, "Default", "720p")
        win.setProperty("TitoloDinamico", window_title)
        win.set_items(results)
        win.doModal()
        tmdb_id, media_type = win.get_selected()
        del win

        if not tmdb_id: return

        _log(f"Selezionato: id={tmdb_id} type={media_type}")

        if media_type == "person":
            self._handle_person(tmdb_id)
        else:
            details = self.bridge.get_details(tmdb_id, media_type)
            title = details.get("title") or details.get("name") or ""
            if title: manage_list("history.txt", item=title)
            self._launch_scraper(title, tmdb_id, media_type, details)

    # ── LOGICA PERSONA (copia esatta dall'addon originale) ────
    def _handle_person(self, tmdb_id):
        _log(f"Persona id={tmdb_id}")
        lang = ADDON.getSetting("tmdb_lang_details") or "it-IT"

        # Dettagli persona con bio, poster, fanart e credits già inclusi
        p_data = self.bridge.get_details(tmdb_id, "person")
        raw_credits = p_data.get("credits", [])

        # ── FILTRO FERREO (come addon originale) ──
        filtered = []
        for c in raw_credits:
            char_name = (c.get('character') or "").lower()
            m_type = c.get("media_type")
            genre_ids = c.get("genre_ids", [])
            is_tv_junk = m_type == "tv" and any(gid in [99, 10767, 10764, 10763] for gid in genre_ids)
            is_voice = "voice" in char_name or "voce" in char_name
            is_minor = not char_name or any(x in char_name for x in ["uncredited", "self", "non accreditato"])
            if not (is_tv_junk or is_voice or is_minor):
                filtered.append(c)

        full_credits = sorted(filtered, key=lambda x: x.get('vote_count', 0), reverse=True)
        _log(f"Persona: {p_data.get('title')} | {len(full_credits)} titoli filtrati")

        # ── FINESTRA PERSONA FISSA ──
        # Una sola scheda con: poster, bio, genere (ruolo/luogo), rating, titoli di successo
        from resources.lib.windows.tmdb_window import TMDBWindow
        win = TMDBWindow("TMDBWindow.xml", ADDON_PATH, "Default", "720p")
        win.setProperty("TitoloDinamico", "Titoli di successo:")

        attore_item = {
            'title': p_data.get("title", ""),
            'year': p_data.get("year", ""),
            'plot': p_data.get("plot", "Bio non disponibile."),
            'genre': p_data.get("genre", ""),
            'rating': p_data.get("rating", ""),
            'cast': ", ".join([
                m.get("title") or m.get("name", "")
                for m in full_credits[:10]
                if m.get("title") or m.get("name")
            ]),
            'poster': p_data.get("poster", ""),
            'fanart': p_data.get("fanart", ""),
            'tmdb_id': str(tmdb_id),
            'media_type': 'person',
            'seasons': '', 'episodes': ''
        }

        win.set_items([attore_item])
        win.doModal()
        sel_id, sel_type = win.get_selected()
        del win

        # Premuto Post → carica direttamente filmografia senza dialogo intermedio
        if sel_id and sel_type == "person":
            self._load_filmografia(full_credits, p_data.get("title", ""))

    def _load_filmografia(self, full_credits, nome_persona):
        """Carica i 50 titoli più importanti con turbina parallela"""
        if not full_credits:
            notify(nome_persona, "Nessun titolo trovato"); return

        _log(f"Avvio filmografia per {nome_persona}: {len(full_credits[:70])} titoli")

        id_per_turbina = [
            {'id': m.get("id"), 'type': m.get("media_type"), 'base_data': m}
            for m in full_credits[:70]
        ]

        risultati_turbo = self.bridge.helper.boost_full_details(id_per_turbina)

        filmografia = []
        for m in risultati_turbo:
            voto = str(m.get('rating', '0'))
            filmografia.append({
                "title": m.get("title") or m.get("name") or "Titolo Sconosciuto",
                "tmdb_id": m.get("tmdb_id"),
                "media_type": m.get("media_type"),
                "poster": m.get("poster", ""),
                "fanart": m.get("fanart", ""),
                "plot": m.get("plot", ""),
                "year": m.get("year", ""),
                "rating": f"★ {voto[:3]}",
                "cast": m.get("cast", ""),
                "genre": m.get("genre", ""),
                "seasons": str(m.get("seasons", "")),
                "episodes": str(m.get("episodes", ""))
            })

        _log(f"Filmografia pronta: {len(filmografia)} titoli")
        self._open_window(filmografia, window_title="Cast:")

    # ── SCRAPER E PLAYER ─────────────────────────────────────
    def _launch_scraper(self, title, tmdb_id, media_type, details):
        if not self.scraper_manager.get_scraper_names():
            notify("MediaBridge", "Nessuno scraper configurato"); return

        imdb_id = details.get('imdb_id') or ''
        _log(f"Lancio scraper: '{title}' | IMDB: {imdb_id}")
        notify("MediaBridge", f"[COLOR FF00FFFF]Cerco:[/COLOR] {title}")
        results = self.scraper_manager.search_all(title, imdb_id=imdb_id)

        if not results:
            notify("MediaBridge", "Nessun risultato trovato nei siti"); return

        labels = [
            f"[COLOR FFFF00FF]{r.get('_site','?')}[/COLOR] - [COLOR FF00FFFF]{r.get('title','')}[/COLOR] {r.get('year','')}"
            for r in results
        ]
        choice = self.dialog.select(f"[COLOR FFFF00FF]Risultati: {title}[/COLOR]", labels)
        if choice < 0: return

        links = self.scraper_manager.get_links_all(results[choice].get('url',''), site_name=results[choice].get('_site'))
        if not links:
            notify("MediaBridge", "Nessun link stream trovato"); return

        # Mostra menu server - torna al menu se il video non parte
        while True:
            link_labels = []
            for lk in links:
                label = lk.get('label', 'Server')
                quality = lk.get('quality', '')
                lang = lk.get('lang', '')
                q_color = '[COLOR FF00FF00]' if '1080' in quality else '[COLOR FFFFFF00]' if '720' in quality else '[COLOR FFAAAAAA]'
                link_labels.append(
                    f"[COLOR FF00FFFF]{label}[/COLOR] {q_color}{quality}[/COLOR] {lang}".strip()
                )

            link_choice = self.dialog.select(
                f"[COLOR FFFF00FF]🎬 {title}[/COLOR]  [COLOR FFAAAAAA]— Scegli server[/COLOR]",
                link_labels
            )
            if link_choice < 0: return

            stream_url = links[link_choice].get('url', '')
            label_scelto = links[link_choice].get('label', 'Server')
            
            notify("MediaBridge", f"[COLOR FF00FFFF]Risolvo {label_scelto}...[/COLOR]")
            resolved = self.scraper_manager.resolve_with_resolveurl(stream_url)
            
            if resolved and resolved != stream_url:
                _log(f"Riproduzione: {label_scelto} → {resolved[:80]}")
                self._play(resolved, title, details)
            elif resolved == stream_url:
                # URL non risolto - prova a riprodurre direttamente
                _log(f"Riproduzione diretta: {label_scelto}")
                self._play(resolved, title, details)
            else:
                notify("MediaBridge", f"[COLOR FFFF0000]{label_scelto}: nessun link trovato[/COLOR]")
                continue

            # Dopo tentativo chiedi se riprovare con altro server
            retry = self.dialog.yesno(
                f"[COLOR FFFF00FF]{title}[/COLOR]",
                "[COLOR FF00FFFF]Il video e' partito con " + label_scelto + "?[/COLOR]"

                + "[COLOR FFAAAAAA] - NO = altro server[/COLOR]"
            )
            if retry: return  # Video partito, esci

    def _play(self, url, title, details):
        import urllib.parse

        # Parsa headers embedded nel URL (formato: url|Header=value&Header2=value2)
        play_url = url
        headers = {}
        if '|' in url:
            parts = url.split('|', 1)
            play_url = parts[0]
            for pair in parts[1].split('&'):
                if '=' in pair:
                    k, v = pair.split('=', 1)
                    headers[k] = urllib.parse.unquote_plus(v)
            _log(f"Play: {play_url[:80]} | headers: {list(headers.keys())}")

        # Costruisci URL con headers nel formato nativo Kodi (url|Header=value)
        if headers:
            encoded = '&'.join([f"{k}={urllib.parse.quote_plus(v)}" for k, v in headers.items()])
            kodi_url = f"{play_url}|{encoded}"
        else:
            kodi_url = play_url

        _log(f"Avvio player con: {kodi_url[:120]}")

        li = xbmcgui.ListItem(label=title, path=kodi_url)
        li.setProperty('IsPlayable', 'true')
        li.setProperty('inputstream.adaptive.manifest_type', 'm3u8' if '.m3u8' in play_url else '')

        # Headers come property
        if headers:
            ua = headers.get('User-Agent', '')
            ref = headers.get('Referer', '')
            org = headers.get('Origin', '')
            if ua: li.setProperty('User-Agent', ua)
            if ref: li.setProperty('Referer', ref)
            if org: li.setProperty('Origin', org)

        try:
            tag = li.getVideoInfoTag()
            tag.setTitle(title)
            tag.setPlot(details.get('plot', ''))
            tag.setGenres([details.get('genre', '')])
            try: tag.setYear(int(details.get('year', 0) or 0))
            except: pass
        except Exception:
            li.setInfo('video', {
                'title': title, 'plot': details.get('plot', ''),
                'year': int(details.get('year', 0) or 0),
                'genre': details.get('genre', ''),
            })

        li.setArt({
            'thumb': details.get('poster', ''),
            'fanart': details.get('fanart', ''),
            'poster': details.get('poster', ''),
        })

        # Usa xbmc.Player().play() invece di setResolvedUrl
        # per garantire la riproduzione in tutti i contesti
        xbmcplugin.setResolvedUrl(self.handle, True, li)
        xbmc.Player().play(kodi_url, li)
