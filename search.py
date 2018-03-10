import common
from notifiers import notify
from rssconfig import RssConfig
from rssdb import RssDb
from url import getURL
from url import postURL

from bs4 import BeautifulSoup as bs
import feedparser
import json
import logging
import re
import os
import sys

def get(title):
    query = title.replace(".", " ").replace(" ", "+")
    mb = getURL("http://www.movie-blog.org/index.php?s=" + query)
    mb = re.findall(r'post-.*?<a href="http:\/{2}.*?\/(.*?)" rel.*?>(.*?)<', mb)
    print mb[1][0]
    results = []
    result_id = 0
    for result in mb:
        results.append([result_id, result[0].replace("/", "+"), result[1]])
        result_id += 1
    print str(results)
    mb = results
    sj = postURL("http://serienjunkies.org/media/ajax/search/search.php", data={'string': "'" + query + "'"})
    sj = json.loads(sj)
    return mb, sj

def download_dl(title, jdownloaderpath, hoster, staffel, db, config):
    search_title = title.replace(".German.720p.", ".German.DL.1080p.").replace(".German.DTS.720p.", ".German.DTS.DL.1080p.").replace(".German.AC3.720p.", ".German.AC3.DL.1080p.").replace(".German.AC3LD.720p.", ".German.AC3LD.DL.1080p.").replace(".German.AC3.Dubbed.720p.", ".German.AC3.Dubbed.DL.1080p.").split('.x264-', 1)[0].split('.h264-', 1)[0].replace(".", " ").replace(" ", "+")
    search_url = "aHR0cDovL3d3dy5tb3ZpZS1ibG9nLm9yZy9zZWFyY2gv".decode('base64') + search_title + "/feed/rss2/"
    feedsearch_title = title.replace(".German.720p.", ".German.DL.1080p.").replace(".German.DTS.720p.", ".German.DTS.DL.1080p.").replace(".German.AC3.720p.", ".German.AC3.DL.1080p.").replace(".German.AC3LD.720p.", ".German.AC3LD.DL.1080p.").replace(".German.AC3.Dubbed.720p.", ".German.AC3.Dubbed.DL.1080p.").split('.x264-', 1)[0].split('.h264-', 1)[0]
    if not '.dl.' in feedsearch_title.lower():
        logging.debug("%s - Release ignoriert (nicht zweisprachig, da wahrscheinlich nicht Retail)" %feedsearch_title)
        return False
    for (key, value, pattern) in dl_search(feedparser.parse(search_url), feedsearch_title):
        download_link = False
        req_page = getURL(value[0])
        soup = bs(req_page, 'lxml')
        download = soup.find("div", {"id": "content"})
        url_hosters = re.findall(r'href="([^"\'>]*)".+?(.+?)<', str(download))
        for url_hoster in url_hosters:
            if not "bW92aWUtYmxvZy5vcmcv".decode("base64") in url_hoster[0]:
                if hoster.lower() in url_hoster[1].lower():
                    download_link = url_hoster[0]

        if download_link:
            if "aHR0cDovL3d3dy5tb3ZpZS1ibG9nLm9yZy8yMDEw".decode("base64") in download_link:
                logging.debug("Fake-Link erkannt!")
                return False
            elif staffel:
                common.write_crawljob_file(
                    key,
                    key,
                    download_link,
                    jdownloaderpath + "/folderwatch",
                    "RSScrawler/Remux"
                )
                db.store(
                    key,
                    'dl' if config.get('enforcedl') and '.dl.' in key.lower() else 'added'
                )
                log_entry = '[Staffel] - <b>Zweisprachig</b> - ' + key + ' - <a href="' + download_link + '" target="_blank" title="Link &ouml;ffnen"><i class="fas fa-link"></i></a> <a href="#log" ng-click="resetTitle(&#39;' + key + '&#39;)" title="Download f&uuml;r n&auml;chsten Suchlauf zur&uuml;cksetzen"><i class="fas fa-undo"></i></a>'
                logging.info(log_entry)
                notify(log_entry)
                return True
            elif '.3d.' in key.lower():
                retail = False
                if config.get('cutoff'):
                    if common.cutoff(key, '2'):
                        retail = True
                common.write_crawljob_file(
                    key,
                    key,
                    download_link,
                    jdownloaderpath + "/folderwatch",
                    "RSScrawler/3Dcrawler"
                )
                db.store(
                    key,
                    'dl' if config.get('enforcedl') and '.dl.' in key.lower() else 'added'
                )
                log_entry = '[Film] - <b>' + ('Retail/' if retail else "") + '3D/Zweisprachig</b> - ' + key + ' - <a href="' + download_link + '" target="_blank" title="Link &ouml;ffnen"><i class="fas fa-link"></i></a> <a href="#log" ng-click="resetTitle(&#39;' + key + '&#39;)" title="Download f&uuml;r n&auml;chsten Suchlauf zur&uuml;cksetzen"><i class="fas fa-undo"></i></a>'
                logging.info(log_entry)
                notify(log_entry)
                return True
            else:
                retail = False
                if config.get('cutoff'):
                    if config.get('enforcedl'):
                        if common.cutoff(key, '1'):
                            retail = True
                    else:
                        if common.cutoff(key, '0'):
                            retail = True
                common.write_crawljob_file(
                    key,
                    key,
                    download_link,
                    jdownloaderpath + "/folderwatch",
                    "RSScrawler/Remux"
                )
                db.store(
                    key,
                    'dl' if config.get('enforcedl') and '.dl.' in key.lower() else 'added'
                )
                log_entry = '[Film] - <b>' + ('Retail/' if retail else "") + 'Zweisprachig</b> - ' + key + ' - <a href="' + download_link + '" target="_blank" title="Link &ouml;ffnen"><i class="fas fa-link"></i></a> <a href="#log" ng-click="resetTitle(&#39;' + key + '&#39;)" title="Download f&uuml;r n&auml;chsten Suchlauf zur&uuml;cksetzen"><i class="fas fa-undo"></i></a>'
                logging.info(log_entry)
                notify(log_entry)
                return True

def dl_search(feed, title):
    s = re.sub(r"[&#\s/]", ".", title).lower()
    for post in feed.entries:
        found = re.search(s, post.title.lower())
        if found:
            yield (post.title, [post.link], title)

def mb(link, jdownloaderpath):
    link = link.replace("+", "/")
    url = getURL("http://movie-blog.org/" + link)
    rsscrawler = RssConfig('RSScrawler')
    config = RssConfig('MB')
    hoster = rsscrawler.get('hoster')
    db = RssDb(os.path.join(os.path.dirname(sys.argv[0]), "Einstellungen/Downloads/Downloads.db"))

    soup = bs(url, 'lxml')
    download = soup.find("div", {"id": "content"})
    key = re.findall(r'Permanent Link: (.*?)"', str(download)).pop()
    url_hosters = re.findall(r'href="([^"\'>]*)".+?(.+?)<', str(download))
    download_link = ""
    for url_hoster in url_hosters:
        if not "bW92aWUtYmxvZy5vcmcv".decode("base64") in url_hoster[0]:
            if hoster.lower() in url_hoster[1].lower():
                download_link = url_hoster[0]

    englisch = False
    if "*englisch*" in key.lower():
        key = key.replace('*ENGLISCH*', '').replace("*Englisch*", "")
        englisch = True

    staffel = re.search(r"s\d{1,2}(-s\d{1,2}|-\d{1,2}|\.)", key.lower())

    if config.get('enforcedl') and '.dl.' not in key.lower():
        original_language = ""
        fail = False
        get_imdb_url = url
        key_regex = r'<title>' + re.escape(key) + r'.*?<\/title>\n.*?<link>(?:(?:.*?\n){1,25}).*?[mM][kK][vV].*?(?:|href=.?http(?:|s):\/\/(?:|www\.)imdb\.com\/title\/(tt[0-9]{7,9}).*?)[iI][mM][dD][bB].*?(?!\d(?:\.|\,)\d)(?:.|.*?)<\/a>'
        imdb_id = re.findall(key_regex, get_imdb_url)
        if len(imdb_id) > 0:
            if not imdb_id[0]:
                fail = True
            else:
                imdb_id = imdb_id[0]
        else:
            fail = True
        if fail:
            search_title = re.findall(r"(.*?)(?:\.(?:(?:19|20)\d{2})|\.German|\.\d{3,4}p|\.S(?:\d{1,3})\.)", key)[0].replace(".", "+")
            search_url = "http://www.imdb.com/find?q=" + search_title
            search_page = getURL(search_url)
            search_results = re.findall(r'<td class="result_text"> <a href="\/title\/(tt[0-9]{7,9})\/\?ref_=fn_al_tt_\d" >(.*?)<\/a>.*? \((\d{4})\)..(.{9})', search_page)
            total_results = len(search_results)
            if total_results == 0:
                download_imdb = ""
            elif staffel:
                imdb_id = search_results[0][0]
            else:
                no_series = False
                while total_results > 0:
                    attempt = 0
                    for result in search_results:
                        if result[3] == "TV Series":
                            no_series = False
                            total_results -= 1
                            attempt += 1
                        else:
                            no_series = True
                            imdb_id = search_results[attempt][0]
                            total_results = 0
                            break
                if no_series is False:
                    logging.debug("%s - Keine passende Film-IMDB-Seite gefunden" % key)
        if not imdb_id:
            if not download_dl(key, jdownloaderpath, hoster, staffel, db, config):
                logging.debug("%s - Kein zweisprachiges Release gefunden." % key)
        else:
            if isinstance(imdb_id, list):
                imdb_id = imdb_id.pop()
            imdb_url = "http://www.imdb.com/title/" + imdb_id
            details = getURL(imdb_url)
            if not details:
                logging.debug("%s - Originalsprache nicht ermittelbar" % key)
            original_language = re.findall(r"Language:<\/h4>\n.*?\n.*?url'>(.*?)<\/a>", details)
            if original_language:
                original_language = original_language[0]
            if original_language == "German":
                logging.debug("%s - Originalsprache ist Deutsch. Breche Suche nach zweisprachigem Release ab!" % key)
            else:
                if not download_dl(key, jdownloaderpath, hoster, staffel, db, config) and not englisch:
                    logging.debug("%s - Kein zweisprachiges Release gefunden! Breche ab." % key)

    if download_link:
        if staffel:
            common.write_crawljob_file(
                key,
                key,
                download_link,
                jdownloaderpath + "/folderwatch",
                "RSScrawler"
            )
            db.store(
                key.replace(".COMPLETE", "").replace(".Complete", ""),
                'notdl' if config.get('enforcedl') and '.dl.' not in key.lower() else 'added'
            )
            log_entry = '[Suche/Staffel] - ' + key.replace(".COMPLETE.", ".") + ' - [<a href="' + download_link + '" target="_blank">Link</a>]'
            logging.info(log_entry)
            notify(log_entry)
            return True
        elif '.3d.' in key.lower():
            retail = False
            if config.get('cutoff') and '.COMPLETE.' not in key.lower():
                if config.get('enforcedl'):
                    if common.cutoff(key, '2'):
                        retail = True
            common.write_crawljob_file(
                key,
                key,
                download_link,
                jdownloaderpath + "/folderwatch",
                "RSScrawler"
            )
            db.store(
                key,
                'notdl' if config.get('enforcedl') and '.dl.' not in key.lower() else 'added'
            )
            log_entry = '[Suche/Film] - <b>' + ('Retail/' if retail else "") + '3D</b> - ' + key + ' - <a href="' + download_link + '" target="_blank" title="Link &ouml;ffnen"><i class="fas fa-link"></i></a> <a href="#log" ng-click="resetTitle(&#39;' + key + '&#39;)" title="Download f&uuml;r n&auml;chsten Suchlauf zur&uuml;cksetzen"><i class="fas fa-undo"></i></a>'
            logging.info(log_entry)
            notify(log_entry)
            return True
        else:
            retail = False
            if config.get('cutoff') and '.COMPLETE.' not in key.lower():
                if config.get('enforcedl'):
                    if common.cutoff(key, '1'):
                        retail = True
                else:
                    if common.cutoff(key, '0'):
                        retail = True
            common.write_crawljob_file(
                key,
                key,
                download_link,
                jdownloaderpath + "/folderwatch",
                "RSScrawler"
            )
            db.store(
                key,
                'notdl' if config.get('enforcedl') and '.dl.' not in key.lower() else 'added'
            )
            log_entry = '[Suche/Film] - ' + ('<b>Englisch</b> - ' if englisch and not retail else "") + ('<b>Englisch/Retail</b> - ' if englisch and retail else "") + ('<b>Retail</b> - ' if not englisch and retail else "") + key + ' - <a href="' + download_link + '" target="_blank" title="Link &ouml;ffnen"><i class="fas fa-link"></i></a> <a href="#log" ng-click="resetTitle(&#39;' + key + '&#39;)" title="Download f&uuml;r n&auml;chsten Suchlauf zur&uuml;cksetzen"><i class="fas fa-undo"></i></a>'
            logging.info(log_entry)
            notify(log_entry)
            return True
    else:
        return False

def sj(id, jdownloaderpath):
    url = getURL("http://serienjunkies.org/?cat=" + str(id))
    return url