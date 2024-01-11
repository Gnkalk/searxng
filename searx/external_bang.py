# SPDX-License-Identifier: AGPL-3.0-or-later

from urllib.parse import quote_plus, urlparse  # `from urllib.parse import quote_plus, urlparse` - This line imports the `quote_plus` and `urlparse` functions from the `urllib.parse` module. `quote_plus` is used to URL encode the query string, and `urlparse` is used to parse the URL of the bang search.
from searx.data import EXTERNAL_BANGS  # `from searx.data import EXTERNAL_BANGS` - This line imports the `EXTERNAL_BANGS` constant from the `searx.data` module. `EXTERNAL_BANGS` is a dictionary that contains the definitions of all external bangs.

LEAF_KEY = chr(16)  # `LEAF_KEY = chr(16)` - This line defines a constant `LEAF_KEY` which is used as a key in the `external_bangs_db` dictionary to store the definition of a bang.


def get_node(external_bangs_db, bang):  # `def get_node(external_bangs_db, bang):` - This function takes the `external_bangs_db` dictionary and a `bang` string as input, and returns the node in the `external_bangs_db` trie that corresponds to the `bang`, along with the parts of the `bang` that were found in the trie (`before`) and not found in the trie (`after`).
    node = external_bangs_db['trie']
    after = ''
    before = ''
    for bang_letter in bang:
        after += bang_letter
        if after in node and isinstance(node, dict):
            node = node[after]
            before += after
            after = ''
    return node, before, after

  # `def get_bang_definition_and_ac(external_bangs_db, bang):` - This function takes the `external_bangs_db` dictionary and a `bang` string as input, and returns the definition of the `bang` and a list of autocompletions for the `bang`.
def get_bang_definition_and_ac(external_bangs_db, bang):
    node, before, after = get_node(external_bangs_db, bang)

    bang_definition = None
    bang_ac_list = []
    if after != '':
        for k in node:
            if k.startswith(after):
                bang_ac_list.append(before + k)
    elif isinstance(node, dict):
        bang_definition = node.get(LEAF_KEY)
        bang_ac_list = [before + k for k in node.keys() if k != LEAF_KEY]
    elif isinstance(node, str):
        bang_definition = node
        bang_ac_list = []
  # `def resolve_bang_definition(bang_definition, query):` - This function takes a `bang_definition` string and a `query` string as input, and returns the URL and rank of the bang search.
    return bang_definition, bang_ac_list


def resolve_bang_definition(bang_definition, query):
    url, rank = bang_definition.split(chr(1))
    if url.startswith('//'):
        url = 'https:' + url
    if query:
        url = url.replace(chr(2), quote_plus(query))
    else:
        # go to main instead of search page
        o = urlparse(url)
        url = o.scheme + '://' + o.netloc

    rank = int(rank) if len(rank) > 0 else 0  # `def get_bang_definition_and_autocomplete(bang, external_bangs_db=None):` - This function takes a `bang` string and an optional `external_bangs_db` dictionary as input, and returns the definition of the `bang` and a sorted list of autocompletions for the `bang`.
    return (url, rank)


def get_bang_definition_and_autocomplete(bang, external_bangs_db=None):
    if external_bangs_db is None:
        external_bangs_db = EXTERNAL_BANGS

    bang_definition, bang_ac_list = get_bang_definition_and_ac(external_bangs_db, bang)

    new_autocomplete = []
    current = [*bang_ac_list]
    done = set()
    while len(current) > 0:
        bang_ac = current.pop(0)
        done.add(bang_ac)

        current_bang_definition, current_bang_ac_list = get_bang_definition_and_ac(external_bangs_db, bang_ac)
        if current_bang_definition:
            _, order = resolve_bang_definition(current_bang_definition, '')
            new_autocomplete.append((bang_ac, order))
        for new_bang in current_bang_ac_list:
            if new_bang not in done and new_bang not in current:
                current.append(new_bang)  # `def get_bang_url(search_query, external_bangs_db=None):` - This function takes a `search_query` object and an optional `external_bangs_db` dictionary as input, and returns the URL of the bang search if the `search_query` contains a valid external bang, else it returns `None`.

    new_autocomplete.sort(key=lambda t: (-t[1], t[0]))
    new_autocomplete = list(map(lambda t: t[0], new_autocomplete))

    return bang_definition, new_autocomplete


def get_bang_url(search_query, external_bangs_db=None):
    """
    Redirects if the user supplied a correct bang search.
    :param search_query: This is a search_query object which contains preferences and the submitted queries.
    :return: None if the bang was invalid, else a string of the redirect url.
    """
    ret_val = None

    if external_bangs_db is None:
        external_bangs_db = EXTERNAL_BANGS

    if search_query.external_bang:
        bang_definition, _ = get_bang_definition_and_ac(external_bangs_db, search_query.external_bang)
        if bang_definition and isinstance(bang_definition, str):
            ret_val = resolve_bang_definition(bang_definition, search_query.query)[0]

    return ret_val
