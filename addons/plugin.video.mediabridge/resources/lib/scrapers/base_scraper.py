# -*- coding: utf-8 -*-
"""
MediaBridge - Base Scraper
Classe base da cui ereditano tutti gli scraper specifici.
"""

import re
import xbmc
from resources.lib.cloudflare.bypass import CloudflareBypass


class BaseScraper:
    """
    Classe base per ogni scraper.
    Ogni sito deve creare una sottoclasse e implementare:
      - SITE_NAME     : nome del sito (stringa)
      - BASE_URL      : URL base del sito (TU INSERISCI)
      - search_url()  : costruisce l'URL di ricerca
      - parse_results(): estrae i risultati dalla pagina
      - get_stream_links(): estrae i link stream da una pagina dettaglio
    """

    SITE_NAME = "BaseScraper"
    BASE_URL = ""  # <-- TU INSERISCI L'URL DEL SITO

    def __init__(self):
        self.cf = CloudflareBypass()
        self.tag = f"[MediaBridge][{self.SITE_NAME}]"

    def log(self, msg, level=xbmc.LOGDEBUG):
        xbmc.log(f"{self.tag} {msg}", level)

    # ----------------------------------------------------------
    #  DA IMPLEMENTARE NEL SCRAPER FIGLIO
    # ----------------------------------------------------------

    def search_url(self, query):
        """
        Costruisce l'URL di ricerca per il sito.
        Esempio:
            return f"{self.BASE_URL}/search?q={urllib.parse.quote(query)}"
        """
        raise NotImplementedError(f"{self.SITE_NAME}: search_url() non implementato")

    def parse_results(self, html, query=None):
        """
        Analizza l'HTML della pagina di ricerca e restituisce una lista di dict:
        [
            {
                'title': 'Titolo',
                'url': 'https://sito.com/film/titolo',
                'year': '2023',          # opzionale
                'poster': 'https://...',  # opzionale
                'type': 'movie' o 'tv'   # opzionale
            },
            ...
        ]
        """
        raise NotImplementedError(f"{self.SITE_NAME}: parse_results() non implementato")

    def get_stream_links(self, url):
        """
        Dato l'URL della pagina dettaglio, estrae tutti i link embed/stream.
        Restituisce una lista di dict:
        [
            {
                'label': 'Server 1 - HD',
                'url': 'https://embed.esempio.com/video/abc123',
                'quality': 'HD',  # opzionale
                'lang': 'ITA',    # opzionale
            },
            ...
        ]
        """
        raise NotImplementedError(f"{self.SITE_NAME}: get_stream_links() non implementato")

    # ----------------------------------------------------------
    #  METODI HELPER (già implementati, pronti all'uso)
    # ----------------------------------------------------------

    def fetch(self, url, prefer_flare=False):
        """Scarica una pagina con bypass Cloudflare automatico"""
        return self.cf.get(url, prefer_flare=prefer_flare)

    def fetch_json(self, url):
        """Scarica e parsa JSON"""
        return self.cf.get_json(url)

    def clean_html(self, html):
        """Rimuove caratteri null e problematici dall'HTML prima del parsing"""
        if not html:
            return html
        # Rimuovi null bytes e caratteri di controllo
        html = html.replace('\x00', '').replace('\0', '')
        # Rimuovi altri caratteri di controllo tranne tab, newline, carriage return
        html = ''.join(ch for ch in html if ord(ch) >= 32 or ch in ('\t', '\n', '\r'))
        return html

    def search(self, query):
        """
        Flusso completo di ricerca:
        1. Costruisce URL
        2. Scarica la pagina
        3. Pulisce l'HTML
        4. Parsa i risultati
        Restituisce lista di risultati o []
        """
        try:
            url = self.search_url(query)
            self.log(f"Ricerca: {url}", xbmc.LOGINFO)
            html = self.fetch(url)
            if not html:
                self.log("Pagina vuota o errore fetch", xbmc.LOGWARNING)
                return []
            html = self.clean_html(html)
            self.log(f"HTML pulito: {len(html)} caratteri", xbmc.LOGDEBUG)
            results = self.parse_results(html, query=query)
            self.log(f"Trovati {len(results)} risultati", xbmc.LOGINFO)
            return results
        except Exception as e:
            self.log(f"Errore search: {e}", xbmc.LOGERROR)
            return []

    def get_links(self, url):
        """
        Flusso completo per ottenere link stream da URL dettaglio.
        Restituisce lista di link o []
        """
        try:
            self.log(f"Estraggo link da: {url}", xbmc.LOGINFO)
            links = self.get_stream_links(url)
            self.log(f"Trovati {len(links)} link", xbmc.LOGINFO)
            return links
        except Exception as e:
            self.log(f"Errore get_links: {e}", xbmc.LOGERROR)
            return []

    def fetch_clean(self, url, prefer_flare=False):
        """Scarica una pagina e pulisce null chars automaticamente"""
        html = self.fetch(url, prefer_flare=prefer_flare)
        return self.clean_html(html) if html else None

    # ----------------------------------------------------------
    #  UTILITY REGEX COMUNI
    # ----------------------------------------------------------

    def find_iframes(self, html):
        """Estrae tutti gli src degli iframe presenti nell'HTML"""
        return re.findall(r'<iframe[^>]+src=["\']([^"\']+)["\']', html, re.IGNORECASE)

    def find_embed_urls(self, html):
        """Cerca pattern comuni di URL embed in tutto l'HTML"""
        patterns = [
            r'(?:src|href|data-src|file)["\s]*[:=]["\s]*["\']?(https?://[^"\'<>\s]+)',
            r'(?:embed|player|iframe)[^"\']*["\']?(https?://[^"\'<>\s]+)',
        ]
        found = []
        for p in patterns:
            found.extend(re.findall(p, html, re.IGNORECASE))
        # Deduplica
        return list(dict.fromkeys(found))

    def clean_title(self, title):
        """Pulisce un titolo da caratteri indesiderati"""
        if not title:
            return ""
        title = re.sub(r'\s+', ' ', title).strip()
        title = re.sub(r'[\r\n\t]', ' ', title)
        return title.strip()

    def extract_year(self, text):
        """Estrae un anno (4 cifre tra 1900 e 2099) da una stringa"""
        match = re.search(r'\b(19\d{2}|20\d{2})\b', text or "")
        return match.group(1) if match else ""
