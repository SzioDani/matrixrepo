# -*- coding: utf-8 -*-
"""
MediaBridge - Scraper TantiFilm
Dominio: tanti-film.homes (aggiornato maggio 2026)
Strategia: costruzione URL diretta + ricerca via motore esterno
"""

import re
import urllib.parse
import xbmc
from resources.lib.scrapers.base_scraper import BaseScraper

TAG = "[MediaBridge][TantiFilm]"

SKIP_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg',
                   '.css', '.js', '.ico', '.woff', '.ttf', '.xml', '.dtd']

SKIP_DOMAINS = ['google', 'facebook', 'twitter', 'youtube', 'googleapis',
                'gstatic', 'w3.org', 'opensearch', 'gravatar',
                'streaming-community', 'guarda-serie', 'altadefinizione', 'eurostreaming']


class TantiFilmScraper(BaseScraper):

    SITE_NAME = "TantiFilm"
    BASE_URL = "https://tanti-film.homes"

    def search_url(self, query):
        # Usa il motore di ricerca interno del sito
        q = urllib.parse.quote_plus(query)
        url = f"{self.BASE_URL}/index.php?do=search&subaction=search&story={q}"
        xbmc.log(f"{TAG} URL ricerca: {url}", xbmc.LOGINFO)
        return url

    def search(self, query):
        """Override: prova più strategie per trovare i film"""
        xbmc.log(f"{TAG} Ricerca: '{query}'", xbmc.LOGINFO)
        results = []

        # Strategia 1: URL diretta costruita dal titolo
        results = self._try_direct_url(query)
        if results:
            xbmc.log(f"{TAG} Trovato via URL diretta: {len(results)}", xbmc.LOGINFO)
            return results

        # Strategia 2: Ricerca via motore interno (POST)
        results = self._try_search_post(query)
        if results:
            xbmc.log(f"{TAG} Trovato via POST: {len(results)}", xbmc.LOGINFO)
            return results

        # Strategia 3: Ricerca via GET con ?s=
        results = self._try_search_get(query)
        xbmc.log(f"{TAG} Trovato via GET: {len(results)}", xbmc.LOGINFO)
        return results

    def _slug_from_title(self, title):
        """Converte titolo in slug URL"""
        slug = title.lower()
        # Rimuovi caratteri speciali
        slug = re.sub(r"[àáâãäå]", "a", slug)
        slug = re.sub(r"[èéêë]", "e", slug)
        slug = re.sub(r"[ìíîï]", "i", slug)
        slug = re.sub(r"[òóôõö]", "o", slug)
        slug = re.sub(r"[ùúûü]", "u", slug)
        slug = re.sub(r"[^a-z0-9\s-]", "", slug)
        slug = re.sub(r'\s+', '-', slug.strip())
        slug = re.sub(r'-+', '-', slug)
        return slug

    def _try_direct_url(self, query):
        """Prova a costruire l'URL direttamente dal titolo"""
        results = []
        slug = self._slug_from_title(query)
        
        # Pattern URL TantiFilm: /guarda/ID-titolo-streaming-hd.html
        # Proviamo con il cerca interno che restituisce la pagina diretta
        search_url = f"{self.BASE_URL}/?s={urllib.parse.quote_plus(query)}"
        xbmc.log(f"{TAG} Provo URL diretta: {search_url}", xbmc.LOGINFO)
        
        html = self.fetch_clean(search_url)
        if not html:
            return results

        xbmc.log(f"{TAG} HTML ricevuto: {len(html)} chars", xbmc.LOGINFO)

        # Controlla se siamo stati reindirizzati alla pagina del film
        og_url = re.search(r'og:url[^>]+content=["\']([^"\']+/guarda/[^"\']+)["\']', html, re.IGNORECASE)
        if og_url:
            film_url = og_url.group(1)
            og_title = re.search(r'og:title[^>]+content=["\']([^"\']+)["\']', html, re.IGNORECASE)
            title = og_title.group(1) if og_title else query
            year = self.extract_year(html) or self.extract_year(film_url)
            xbmc.log(f"{TAG} Reindirizzato a film: '{title}' -> {film_url}", xbmc.LOGINFO)
            results.append({'title': title, 'url': film_url, 'year': year, 'poster': '', 'type': 'movie'})
            return results

        # Cerca link /guarda/ nell'HTML
        guarda_links = re.findall(r'href=["\']([^"\']*guarda/[^"\']+)["\']', html, re.IGNORECASE)
        xbmc.log(f"{TAG} Link /guarda/ trovati: {len(guarda_links)}", xbmc.LOGINFO)
        
        seen = set()
        for href in guarda_links:
            if any(ext in href for ext in SKIP_EXTENSIONS): continue
            if href.startswith('//'): href = 'https:' + href
            elif href.startswith('/'): href = self.BASE_URL + href
            if not href.startswith('http') or href in seen: continue
            seen.add(href)
            slug_found = href.rstrip('/').split('/')[-1]
            slug_found = re.sub(r'\.html?$', '', slug_found)
            slug_found = re.sub(r'^\d+-', '', slug_found)
            slug_found = re.sub(r'-(hd|streaming|parte-\d+|streaming-hd).*$', '', slug_found)
            title = slug_found.replace('-', ' ').strip().title()
            year = self.extract_year(href)
            xbmc.log(f"{TAG}   -> '{title}' | {href}", xbmc.LOGINFO)
            results.append({'title': title, 'url': href, 'year': year, 'poster': '', 'type': 'movie'})

        return results

    def _try_search_post(self, query):
        """Ricerca via POST form (motore DLE)"""
        results = []
        try:
            import requests
            from resources.lib.cloudflare.bypass import HEADERS_CHROME
            
            search_url = f"{self.BASE_URL}/index.php?do=search"
            data = {
                'do': 'search',
                'subaction': 'search',
                'story': query,
                'search_start': '0',
                'full_search': '0',
                'result_from': '1',
            }
            h = dict(HEADERS_CHROME)
            h['Content-Type'] = 'application/x-www-form-urlencoded'
            h['Referer'] = self.BASE_URL
            
            resp = requests.post(search_url, data=data, headers=h, timeout=(10, 30))
            xbmc.log(f"{TAG} POST status: {resp.status_code}", xbmc.LOGINFO)
            
            if resp.status_code == 200:
                html = self.clean_html(resp.text)
                guarda_links = re.findall(r'href=["\']([^"\']*guarda/[^"\']+)["\']', html, re.IGNORECASE)
                xbmc.log(f"{TAG} POST /guarda/ trovati: {len(guarda_links)}", xbmc.LOGINFO)
                
                seen = set()
                for href in guarda_links:
                    if any(ext in href for ext in SKIP_EXTENSIONS): continue
                    if href.startswith('/'): href = self.BASE_URL + href
                    if href in seen: continue
                    seen.add(href)
                    slug = href.rstrip('/').split('/')[-1]
                    slug = re.sub(r'\.html?$', '', slug)
                    slug = re.sub(r'^\d+-', '', slug)
                    title = slug.replace('-', ' ').strip().title()
                    results.append({'title': title, 'url': href, 'year': self.extract_year(href), 'poster': '', 'type': 'movie'})
        except Exception as e:
            xbmc.log(f"{TAG} POST errore: {e}", xbmc.LOGERROR)
        return results

    def _try_search_get(self, query):
        """Fallback: ricerca GET"""
        results = []
        url = f"{self.BASE_URL}/?s={urllib.parse.quote_plus(query)}"
        html = self.fetch_clean(url)
        if not html:
            return results
        
        # Cerca QUALSIASI link interno che assomigli a un film
        all_links = re.findall(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>([^<]{2,60})</a>', html, re.IGNORECASE)
        skip = ['home', 'menu', 'cerca', 'login', 'cookie', 'privacy', 'streaming', 'serie tv', 'film', 'page', 'aggior']
        seen = set()
        for href, text in all_links:
            text = self.clean_title(text)
            if not text or len(text) < 2: continue
            if any(x in text.lower() for x in skip): continue
            if any(dom in href.lower() for dom in SKIP_DOMAINS): continue
            if href.startswith('/'): href = self.BASE_URL + href
            if not href.startswith('http'): continue
            if 'tanti-film' not in href.lower(): continue
            if href in seen or href.rstrip('/') == self.BASE_URL.rstrip('/'): continue
            seen.add(href)
            results.append({'title': text, 'url': href, 'year': self.extract_year(href), 'poster': '', 'type': 'movie'})
        
        xbmc.log(f"{TAG} GET risultati: {len(results)}", xbmc.LOGINFO)
        return results

    # parse_results non usato (override di search) ma richiesto dalla base
    def parse_results(self, html, query=None):
        return []

    def get_stream_links(self, url):
        xbmc.log(f"{TAG} get_stream_links: {url}", xbmc.LOGINFO)
        links = []
        html = self.fetch_clean(url, prefer_flare=True)
        if not html:
            xbmc.log(f"{TAG} Pagina non scaricata", xbmc.LOGERROR)
            return links

        xbmc.log(f"{TAG} Pagina: {len(html)} chars", xbmc.LOGINFO)

        SERVER_LABELS = {
            'server1': 'SERVER 1', 'superhd': 'SuperHD', 'drophd': 'DropHD',
            'server4k': 'SERVER 4K', 'supervideo': 'SuperVideo',
            'dropload': 'Dropload', 'mixdrop': 'MixDrop', 'streamhg': 'StreamHG',
            'streamtape': 'StreamTape', 'doodstream': 'DoodStream', 'voe': 'VOE',
        }

        def is_valid_stream(src):
            if not src or not src.startswith('http'): return False
            if any(src.endswith(ext) for ext in SKIP_EXTENSIONS): return False
            if any(dom in src.lower() for dom in SKIP_DOMAINS): return False
            if 'uploads/thumb' in src or '/thumb/' in src: return False
            if 'tanti-film' in src.lower() and 'guarda' not in src.lower(): return False
            return True

        def add_link(src, label=''):
            src = src.strip()
            if not is_valid_stream(src): return
            if src in [l['url'] for l in links]: return
            if not label:
                label = self._label_from_url(src, SERVER_LABELS) or f'Server {len(links)+1}'
            links.append({'label': label, 'url': src, 'quality': self._guess_quality(src, label), 'lang': 'ITA'})
            xbmc.log(f"{TAG}   + {label} | {src[:80]}", xbmc.LOGINFO)

        for src in self.find_iframes(html):
            if src.startswith('/'): src = self.BASE_URL + src
            add_link(src)

        for attr in ['data-link', 'data-src', 'data-embed', 'data-video', 'data-url', 'data-file', 'data-source', 'data-stream', 'data-player']:
            for src in re.findall(rf'{attr}=["\']([^"\']+)["\']', html, re.IGNORECASE):
                if src.startswith('/'): src = self.BASE_URL + src
                add_link(src)

        js_urls = re.findall(r'''["'](https?://[^"'<>\s]{15,})["']''', html, re.IGNORECASE)
        for src in js_urls:
            add_link(src)

        xbmc.log(f"{TAG} Link validi: {len(links)}", xbmc.LOGINFO)
        return links

    def _label_from_url(self, url, server_map):
        url_lower = url.lower()
        for key, label in server_map.items():
            if key in url_lower: return label
        return ''

    def _guess_quality(self, url, label=''):
        combined = (url + label).lower()
        if any(x in combined for x in ['1080', 'fhd', 'fullhd', '4k']): return '1080p'
        if any(x in combined for x in ['720', 'hd', 'superhd']): return '720p'
        if any(x in combined for x in ['480', 'sd']): return '480p'
        return ''


scraper = TantiFilmScraper()
