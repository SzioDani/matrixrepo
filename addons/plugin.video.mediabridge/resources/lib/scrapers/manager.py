# -*- coding: utf-8 -*-
import threading
import re
import xbmc

TAG = "[MediaBridge][ScraperManager]"

from resources.lib.scrapers.guardahd import GuardaHDScraper
from resources.lib.scrapers.tantifilm import TantiFilmScraper

REGISTERED_SCRAPERS = [
    GuardaHDScraper(),
    TantiFilmScraper(),
]


class ScraperManager:

    def __init__(self):
        self.scrapers = REGISTERED_SCRAPERS

    def log(self, msg, level=xbmc.LOGDEBUG):
        xbmc.log(f"{TAG} {msg}", level)

    def search_all(self, query, imdb_id=None):
        if not self.scrapers:
            self.log("Nessuno scraper registrato!", xbmc.LOGWARNING)
            return []
        all_results = []
        lock = threading.Lock()
        threads = []

        def _worker(scraper, q, iid, results, lk):
            try:
                if hasattr(scraper, 'search') and iid:
                    try:
                        found = scraper.search(q, imdb_id=iid)
                    except TypeError:
                        found = scraper.search(q)
                else:
                    found = scraper.search(q)
                for r in found:
                    r['_site'] = scraper.SITE_NAME
                with lk:
                    results.extend(found)
            except Exception as e:
                xbmc.log(f"{TAG} Errore {scraper.SITE_NAME}: {e}", xbmc.LOGERROR)

        for s in self.scrapers:
            t = threading.Thread(target=_worker, args=(s, query, imdb_id, all_results, lock))
            threads.append(t)
            t.start()
        for t in threads:
            t.join(timeout=30)

        self.log(f"Totale risultati: {len(all_results)}", xbmc.LOGINFO)
        return all_results

    def get_links_all(self, url, site_name=None):
        if site_name:
            for s in self.scrapers:
                if s.SITE_NAME == site_name:
                    return s.get_links(url)
            return []
        for s in self.scrapers:
            links = s.get_links(url)
            if links:
                return links
        return []

    def resolve_with_resolveurl(self, url):
        # Resolver manuale per vixsrc
        if 'vixsrc.to' in url or 'vixcloud.co' in url:
            resolved = self._resolve_vixsrc(url)
            if resolved:
                return resolved
            xbmc.log(f"{TAG} vixsrc fallback URL diretto", xbmc.LOGWARNING)
            return url

        # ResolveURL standard
        try:
            import resolveurl
            if resolveurl.HostedMediaFile(url).valid_url():
                resolved = resolveurl.HostedMediaFile(url).resolve()
                xbmc.log(f"{TAG} ResolveURL OK: {resolved[:80]}", xbmc.LOGINFO)
                return resolved
            xbmc.log(f"{TAG} ResolveURL non supportato: {url}", xbmc.LOGWARNING)
        except ImportError:
            xbmc.log(f"{TAG} resolveurl non installato", xbmc.LOGWARNING)
        except Exception as e:
            xbmc.log(f"{TAG} ResolveURL errore: {e}", xbmc.LOGERROR)

        xbmc.log(f"{TAG} Fallback URL diretto: {url}", xbmc.LOGINFO)
        return url

    def _resolve_vixsrc(self, url):
        """Resolver manuale per vixsrc.to - cerca URL m3u8/mp4 nella pagina"""
        try:
            import requests
            from resources.lib.cloudflare.bypass import HEADERS_CHROME
            xbmc.log(f"{TAG} vixsrc resolver: {url}", xbmc.LOGINFO)
            h = dict(HEADERS_CHROME)
            h['Referer'] = 'https://vixsrc.to/'
            resp = requests.get(url, headers=h, timeout=15, allow_redirects=True)
            if resp.status_code != 200:
                return None
            html = resp.text
            # Cerca URL video diretti
            pat_m3u8 = re.compile(r'https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*')
            pat_mp4 = re.compile(r'https?://[^\s"\'<>]+\.mp4[^\s"\'<>]*')
            for pat in [pat_m3u8, pat_mp4]:
                for m in pat.findall(html):
                    if 'vixsrc' not in m and 'tmdb' not in m and 'google' not in m:
                        xbmc.log(f"{TAG} vixsrc trovato: {m[:80]}", xbmc.LOGINFO)
                        ua = HEADERS_CHROME.get('User-Agent', '')
                        return f"{m}|Referer={url}&User-Agent={ua}"
        except Exception as e:
            xbmc.log(f"{TAG} vixsrc errore: {e}", xbmc.LOGERROR)
        return None

    def get_scraper_names(self):
        return [s.SITE_NAME for s in self.scrapers]
