# -*- coding: utf-8 -*-
"""
MediaBridge - Template Scraper
==============================================
ISTRUZIONI:
1. Copia questo file e rinominalo (es: sito_mio.py)
2. Cambia SITE_NAME con il nome del sito
3. Inserisci BASE_URL con l'URL del sito
4. Implementa search_url(), parse_results(), get_stream_links()
5. Registra lo scraper in scrapers/__init__.py
==============================================
"""

import re
import urllib.parse
from resources.lib.scrapers.base_scraper import BaseScraper


class SitoMioScraper(BaseScraper):

    # --------------------------------------------------------
    #  CONFIGURAZIONE - MODIFICA QUI
    # --------------------------------------------------------
    SITE_NAME = "SitoMio"
    BASE_URL = ""  # <-- INSERISCI L'URL BASE DEL SITO (es: "https://www.sito.it")

    # --------------------------------------------------------
    #  1. URL DI RICERCA
    # --------------------------------------------------------
    def search_url(self, query):
        """
        Costruisci qui l'URL di ricerca del sito.
        query = titolo cercato (già URL-encoded con urllib.parse.quote se necessario)

        Esempi comuni:
            return f"{self.BASE_URL}/search?q={urllib.parse.quote(query)}"
            return f"{self.BASE_URL}/cerca/{urllib.parse.quote_plus(query)}"
            return f"{self.BASE_URL}/?s={urllib.parse.quote(query)}"
        """
        return f"{self.BASE_URL}/search?q={urllib.parse.quote(query)}"  # <-- MODIFICA

    # --------------------------------------------------------
    #  2. PARSING RISULTATI RICERCA
    # --------------------------------------------------------
    def parse_results(self, html, query=None):
        """
        Analizza la pagina di ricerca e restituisce una lista di risultati.

        Suggerimento: apri la pagina di ricerca nel browser,
        clicca destro → Ispeziona, trova il blocco HTML dei risultati
        e costruisci il regex o BeautifulSoup di conseguenza.

        Struttura da restituire:
        [
            {
                'title': 'Titolo Film',
                'url': 'https://sito.it/film/titolo-film',
                'year': '2023',           # opzionale
                'poster': 'https://...',  # opzionale
                'type': 'movie',          # 'movie' o 'tv'
            }
        ]
        """
        results = []

        # ESEMPIO con regex - adatta in base all'HTML del sito:
        # pattern = re.findall(
        #     r'<div class="film-card">.*?<a href="([^"]+)"[^>]*>([^<]+)</a>.*?(\d{4})',
        #     html, re.DOTALL | re.IGNORECASE
        # )
        # for url, title, year in pattern:
        #     results.append({
        #         'title': self.clean_title(title),
        #         'url': self.BASE_URL + url if url.startswith('/') else url,
        #         'year': year,
        #         'type': 'movie'
        #     })

        return results  # <-- IMPLEMENTA LA LOGICA

    # --------------------------------------------------------
    #  3. ESTRAZIONE LINK STREAM
    # --------------------------------------------------------
    def get_stream_links(self, url):
        """
        Data la pagina di dettaglio di un film/serie, estrai i link ai player/embed.

        Suggerimento: apri la pagina del film nel browser,
        usa F12 → Network → filtra per "embed" o "player",
        oppure ispeziona il sorgente HTML per trovare gli iframe.

        Struttura da restituire:
        [
            {
                'label': 'Server 1 - HD',
                'url': 'https://embed.server.com/video/xyz',
                'quality': 'HD',   # opzionale
                'lang': 'ITA',     # opzionale
            }
        ]
        """
        links = []
        html = self.fetch(url, prefer_flare=True)
        if not html:
            return links

        # METODO 1: cerca iframe automaticamente
        iframes = self.find_iframes(html)
        for i, src in enumerate(iframes):
            links.append({
                'label': f'Server {i+1}',
                'url': src,
                'quality': '',
                'lang': 'ITA'
            })

        # METODO 2: cerca embed URL con regex custom
        # Esempio:
        # pattern = re.findall(r'data-url=["\']([^"\']+)["\']', html)
        # for src in pattern:
        #     links.append({'label': 'Embed', 'url': src, 'quality': 'HD', 'lang': 'ITA'})

        return links  # <-- IMPLEMENTA LA LOGICA


# Istanza globale usata dal manager
scraper = SitoMioScraper()
