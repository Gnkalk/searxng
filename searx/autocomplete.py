# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""This module implements functions needed for the autocompleter.

"""
# pylint: disable=use-dict-literal

import json
from urllib.parse import urlencode

import lxml
from httpx import HTTPError

from searx import settings
from searx.engines import (
    engines,
    google,
)
from searx.network import get as http_get
from searx.exceptions import SearxEngineResponseException

# This function is a wrapper around the http_get function from the searx.network module.
# It sets a default timeout and raises an error for HTTP errors.
def get(*args, **kwargs):
    if 'timeout' not in kwargs:
        kwargs['timeout'] = settings['outgoing']['request_timeout']
    kwargs['raise_for_httperror'] = True
    return http_get(*args, **kwargs)

# This function uses the Brave search engine's suggest API to get autocomplete suggestions.
def brave(query, _lang):
    url = 'https://search.brave.com/api/suggest?'
    url += urlencode({'q': query})
    country = 'all'
    kwargs = {'cookies': {'country': country}}
    resp = get(url, **kwargs)

    results = []

    if resp.ok:
        data = resp.json()
        for item in data[1]:
            results.append(item)
    return results

# This function uses the DBpedia lookup API to get autocomplete suggestions.
def dbpedia(query, _lang):
    autocomplete_url = 'https://lookup.dbpedia.org/api/search.asmx/KeywordSearch?'

    response = get(autocomplete_url + urlencode(dict(QueryString=query)))

    results = []

    if response.ok:
        dom = lxml.etree.fromstring(response.content)
        results = dom.xpath('//Result/Label//text()')

    return results

# This function uses the DuckDuckGo autocomplete API to get autocomplete suggestions.
def duckduckgo(query, sxng_locale):
    traits = engines['duckduckgo'].traits
    args = {
        'q': query,
        'kl': traits.get_region(sxng_locale, traits.all_locale),
    }

    url = 'https://duckduckgo.com/ac/?type=list&' + urlencode(args)
    resp = get(url)

    ret_val = []
    if resp.ok:
        j = resp.json()
        if len(j) > 1:
            ret_val = j[1]
    return ret_val

# This function uses the Google autocomplete API to get autocomplete suggestions.
def google_complete(query, sxng_locale):
    google_info = google.get_google_info({'searxng_locale': sxng_locale}, engines['google'].traits)

    url = 'https://{subdomain}/complete/search?{args}'
    args = urlencode(
        {
            'q': query,
            'client': 'gws-wiz',
            'hl': google_info['params']['hl'],
        }
    )
# This function uses the Google autocomplete API to get autocomplete suggestions.
# It formats the URL with the subdomain and arguments, sends a GET request,
# and if the response is OK, it processes the JSON text in the response.
# It then appends the text content of each item in the data to the results list.
results = []
resp = get(url.format(subdomain=google_info['subdomain'], args=args))
if resp.ok:
    json_txt = resp.text[resp.text.find('[') : resp.text.find(']', -3) + 1]
    data = json.loads(json_txt)
    for item in data[0]:
        results.append(lxml.html.fromstring(item[0]).text_content())
return results

# This function uses the Mwmbl autocomplete API to get autocomplete suggestions.
# It formats the URL with the query, sends a GET request, and processes the JSON in the response.
# It filters out results that start with "go: " or "search: " as they are not useful for auto completion.
def mwmbl(query, _lang):
    url = 'https://api.mwmbl.org/search/complete?{query}'
    results = get(url.format(query=urlencode({'q': query}))).json()[1]
    return [result for result in results if not result.startswith("go: ") and not result.startswith("search: ")]

# This function uses the Seznam search autocomplete API to get autocomplete suggestions.
# It formats the URL with the query and other parameters, sends a GET request, and processes the JSON in the response.
# It returns a list of text results where the item type is 'ItemType.TEXT'.
def seznam(query, _lang):
    url = 'https://suggest.seznam.cz/fulltext/cs?{query}'
    resp = get(
        url.format(
            query=urlencode(
                {'phrase': query, 'cursorPosition': len(query), 'format': 'json-2', 'highlight': '1', 'count': '6'}
            )
        )
    )
    if not resp.ok:
        return []
    data = resp.json()
    return [
        ''.join([part.get('text', '') for part in item.get('text', [])])
        for item in data.get('result', [])
        if item.get('itemType', None) == 'ItemType.TEXT'
    ]

# This function uses the Startpage autocomplete API to get autocomplete suggestions.
# It formats the URL with the query and other parameters, sends a GET request, and processes the JSON in the response.
# It returns a list of text results.
def startpage(query, sxng_locale):
    lui = engines['startpage'].traits.get_language(sxng_locale, 'english')
    url = 'https://startpage.com/suggestions?{query}'
    resp = get(url.format(query=urlencode({'q': query, 'segment': 'startpage.udog', 'lui': lui})))
    data = resp.json()
    return [e['text'] for e in data.get('suggestions', []) if 'text' in e]

# This function uses the Swisscows autocomplete API to get autocomplete suggestions.
# It formats the URL with the query, sends a GET request, and processes the JSON text in the response.
def swisscows(query, _lang):
    url = 'https://swisscows.ch/api/suggest?{query}&itemsCount=5'
    resp = json.loads(get(url.format(query=urlencode({'query': query}))).text)
    return resp

# This function uses the Qwant autocomplete API to get autocomplete suggestions.
# It formats the URL with the query and other parameters, sends a GET request, and processes the JSON in the response.
# It returns a list of value results where the status is 'success'.
def qwant(query, sxng_locale):
    results = []
    locale = engines['qwant'].traits.get_region(sxng_locale, 'en_US')
    url = 'https://api.qwant.com/v3/suggest?{query}'
    resp = get(url.format(query=urlencode({'q': query, 'locale': locale, 'version': '2'})))
    if resp.ok:
        data = resp.json()
        if data['status'] == 'success':
            for item in data['data']['items']:
                results.append(item['value'])
    return results

# This function uses the Wikipedia autocomplete API to get autocomplete suggestions.
# It formats the URL with the query and other parameters, sends a GET request, and processes the JSON in the response.
# It returns a list of results.
def wikipedia(query, sxng_locale):
    results = []
    eng_traits = engines['wikipedia'].traits
    wiki_lang = eng_traits.get_language(sxng_locale, 'en')
    wiki_netloc = eng_traits.custom['wiki_netloc'].get(wiki_lang, 'en.wikipedia.org')
    url = 'https://{wiki_netloc}/w/api.php?{args}'
    args = urlencode(
        {
            'action': 'opensearch',
            'format': 'json',
            'formatversion': '2',
            'search': query,
            'namespace': '0',
            'limit': '10',
        }
    )
    resp = get(url.format(args=args, wiki_netloc=wiki_netloc))
    if resp.ok:
        data = resp.json()
        if len(data) > 1:
            results = data[1]
    return results

# This function uses the Yandex autocomplete API to get autocomplete suggestions.
# The URL is formatted with the query.
def yandex(query, _lang):
    url = "https://suggest.yandex.com/suggest-ff.cgi?{0}"
# This function sends a GET request to the URL formatted with the query,
# processes the JSON text in the response, and returns the second item in the response if it exists.
resp = json.loads(get(url.format(urlencode(dict(part=query)))).text)
if len(resp) > 1:
    return resp[1]
return []

# This dictionary maps the names of autocomplete backends to their corresponding functions.
backends = {
    'dbpedia': dbpedia,
    'duckduckgo': duckduckgo,
    'google': google_complete,
    'mwmbl': mwmbl,
    'seznam': seznam,
    'startpage': startpage,
    'swisscows': swisscows,
    'qwant': qwant,
    'wikipedia': wikipedia,
    'brave': brave,
    'yandex': yandex,
}

# This function uses the specified backend to get autocomplete suggestions for the given query.
# If the backend is not found in the backends dictionary, it returns an empty list.
# If an HTTP error or a SearxEngineResponseException occurs, it also returns an empty list.
def search_autocomplete(backend_name, query, sxng_locale):
    backend = backends.get(backend_name)
    if backend is None:
        return []
    try:
        return backend(query, sxng_locale)
    except (HTTPError, SearxEngineResponseException):
        return []
