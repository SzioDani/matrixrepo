# -*- coding: utf-8 -*-
"""
MediaBridge - Scraper GuardaHD
URL: https://guardahd.stream/index.php?task=set-movie-u&id_imdb=ttXXXXXXX
Usa l'IMDB ID direttamente - nessun scraping di ricerca necessario!

Note sui server (da analisi):
- vixsrc.to: funziona, conserva il codice IMDB
- supervideo.cc: cambia dominio ma conserva il codice es. /y/xxxxxx
- dr0pstream.com: cambia dominio ma conserva /e/xxxxxx  
- m1xdrop: cambia dominio (net->bz) ma conserva /e/xxxxxx
- streamhg: cambia dominio ma conserva /e/xxxxxx
- Server 4K (fullhd): richiede registrazione
"""

import re
import urllib.parse
import xbmc
from resources.lib.scrapers.base_scraper import BaseScraper

TAG = "[MediaBridge][GuardaHD]"

# Domini alternativi noti per ogni host
HOST_ALIASES = {
    'supervideo': ['supervideo.cc', 'supervideo.tv', 'supervideo.me'],
    'dropload': ['dr0pstream.com', 'dropload.io', 'dropload.cc'],
    'mixdrop': ['m1xdrop.net', 'm1xdrop.bz', 'mixdrop.co', 'mixdrop.to'],
    'streamhg': ['dhcplay.com', 'audinifer.com', 'vibuxer.com', 'streamhg.com'],
    'vixsrc': ['vixsrc.to', 'vixcloud.co'],
    'doodstream': ['dood.so', 'dood.la', 'doodstream.com'],
    'streamtape': ['streamtape.com', 'streamtape.cc'],
}

SKIP_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg',
                   '.css', '.js', '.ico', '.woff', '.ttf']


class GuardaHDScraper(BaseScraper):

    SITE_NAME = "GuardaHD"
    BASE_URL = "https://guardahd.stream"

    def search_url(self, query):
        # Non usato - usiamo IMDB ID direttamente
        return f"{self.BASE_URL}/?s={urllib.parse.quote_plus(query)}"

    def search(self, query, imdb_id=None):
        """Cerca usando IMDB ID se disponibile, altrimenti fallback"""
        if imdb_id and imdb_id.startswith('tt'):
            xbmc.log(f"{TAG} Ricerca via IMDB ID: {imdb_id}", xbmc.LOGINFO)
            return self._search_by_imdb(imdb_id, query)
        else:
            xbmc.log(f"{TAG} IMDB ID non disponibile, uso titolo: '{query}'", xbmc.LOGWARNING)
            return self._search_by_title(query)

    def _search_by_imdb(self, imdb_id, title=""):
        """Usa l'URL diretto con IMDB ID"""
        url = f"{self.BASE_URL}/index.php?task=set-movie-u&id_imdb={imdb_id}"
        xbmc.log(f"{TAG} URL IMDB: {url}", xbmc.LOGINFO)
        return [{
            'title': title or imdb_id,
            'url': url,
            'year': '',
            'poster': '',
            'type': 'movie',
            'imdb_id': imdb_id,
        }]

    def _search_by_title(self, query):
        """Fallback: ricerca per titolo"""
        html = self.fetch_clean(self.search_url(query))
        if not html:
            return []
        results = []
        links = re.findall(r'href=["\']([^"\']*(?:film|movie|guarda|streaming)[^"\']*)["\'][^>]*>([^<]{2,60})', html, re.IGNORECASE)
        seen = set()
        for href, text in links:
            text = self.clean_title(text)
            if not text or href in seen: continue
            if href.startswith('/'): href = self.BASE_URL + href
            if not href.startswith('http'): continue
            seen.add(href)
            results.append({'title': text, 'url': href, 'year': self.extract_year(href), 'poster': '', 'type': 'movie'})
        return results

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

        # Struttura HTML: <li class="active" data-link="URL">Nome Server</li>
        # Estrai tutti i data-link con il nome del server
        server_pattern = re.findall(
            r'<li[^>]+data-link=["\']([^"\']+)["\'][^>]*>\s*([^<]{2,30})\s*</li>',
            html, re.IGNORECASE | re.DOTALL
        )
        xbmc.log(f"{TAG} Server trovati: {len(server_pattern)}", xbmc.LOGINFO)

        for data_link, label in server_pattern:
            label = self.clean_title(label)
            data_link = data_link.strip()

            # Risolvi URL relativi
            if data_link.startswith('//'): 
                data_link = 'https:' + data_link
            elif data_link.startswith('/'):
                data_link = self.BASE_URL + data_link

            if not data_link.startswith('http'): continue
            if any(data_link.endswith(ext) for ext in SKIP_EXTENSIONS): continue

            # Salta Server 4K (richiede registrazione)
            if 'fullhd' in data_link.lower() or 'server 4k' in label.lower():
                xbmc.log(f"{TAG}   Skip 4K (richiede registrazione): {label}", xbmc.LOGDEBUG)
                continue

            quality = self._guess_quality(data_link, label)
            xbmc.log(f"{TAG}   + {label} | {quality} | {data_link[:80]}", xbmc.LOGINFO)
            links.append({
                'label': label,
                'url': data_link,
                'quality': quality,
                'lang': 'ITA',
            })

        # Fallback: cerca data-link anche senza testo
        if not links:
            xbmc.log(f"{TAG} Fallback: cerca data-link generici", xbmc.LOGWARNING)
            raw_links = re.findall(r'data-link=["\']([^"\']+)["\']', html, re.IGNORECASE)
            for i, src in enumerate(raw_links):
                if src.startswith('//'): src = 'https:' + src
                elif src.startswith('/'): src = self.BASE_URL + src
                if not src.startswith('http'): continue
                if 'fullhd' in src: continue
                links.append({'label': f'Server {i+1}', 'url': src, 'quality': self._guess_quality(src), 'lang': 'ITA'})

        xbmc.log(f"{TAG} Totale link: {len(links)}", xbmc.LOGINFO)
        return links

    def _guess_quality(self, url, label=''):
        combined = (url + label).lower()
        if any(x in combined for x in ['1080', 'fhd', 'fullhd', '4k']): return '1080p'
        if any(x in combined for x in ['720', 'hd', 'superhd']): return '720p'
        if any(x in combined for x in ['480', 'sd']): return '480p'
        return ''


scraper = GuardaHDScraper()
