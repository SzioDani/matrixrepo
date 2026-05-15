# -*- coding: utf-8 -*-
"""
Brotli stub compatibile con cloudscraper e urllib3 per Kodi Android.
Fornisce tutti gli attributi richiesti senza implementazione reale.
"""

class error(Exception):
    pass

class Decompressor:
    """Stub per urllib3 - non decomprime realmente"""
    def __init__(self):
        self._buf = b''
    def decompress(self, data):
        self._buf += data
        return b''
    def flush(self):
        return b''

class Compressor:
    """Stub per completezza"""
    def __init__(self, quality=11, lgwin=22, lgblock=0, mode=0, newline_urgency=0):
        pass
    def process(self, data):
        return b''
    def finish(self):
        return b''

# Costanti richieste
MODE_GENERIC = 0
MODE_TEXT = 1
MODE_FONT = 2

def decompress(data):
    raise error("Brotli nativo non disponibile - usa Accept-Encoding: identity")

def compress(data, quality=11, lgwin=22, lgblock=0, mode=MODE_GENERIC):
    raise error("Brotli compress non disponibile")
