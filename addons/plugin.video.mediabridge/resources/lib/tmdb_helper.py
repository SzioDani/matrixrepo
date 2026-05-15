# -*- coding: utf-8 -*-
import threading
import xbmc
import xbmcaddon
from resources.lib import tmdb_custom as tmdb

TAG = "[TMDB_HELPER]"

class TMDBHelper:
    def __init__(self, bridge_instance):
        self.bridge = bridge_instance
        self.addon = xbmcaddon.Addon()
        xbmc.log(f"{TAG} Init OK", xbmc.LOGINFO)

    def _get_target_lang(self):
        lang = self.addon.getSetting("tmdb_lang_details") or "it-IT"
        return lang.split('-')[0], lang

    def boost_collection(self, items_list):
        """Carica genere, cast, rating e traduce la trama per ogni item in parallelo"""
        if not items_list: return items_list
        xbmc.log(f"{TAG} Avvio Turbo Traduzione su {len(items_list)} elementi", xbmc.LOGINFO)
        target_code, target_lang = self._get_target_lang()
        threads = []
        for item in items_list:
            t = threading.Thread(target=self._boost_task, args=(item, target_code, target_lang))
            threads.append(t)
            t.start()
        for t in threads: t.join(timeout=10)
        xbmc.log(f"{TAG} Turbo completato con successo", xbmc.LOGINFO)
        return items_list

    def _boost_task(self, item, target_code, target_lang):
        try:
            tmdb_id = item.get('tmdb_id')
            media_type = item.get('media_type')

            # Persona: traduci solo la bio
            if media_type == 'person' or not tmdb_id:
                plot = item.get('plot', '')
                if plot and len(plot) > 10:
                    item['plot'] = self.bridge.translate_text(plot, target_lang=target_code)
                return

            # Film/Serie: carica dettagli completi
            if media_type == 'movie':
                d = tmdb.get_movie(tmdb_id, lang=target_lang) or {}
            elif media_type == 'tv':
                d = tmdb.get_tv(tmdb_id, lang=target_lang) or {}
            else:
                return

            # Genere
            genres = d.get('genres') or []
            item['genre'] = ", ".join([g.get('name', '') for g in genres if g.get('name')])

            # Rating
            vote = d.get('vote_average', 0)
            item['rating'] = f"{str(vote)[:3]}"

            # Cast (primi 10)
            cast_list = d.get('credits', {}).get('cast', [])
            item['cast'] = ", ".join([c.get('name', '') for c in cast_list[:10] if c.get('name')])

            # Stagioni/Episodi per TV
            if media_type == 'tv':
                s = str(d.get('number_of_seasons') or '')
                e = str(d.get('number_of_episodes') or '')
                item['seasons'] = s if s and s != '0' else ''
                item['episodes'] = e if e and e != '0' else ''

            # Poster/fanart se mancanti
            if not item.get('poster') and d.get('poster_path'):
                item['poster'] = f"https://image.tmdb.org/t/p/w500{d['poster_path']}"
            if not item.get('fanart') and d.get('backdrop_path'):
                item['fanart'] = f"https://image.tmdb.org/t/p/original{d['backdrop_path']}"

            # Trama: carica e traduci
            plot = d.get('overview') or item.get('plot', '')
            if not plot or len(plot) < 20:
                d_en = (tmdb.get_movie(tmdb_id, lang='en-US') if media_type == 'movie'
                        else tmdb.get_tv(tmdb_id, lang='en-US')) or {}
                plot = d_en.get('overview', '')
            if plot:
                item['plot'] = self.bridge.translate_text(plot, target_lang=target_code)

            # Mantieni solo il PRIMO genere come genere primario per la categorizzazione
            # ma mostra tutti nella UI
            if item.get('genre'):
                primary = item['genre'].split(',')[0].strip()
                item['primary_genre'] = primary

            xbmc.log(f"{TAG}   OK: {item.get('title')} | genere={item.get('genre','')} | cast={str(item.get('cast',''))[:40]}...", xbmc.LOGINFO)

        except Exception as e:
            xbmc.log(f"{TAG} Errore boost_task id={item.get('tmdb_id')}: {e}", xbmc.LOGERROR)

    def boost_full_details(self, id_list):
        """Per filmografie profonde"""
        if not id_list: return []
        xbmc.log(f"{TAG} Avvio Turbina Totale su {len(id_list)} elementi", xbmc.LOGINFO)
        target_code, target_lang = self._get_target_lang()
        results = [None] * len(id_list)
        threads = []
        for index, item in enumerate(id_list):
            t = threading.Thread(target=self._full_worker, args=(index, item, results, target_code, target_lang))
            threads.append(t)
            t.start()
        for t in threads: t.join(timeout=15)
        return [r for r in results if r is not None]

    def _full_worker(self, index, item, results, target_code, target_lang):
        try:
            tmdb_id = item.get('id')
            media_type = item.get('type')
            base_m = item.get('base_data', {})
            data = self.bridge.get_details(tmdb_id, media_type)
            if data:
                data['tmdb_id'] = tmdb_id
                data['media_type'] = media_type
                if media_type == 'tv':
                    data['seasons'] = str(data.get('seasons') or base_m.get('season_count') or '')
                    data['episodes'] = str(data.get('episodes') or base_m.get('episode_count') or '')
                else:
                    data['seasons'] = ''
                    data['episodes'] = ''
                plot_raw = data.get('plot') or base_m.get('overview') or ''
                data['plot'] = self.bridge.translate_text(plot_raw, target_lang=target_code)
                if not data.get('poster'):
                    path = base_m.get('poster_path')
                    data['poster'] = f"https://image.tmdb.org/t/p/w500{path}" if path else ''
                results[index] = data
        except Exception as e:
            xbmc.log(f"{TAG} Errore full_worker: {e}", xbmc.LOGERROR)
