# -*- coding: utf-8 -*-
"""
MediaBridge - Cloudflare Bypass Layer
Metodi: cloudscraper, headers spoofing, FlareSolverr
Compatibile con WiFi e rete dati mobile
"""

import xbmc
import xbmcaddon
import json
import time

TAG = "[MediaBridge][CF]"

HEADERS_CHROME = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Cache-Control': 'max-age=0',
}

HEADERS_MOBILE = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.82 Mobile Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'it-IT,it;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

# Timeout generosi per funzionare anche su rete dati lenta
TIMEOUT_CONNECT = 10   # secondi per stabilire connessione
TIMEOUT_READ    = 30   # secondi per leggere la risposta
MAX_RETRIES     = 3    # tentativi in caso di timeout


class CloudflareBypass:

    def __init__(self):
        self.addon = xbmcaddon.Addon()
        self.flaresolverr_url = self.addon.getSetting('flaresolverr_url') or 'http://localhost:8191'
        try:
            self.flaresolverr_enabled = self.addon.getSettingBool('flaresolverr_enabled')
        except Exception:
            self.flaresolverr_enabled = self.addon.getSetting('flaresolverr_enabled') == 'true'
        self._session_cookies = {}
        xbmc.log(f"{TAG} Init OK | FlareSolverr={self.flaresolverr_enabled} | timeout={TIMEOUT_READ}s", xbmc.LOGINFO)

    # ----------------------------------------------------------
    #  METODO 1: cloudscraper
    # ----------------------------------------------------------
    def get_cloudscraper(self, url, headers=None, timeout=None):
        t = timeout or (TIMEOUT_CONNECT, TIMEOUT_READ)
        try:
            # cloudscraper è bundled dentro resources/lib/
            import sys, os, xbmcvfs
            _lib_path = xbmcvfs.translatePath('special://home/addons/plugin.video.mediabridge/resources/lib')
            if _lib_path not in sys.path:
                sys.path.insert(0, _lib_path)
            xbmc.log(f"{TAG} cloudscraper bundled, lib path: {_lib_path}", xbmc.LOGINFO)
            import cloudscraper
            xbmc.log(f"{TAG} cloudscraper: avvio per {url}", xbmc.LOGINFO)
            scraper = cloudscraper.create_scraper(
                browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False},
                allow_brotli=False  # Gestiamo brotli manualmente
            )
            h = dict(headers or HEADERS_CHROME)
            h['Accept-Encoding'] = 'gzip, deflate, br'
            resp = scraper.get(url, headers=h, timeout=t)
            xbmc.log(f"{TAG} cloudscraper status: {resp.status_code} | encoding: {resp.encoding} | content-encoding: {resp.headers.get('content-encoding','none')}", xbmc.LOGINFO)
            if resp.status_code == 200:
                # Decompressione robusta
                raw = resp.content
                content_enc = resp.headers.get('content-encoding', '').lower()
                xbmc.log(f"{TAG} raw bytes: {len(raw)} | content-encoding: {content_enc} | first bytes: {raw[:4].hex()}", xbmc.LOGINFO)

                def is_html(t):
                    return bool(t and ('<html' in t[:1000].lower() or '<div' in t[:1000].lower() or '<!doc' in t[:1000].lower() or '<head' in t[:500].lower()))

                # Metodo 1: brotli (firma 1b77a4 o altri header brotli)
                try:
                    import brotli
                    text = brotli.decompress(raw).decode('utf-8', errors='replace')
                    if is_html(text):
                        xbmc.log(f"{TAG} brotli OK: {len(text)} chars | inizio: {text[:80]}", xbmc.LOGINFO)
                        return text
                except Exception as e1:
                    xbmc.log(f"{TAG} brotli fallito: {e1}", xbmc.LOGDEBUG)

                # Metodo 2: gzip
                try:
                    import gzip
                    text = gzip.decompress(raw).decode('utf-8', errors='replace')
                    if is_html(text):
                        xbmc.log(f"{TAG} gzip OK: {len(text)} chars", xbmc.LOGINFO)
                        return text
                except Exception as e2:
                    xbmc.log(f"{TAG} gzip fallito: {e2}", xbmc.LOGDEBUG)

                # Metodo 3: zlib
                try:
                    import zlib
                    text = zlib.decompress(raw, 47).decode('utf-8', errors='replace')
                    if is_html(text):
                        xbmc.log(f"{TAG} zlib OK: {len(text)} chars", xbmc.LOGINFO)
                        return text
                except Exception as e3:
                    xbmc.log(f"{TAG} zlib fallito: {e3}", xbmc.LOGDEBUG)

                # Metodo 4: testo diretto (se non compresso)
                try:
                    text = resp.text
                    if is_html(text):
                        xbmc.log(f"{TAG} resp.text OK: {len(text)} chars", xbmc.LOGINFO)
                        return text
                except Exception as e4:
                    xbmc.log(f"{TAG} resp.text fallito: {e4}", xbmc.LOGDEBUG)

                # Metodo 5: richiesta con identity (no compression)
                try:
                    h2 = dict(h)
                    h2['Accept-Encoding'] = 'identity'
                    resp2 = scraper.get(url, headers=h2, timeout=t)
                    if resp2.status_code == 200:
                        text = resp2.text
                        if is_html(text):
                            xbmc.log(f"{TAG} identity OK: {len(text)} chars", xbmc.LOGINFO)
                            return text
                except Exception as e5:
                    xbmc.log(f"{TAG} identity fallito: {e5}", xbmc.LOGDEBUG)

                xbmc.log(f"{TAG} TUTTI i metodi di decompressione falliti", xbmc.LOGERROR)
            xbmc.log(f"{TAG} cloudscraper HTTP {resp.status_code}", xbmc.LOGWARNING)
        except ImportError:
            xbmc.log(f"{TAG} cloudscraper NON installato, uso fallback", xbmc.LOGWARNING)
        except Exception as e:
            xbmc.log(f"{TAG} cloudscraper errore: {e}", xbmc.LOGERROR)
        return None

    # ----------------------------------------------------------
    #  METODO 2: requests con headers + retry automatico
    # ----------------------------------------------------------
    def get_with_headers(self, url, headers=None, cookies=None, timeout=None):
        t = timeout or (TIMEOUT_CONNECT, TIMEOUT_READ)
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                import requests
                from requests.adapters import HTTPAdapter
                from urllib3.util.retry import Retry

                xbmc.log(f"{TAG} Headers spoofing tentativo {attempt}/{MAX_RETRIES}: {url}", xbmc.LOGINFO)

                s = requests.Session()
                # Retry automatico su errori di rete (non su timeout di lettura)
                retry = Retry(connect=2, backoff_factor=1)
                adapter = HTTPAdapter(max_retries=retry)
                s.mount('https://', adapter)
                s.mount('http://', adapter)

                if cookies:
                    s.cookies.update(cookies)

                # Alterna headers desktop e mobile nei tentativi
                h = HEADERS_MOBILE if attempt % 2 == 0 else (headers or HEADERS_CHROME)

                resp = s.get(url, headers=h, timeout=t, allow_redirects=True)
                xbmc.log(f"{TAG} Headers status: {resp.status_code} | len={len(resp.text)}", xbmc.LOGINFO)

                if resp.status_code == 200:
                    return resp.text, s.cookies.get_dict()

                # Cloudflare 403/503 - attendi e riprova
                if resp.status_code in (403, 503):
                    xbmc.log(f"{TAG} CF challenge ({resp.status_code}), attendo 2s...", xbmc.LOGWARNING)
                    time.sleep(2)
                    continue

                xbmc.log(f"{TAG} Headers HTTP {resp.status_code}", xbmc.LOGWARNING)

            except Exception as e:
                xbmc.log(f"{TAG} Headers tentativo {attempt} errore: {e}", xbmc.LOGERROR)
                if attempt < MAX_RETRIES:
                    xbmc.log(f"{TAG} Riprovo tra 2s...", xbmc.LOGINFO)
                    time.sleep(2)

        return None, {}

    # ----------------------------------------------------------
    #  METODO 3: FlareSolverr
    # ----------------------------------------------------------
    def get_flaresolverr(self, url, timeout=60):
        if not self.flaresolverr_enabled:
            xbmc.log(f"{TAG} FlareSolverr disabilitato", xbmc.LOGDEBUG)
            return None
        try:
            import requests
            xbmc.log(f"{TAG} FlareSolverr: invio per {url}", xbmc.LOGINFO)
            payload = {"cmd": "request.get", "url": url, "maxTimeout": timeout * 1000}
            resp = requests.post(f"{self.flaresolverr_url}/v1", json=payload, timeout=timeout + 10)
            data = resp.json()
            if data.get('status') == 'ok':
                solution = data.get('solution', {})
                for c in solution.get('cookies', []):
                    self._session_cookies[c['name']] = c['value']
                xbmc.log(f"{TAG} FlareSolverr OK", xbmc.LOGINFO)
                return solution.get('response', '')
            xbmc.log(f"{TAG} FlareSolverr fallito: {data.get('message')}", xbmc.LOGWARNING)
        except Exception as e:
            xbmc.log(f"{TAG} FlareSolverr errore: {e}", xbmc.LOGERROR)
        return None

    # ----------------------------------------------------------
    #  METODO UNIFICATO: cascata
    # ----------------------------------------------------------
    def get(self, url, headers=None, prefer_flare=False):
        xbmc.log(f"{TAG} Fetch: {url} | prefer_flare={prefer_flare}", xbmc.LOGINFO)

        if prefer_flare and self.flaresolverr_enabled:
            result = self.get_flaresolverr(url)
            if result:
                xbmc.log(f"{TAG} Successo via FlareSolverr", xbmc.LOGINFO)
                return result

        result = self.get_cloudscraper(url, headers=headers)
        if result:
            xbmc.log(f"{TAG} Successo via cloudscraper", xbmc.LOGINFO)
            return result

        result, cookies = self.get_with_headers(url, headers=headers, cookies=self._session_cookies)
        if result:
            self._session_cookies.update(cookies)
            xbmc.log(f"{TAG} Successo via headers spoofing", xbmc.LOGINFO)
            return result

        xbmc.log(f"{TAG} TUTTI I METODI FALLITI per: {url}", xbmc.LOGERROR)
        return None

    def get_json(self, url, headers=None):
        text = self.get(url, headers=headers)
        if text:
            try:
                return json.loads(text)
            except Exception as e:
                xbmc.log(f"{TAG} JSON parse errore: {e}", xbmc.LOGERROR)
        return None

    def get_cookies(self):
        return self._session_cookies
