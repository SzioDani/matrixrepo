# -*- coding: utf-8 -*-
import xbmc, xbmcaddon, urllib.parse, urllib.request, re, json
from resources.lib import tmdb_custom as tmdb
from resources.lib.tmdb_helper import TMDBHelper

# ============================================================
#   FUNZIONI CORE (PULIZIA E TRADUZIONE ORIGINALI)
# ============================================================

def core_clean(text):
    if not text: return ""
    text = re.sub(r'[a-f0-9]{20,}.*', '', text)
    text = text.replace('\\n', ' ').replace('\n', ' ')
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'(\.|\s|)(itit|enit|it|en)$', r'\1', text)
    text = re.sub(r'\.{2,}[a-z]*$', '...', text)
    return text.strip()
    
def core_translate(text, target_lang=None):
    if not text or len(str(text).strip()) < 5: return text
    if target_lang is None:
        lang_setting = xbmcaddon.Addon().getSetting("tmdb_lang_details") or "it-IT"
        target_lang = lang_setting.split('-')[0]

    try:
        text = core_clean(text)
        query = urllib.parse.quote(str(text))
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl={target_lang}&dt=t&q={query}"
        
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            # LEGGIAMO IL JSON CORRETTAMENTE
            data = json.loads(response.read().decode('utf-8'))
            if data and data[0]:
                # Uniamo TUTTI i pezzi della traduzione, nessuno escluso
                translated = "".join([part[0] for part in data[0] if part[0]])
                return core_clean(translated)
    except Exception as e:
        xbmc.log(f"[TMDB BRIDGE] Errore traduzione: {str(e)}", xbmc.LOGERROR)
        
    return core_clean(text)
    

# ============================================================
#   CLASSE TMDBBRIDGE
# ============================================================

def _is_latin_title(title):
    """Filtra titoli con caratteri non latini (cinese, arabo, coreano, ecc.)"""
    if not title: return True
    import unicodedata
    for ch in title:
        name = unicodedata.name(ch, '')
        if any(x in name for x in ['CJK', 'HIRAGANA', 'KATAKANA', 'HANGUL',
                                     'ARABIC', 'HEBREW', 'THAI', 'DEVANAGARI']):
            return False
    return True


class TMDBBridge:
    def __init__(self):
        xbmc.log('[MediaBridge][TMDBBridge] Inizializzazione TMDBBridge', xbmc.LOGINFO)
        try:
            self.helper = TMDBHelper(self)
            xbmc.log('[MediaBridge][TMDBBridge] TMDBHelper caricato OK', xbmc.LOGINFO)
        except Exception as e:
            xbmc.log(f'[MediaBridge][TMDBBridge] TMDBHelper errore: {e}', xbmc.LOGWARNING)
            self.helper = None
         
    def clean_text(self, text):
        return core_clean(text)

    def translate_text(self, text, target_lang='it'):
        return core_translate(text, target_lang)
        
    def search(self, query):
        """Ricerca Multipla localizzata"""
        lang_setting = xbmcaddon.Addon().getSetting("tmdb_lang_details") or "it-IT"
        target_code = lang_setting.split('-')[0]
        
        # Ora passiamo lang perché abbiamo aggiornato il custom!
        results = tmdb.search_multi(query, lang=lang_setting) 
        final = []
        
        for item in results:
            if not item: continue
            media_type = item.get("media_type")
            if media_type not in ["movie", "tv", "person"]: continue
            
            tmdb_id = item.get("id")
            if not tmdb_id: continue

            # Filtro spazzatura originale
            if media_type in ["movie", "tv"]:
                plot = item.get("overview") or ""
                poster = item.get("poster_path")
                if not poster and not plot: continue
                yr = (item.get("release_date") or item.get("first_air_date") or "")
                if not yr: continue
            
            poster = item.get("poster_path") or item.get("profile_path")
            fanart = item.get("backdrop_path")
            
            if media_type == "person" and not fanart:
                kf = item.get("known_for", [])
                if kf and isinstance(kf, list): fanart = kf[0].get("backdrop_path")
            
            title = item.get("title") or item.get("name") or "Sconosciuto"
            year_raw = (item.get("release_date") or item.get("first_air_date") or item.get("birthday") or "")
            year = year_raw[:4] if year_raw else ""
            
            final.append({
                "title": title, "year": year,
                "plot": item.get("overview") or item.get("biography") or "Dettagli non disponibili.",
                "rating": f"{str(item.get('vote_average', 0))[:3]}" if media_type != "person" else f"Pop: {int(item.get('popularity', 0))}",
                "poster": f"https://image.tmdb.org/t/p/w500{poster}" if poster else "",
                "fanart": f"https://image.tmdb.org/t/p/original{fanart}" if fanart else "",
                "tmdb_id": tmdb_id, "media_type": media_type
            })
            
        # Filtra titoli in lingue non latine (cinese, arabo, ecc.)
        final = [r for r in final if _is_latin_title(r.get('title', ''))]
        xbmc.log(f"[MediaBridge][TMDBBridge] Risultati dopo filtro lingue: {len(final)}", xbmc.LOGINFO)

        if self.helper and final:
            return self.helper.boost_collection(final)
        return final

    def get_details(self, tmdb_id, media_type, lang=None):
        target_setting = xbmcaddon.Addon().getSetting("tmdb_lang_details") or "it-IT"
        target_code = target_setting.split('-')[0]

        # Sfrutta il parametro lang ora presente nel tuo custom
        if media_type == "movie":
            d = tmdb.get_movie(tmdb_id, lang=target_setting) or {}
            plot = d.get("overview") or ""
            if not plot or len(str(plot)) < 20:
                d_en = tmdb.get_movie(tmdb_id, lang="en-US") or {}
                plot = self.translate_text(d_en.get("overview", ""), target_lang=target_code)
                    
            ext = d.get("external_ids") or {}
            return {
                "title": d.get("title") or d.get("original_title") or "N/A", 
                "plot": plot, 
                "poster": f"https://image.tmdb.org/t/p/w500{d.get('poster_path', '')}",
                "fanart": f"https://image.tmdb.org/t/p/original{d.get('backdrop_path', '')}",
                "genre": ", ".join([g.get("name") for g in d.get("genres", [])]),
                "rating": f"{str(d.get('vote_average', 0))[:3]}",
                "cast": ", ".join([c.get("name") for c in d.get("credits", {}).get("cast", [])[:15]]),
                "year": (d.get("release_date") or "")[:4],
                "imdb_id": ext.get("imdb_id") or d.get("imdb_id") or "",
            }
            
        elif media_type == "tv":
            d = tmdb.get_tv(tmdb_id, lang=target_setting) or {}
            plot = d.get("overview") or ""
            if not plot or len(str(plot)) < 20:
                d_en = tmdb.get_tv(tmdb_id, lang="en-US") or {}
                plot = self.translate_text(d_en.get("overview", ""), target_lang=target_code)
                    
            ext2 = d.get("external_ids") or {}
            return {
                "title": d.get("name") or d.get("original_name") or "N/A", 
                "plot": plot, 
                "poster": f"https://image.tmdb.org/t/p/w500{d.get('poster_path', '')}",
                "fanart": f"https://image.tmdb.org/t/p/original{d.get('backdrop_path', '')}",
                "genre": ", ".join([g.get("name") for g in d.get("genres", [])]),
                "rating": f"{str(d.get('vote_average', 0))[:3]}",
                "cast": ", ".join([c.get("name") for c in d.get("credits", {}).get("cast", [])[:15]]),
                "year": (d.get("first_air_date") or "")[:4],
                "seasons": str(d.get("number_of_seasons") or "0"),
                "episodes": str(d.get("number_of_episodes") or "0"),
                "imdb_id": ext2.get("imdb_id") or "",
            }
            
        elif media_type == "person":
            p = tmdb.get_person(tmdb_id, lang=target_setting) or {}
            biography = p.get("biography") or ""
            if not biography or len(biography) < 20:
                p_en = tmdb.get_person(tmdb_id, "en-US") or {}
                biography = self.translate_text(p_en.get("biography", ""), target_lang=target_code)
            
            nascita = p.get("birthday")
            data_ita = f"{nascita[8:10]}-{nascita[5:7]}-{nascita[0:4]}" if (nascita and len(str(nascita)) == 10) else ""
            luogo = p.get("place_of_birth") or ""
            voto_estetico = int(float(p.get('popularity', 0)) * 13) 
            gender = p.get("gender", 0)
            ruolo = "Attore" if gender == 2 else "Attrice" if gender == 1 else "Artista"
            
            c_luogo, c_voto, c_ruolo, c_reset = "[COLOR FFFF0099]", "[COLOR FFFFFF00]", "[COLOR FF00FFFF]", "[/COLOR]"
            sep = "[COLOR FFFF00FF] | [/COLOR]" 

            info_parts = []
            if luogo: info_parts.append(f"{c_luogo}{luogo}{c_reset}")
            info_parts.append(f"{c_ruolo}{ruolo}{c_reset}")
            
            profile = p.get("profile_path") or ""
            # Per la persona usiamo il profilo come poster
            # e il fanart dal primo film noto
            fanart = ""
            combined = p.get("combined_credits", {}) if isinstance(p.get("combined_credits"), dict) else {}
            known_for = combined.get("cast", [])
            for kf in known_for[:5]:
                if kf.get("backdrop_path"):
                    fanart = f"https://image.tmdb.org/t/p/original{kf['backdrop_path']}"
                    break

            return {
                "title": p.get("name") or "Sconosciuto",
                "plot": self.translate_text(biography, target_lang=target_code),
                "year": data_ita,
                "genre": sep.join(info_parts), 
                "rating": f"{c_voto}★ {voto_estetico}{c_reset}",
                "poster": f"https://image.tmdb.org/t/p/w500{profile}" if profile else "",
                "fanart": fanart,
                "credits": known_for
            }
            
        return {"title": "", "plot": ""}
        