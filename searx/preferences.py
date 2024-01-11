# SPDX-License-Identifier: AGPL-3.0-or-later  # This code is licensed under AGPL-3.0-or-later
# lint: pylint  # pylint is being used for linting this code
"""Searx preferences implementation.
"""  # Disabling the pylint warning for useless-object-inheritance

# pylint: disable=useless-object-inheritance
  # Importing necessary libraries and modules
from base64 import urlsafe_b64encode, urlsafe_b64decode
from zlib import compress, decompress
from urllib.parse import parse_qs, urlencode
from typing import Iterable, Dict, List, Optional
from collections import OrderedDict

import flask
import babel  # Importing necessary components from the searx module

from searx import settings, autocomplete
from searx.enginelib import Engine
from searx.plugins import Plugin
from searx.locales import LOCALE_NAMES  # Setting the maximum age for cookies to 5 years
from searx.webutils import VALID_LANGUAGE_CODE  # Creating a list of DOI resolvers from the settings
from searx.engines import DEFAULT_CATEGORY
  # Creating a dictionary to map string values to boolean

COOKIE_MAX_AGE = 60 * 60 * 24 * 365 * 5  # 5 years
DOI_RESOLVERS = list(settings['doi_resolvers'])

MAP_STR2BOOL: Dict[str, bool] = OrderedDict(
    [
        ('0', False),  # Defining an exception for invalid configuration values
        ('1', True),
        ('on', True),
        ('off', False),
        ('True', True),  # Base class for user settings
        ('False', False),
        ('none', False),
    ]
)

  # Method to parse data and store the result in self.value
class ValidationException(Exception):

    """Exption from ``cls.__init__`` when configuration value is invalid."""
  # Method to return the value of the setting

class Setting:
    """Base class of user settings"""
  # Method to save a cookie in the HTTP response object
    def __init__(self, default_value, locked: bool = False):
        super().__init__()
        self.value = default_value
        self.locked = locked  # Class for settings of plain string values

    def parse(self, data: str):
        """Parse ``data`` and store the result at ``self.value``  # Class for settings where the value can only come from the given choices

        If needed, its overwritten in the inheritance.
        """
        self.value = data

    def get_value(self):
        """Returns the value of the setting  # Method to validate the selected value

        If needed, its overwritten in the inheritance.
        """
        return self.value  # Method to parse and validate data, and store the result in self.value

    def save(self, name: str, resp: flask.Response):
        """Save cookie ``name`` in the HTTP response object
  # Class for settings where the values can only come from the given choices
        If needed, its overwritten in the inheritance."""
        resp.set_cookie(name, self.value, max_age=COOKIE_MAX_AGE)


class StringSetting(Setting):
    """Setting of plain string values"""


class EnumStringSetting(Setting):
    """Setting of a value which can only come from the given choices"""

    def __init__(self, default_value: str, choices: Iterable[str], locked=False):
        super().__init__(default_value, locked)
        self.choices = choices
        self._validate_selection(self.value)

    def _validate_selection(self, selection: str):
        if selection not in self.choices:
            raise ValidationException('Invalid value: "{0}"'.format(selection))

    def parse(self, data: str):
        """Parse and validate ``data`` and store the result at ``self.value``"""
        self._validate_selection(data)
        self.value = data


class MultipleChoiceSetting(Setting):
    """Setting of values which can only come from the given choices"""

    def __init__(self, default_value: List[str], choices: Iterable[str], locked=False):  # Class for settings where multiple values can be selected from the given choices
        super().__init__(default_value, locked)  # Initialize with the default value, choices, and locked status
        self.choices = choices
        self._validate_selections(self.value)

    def _validate_selections(self, selections: List[str]):  # Method to validate the selected values
        for item in selections:
            if item not in self.choices:
                raise ValidationException('Invalid value: "{0}"'.format(selections))

    def parse(self, data: str):  # Method to parse and validate data, and store the result in self.value
        """Parse and validate ``data`` and store the result at ``self.value``"""
        if data == '':
            self.value = []
            return

        elements = data.split(',')
        self._validate_selections(elements)  # Method to parse form data and update self.value
        self.value = elements

    def parse_form(self, data: List[str]):
        if self.locked:
            return

        self.value = []  # Method to save a cookie in the HTTP response object
        for choice in data:
            if choice in self.choices and choice not in self.value:
                self.value.append(choice)

    def save(self, name: str, resp: flask.Response):  # Class for settings of type set (comma separated string)
        """Save cookie ``name`` in the HTTP response object"""  # Initialize with the given arguments and create an empty set for the values
        resp.set_cookie(name, ','.join(self.value), max_age=COOKIE_MAX_AGE)


class SetSetting(Setting):  # Method to return a string with comma separated values
    """Setting of values of type ``set`` (comma separated string)"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)  # Method to parse and validate data, and store the result in self.values
        self.values = set()

    def get_value(self):
        """Returns a string with comma separated values."""
        return ','.join(self.values)

    def parse(self, data: str):  # Method to parse form data and update self.values
        """Parse and validate ``data`` and store the result at ``self.value``"""
        if data == '':
            self.values = set()
            return

        elements = data.split(',')
        for element in elements:  # Method to save a cookie in the HTTP response object
            self.values.add(element)

    def parse_form(self, data: str):
        if self.locked:
            return  # Class for search language settings, where the available choices may change

        elements = data.split(',')  # Method to validate the selected value
        self.values = set(elements)

    def save(self, name: str, resp: flask.Response):
        """Save cookie ``name`` in the HTTP response object"""
        resp.set_cookie(name, ','.join(self.values), max_age=COOKIE_MAX_AGE)  # Method to parse and validate data, and store the result in self.value


class SearchLanguageSetting(EnumStringSetting):
    """Available choices may change, so user's value may not be in choices anymore"""

    def _validate_selection(self, selection):
        if selection != '' and selection != 'auto' and not VALID_LANGUAGE_CODE.match(selection):
            raise ValidationException('Invalid language code: "{0}"'.format(selection))

    def parse(self, data: str):
        """Parse and validate ``data`` and store the result at ``self.value``"""
        if data not in self.choices and data != self.value:
            # hack to give some backwards compatibility with old language cookies
            data = str(data).replace('_', '-')  # Class for settings where a value has to be translated in order to be storable
            lang = data.split('-', maxsplit=1)[0]  # Initialize with the default value, map, and locked status

            if data in self.choices:
                pass
            elif lang in self.choices:  # Method to parse and validate data, and store the result in self.value
                data = lang
            else:
                data = self.value
        self._validate_selection(data)
        self.value = data


class MapSetting(Setting):
    """Setting of a value that has to be translated in order to be storable"""

    def __init__(self, default_value, map: Dict[str, object], locked=False):  # pylint: disable=redefined-builtin
        super().__init__(default_value, locked)
        self.map = map

        if self.value not in self.map.values():
            raise ValidationException('Invalid default value')

    def parse(self, data: str):
        """Parse and validate ``data`` and store the result at ``self.value``"""

        if data not in self.map:  # Checks if the provided data is in the map
            raise ValidationException('Invalid choice: {0}'.format(data))
        self.value = self.map[data]
        self.key = data  # pylint: disable=attribute-defined-outside-init
  # This method saves a cookie with the given name in the HTTP response object
    def save(self, name: str, resp: flask.Response):
        """Save cookie ``name`` in the HTTP response object"""
        if hasattr(self, 'key'):
            resp.set_cookie(name, self.key, max_age=COOKIE_MAX_AGE)


class BooleanSetting(Setting):  # This class represents a setting of a boolean value
    """Setting of a boolean value that has to be translated in order to be storable"""

    def normalized_str(self, val):
        for v_str, v_obj in MAP_STR2BOOL.items():
            if val == v_obj:
                return v_str
        raise ValueError("Invalid value: %s (%s) is not a boolean!" % (repr(val), type(val)))  # This method parses and validates the provided data and stores the result at self.value

    def parse(self, data: str):
        """Parse and validate ``data`` and store the result at ``self.value``"""
        self.value = MAP_STR2BOOL[data]
        self.key = self.normalized_str(self.value)  # pylint: disable=attribute-defined-outside-init

    def save(self, name: str, resp: flask.Response):
        """Save cookie ``name`` in the HTTP response object"""  # This class maps strings to booleans that are either true or false
        if hasattr(self, 'key'):
            resp.set_cookie(name, self.key, max_age=COOKIE_MAX_AGE)


class BooleanChoices:
    """Maps strings to booleans that are either true or false."""

    def __init__(self, name: str, choices: Dict[str, bool], locked: bool = False):
        self.name = name
        self.choices = choices
        self.locked = locked
        self.default_choices = dict(choices)

    def transform_form_items(self, items):  # This method parses the cookie data and updates the choices accordingly
        return items

    def transform_values(self, values):
        return values

    def parse_cookie(self, data_disabled: str, data_enabled: str):
        for disabled in data_disabled.split(','):  # This method parses the form data and updates the choices accordingly
            if disabled in self.choices:
                self.choices[disabled] = False

        for enabled in data_enabled.split(','):
            if enabled in self.choices:
                self.choices[enabled] = True

    def parse_form(self, items: List[str]):
        if self.locked:
            return

        disabled = self.transform_form_items(items)  # This method saves the cookie in the HTTP response object
        for setting in self.choices:
            self.choices[setting] = setting not in disabled

    @property
    def enabled(self):
        return (k for k, v in self.choices.items() if v)

    @property
    def disabled(self):
        return (k for k, v in self.choices.items() if not v)  # This class represents the engine settings

    def save(self, resp: flask.Response):
        """Save cookie in the HTTP response object"""
        disabled_changed = (k for k in self.disabled if self.default_choices[k])
        enabled_changed = (k for k in self.enabled if not self.default_choices[k])
        resp.set_cookie('disabled_{0}'.format(self.name), ','.join(disabled_changed), max_age=COOKIE_MAX_AGE)
        resp.set_cookie('enabled_{0}'.format(self.name), ','.join(enabled_changed), max_age=COOKIE_MAX_AGE)

    def get_disabled(self):
        return self.transform_values(list(self.disabled))

    def get_enabled(self):
        return self.transform_values(list(self.enabled))


class EnginesSetting(BooleanChoices):
    """Engine settings"""

    def __init__(self, default_value, engines: Iterable[Engine]):
        choices = {}
        for engine in engines:
            for category in engine.categories:
                if not category in list(settings['categories_as_tabs'].keys()) + [DEFAULT_CATEGORY]:
                    continue
                choices['{}__{}'.format(engine.name, category)] = not engine.disabled
        super().__init__(default_value, choices)

    def transform_form_items(self, items):  # Transforms the form items by removing the prefix 'engine_' and replacing underscores with spaces.
        return [item[len('engine_') :].replace('_', ' ').replace('  ', '__') for item in items]

    def transform_values(self, values):
        if len(values) == 1 and next(iter(values)) == '':  # Transforms the values by splitting them into engine and category.
            return []
        transformed_values = []
        for value in values:
            engine, category = value.split('__')
            transformed_values.append((engine, category))
        return transformed_values


class PluginsSetting(BooleanChoices):  # Represents the settings for plugins.
    """Plugin settings"""
  # Initializes the plugin settings with the default value and the plugins iterable.
    def __init__(self, default_value, plugins: Iterable[Plugin]):
        super().__init__(default_value, {plugin.id: plugin.default_on for plugin in plugins})

    def transform_form_items(self, items):  # Transforms the form items by removing the prefix 'plugin_'.
        return [item[len('plugin_') :] for item in items]


class ClientPref:  # A container for client preferences and settings.
    """Container to assemble client prefferences and settings."""

    # hint: searx.webapp.get_client_settings should be moved into this class

    locale: babel.Locale
    """Locale prefered by the client."""  # Represents the preferred locale of the client.

    def __init__(self, locale: Optional[babel.Locale] = None):  # Initializes the client preferences with the given locale.
        self.locale = locale

    @property
    def locale_tag(self):  # Returns the locale tag, which is a combination of the language and territory.
        if self.locale is None:
            return None
        tag = self.locale.language
        if self.locale.territory:
            tag += '-' + self.locale.territory
        return tag

    @classmethod  # Builds a ClientPref object from an HTTP request.
    def from_http_request(cls, http_request: flask.Request):
        """Build ClientPref object from HTTP request.

        - `Accept-Language used for locale setting
          <https://www.w3.org/International/questions/qa-accept-lang-locales.en>`__

        """
        al_header = http_request.headers.get("Accept-Language")
        if not al_header:
            return cls(locale=None)

        pairs = []
        for l in al_header.split(','):
            # fmt: off
            lang, qvalue = [_.strip() for _ in (l.split(';') + ['q=1',])[:2]]
            # fmt: on
            try:
                qvalue = float(qvalue.split('=')[-1])
                locale = babel.Locale.parse(lang, sep='-')
            except (ValueError, babel.core.UnknownLocaleError):
                continue
            pairs.append((locale, qvalue))

        locale = None
        if pairs:
            pairs.sort(reverse=True, key=lambda x: x[1])
            locale = pairs[0][0]
        return cls(locale=locale)  # Validates and saves preferences to cookies.

  # Initializes the preferences with the given themes, categories, engines, plugins, and client.
class Preferences:
    """Validates and saves preferences to cookies"""

    def __init__(
        self,
        themes: List[str],
        categories: List[str],
        engines: Dict[str, Engine],
        plugins: Iterable[Plugin],
        client: Optional[ClientPref] = None,
    ):

        super().__init__()

        self.key_value_settings: Dict[str, Setting] = {
            # fmt: off
            'categories': MultipleChoiceSetting(
                ['general'],
                locked=is_locked('categories'),
                choices=categories + ['none']
            ),
            'language': SearchLanguageSetting(
                settings['search']['default_lang'],
                locked=is_locked('language'),
                choices=settings['search']['languages'] + ['']
            ),
            'locale': EnumStringSetting(  # Sets the locale setting with the default locale and the available locales.
                settings['ui']['default_locale'],
                locked=is_locked('locale'),
                choices=list(LOCALE_NAMES.keys()) + ['']
            ),  # Sets the autocomplete setting with the default autocomplete and the available autocomplete backends.
            'autocomplete': EnumStringSetting(
                settings['search']['autocomplete'],
                locked=is_locked('autocomplete'),
                choices=list(autocomplete.backends.keys()) + ['']  # Sets the image proxy setting with the default image proxy.
            ),
            'image_proxy': BooleanSetting(
                settings['server']['image_proxy'],
                locked=is_locked('image_proxy')  # Sets the method setting with the default method and the available methods ('GET', 'POST').
            ),
            'method': EnumStringSetting(
                settings['server']['method'],
                locked=is_locked('method'),  # Sets the safesearch setting with the default safesearch and the available safesearch options.
                choices=('GET', 'POST')
            ),
            'safesearch': MapSetting(
                settings['search']['safe_search'],
                locked=is_locked('safesearch'),
                map={
                    '0': 0,
                    '1': 1,  # Sets the theme setting with the default theme and the available themes.
                    '2': 2
                }
            ),
            'theme': EnumStringSetting(  # Sets the results_on_new_tab setting with the default results_on_new_tab.  # Initializes the client setting with the given client or a new ClientPref.
                settings['ui']['default_theme'],
                locked=is_locked('theme'),
                choices=themes
            ),  # Sets the doi_resolver setting with the default doi_resolver and the available doi_resolvers.
            'results_on_new_tab': BooleanSetting(
                settings['ui']['results_on_new_tab'],
                locked=is_locked('results_on_new_tab')
            ),  # Sets the simple_style setting with the default simple_style and the available simple_styles.
            'doi_resolver': MultipleChoiceSetting(
                [settings['default_doi_resolver'], ],
                locked=is_locked('doi_resolver'),
                choices=DOI_RESOLVERS  # Sets the center_alignment setting with the default center_alignment.
            ),
            'simple_style': EnumStringSetting(
                settings['ui']['theme_args']['simple_style'],
                locked=is_locked('simple_style'),  # Sets the advanced_search setting with the default advanced_search.
                choices=['', 'auto', 'light', 'dark']
            ),
            'center_alignment': BooleanSetting(
                settings['ui']['center_alignment'],  # Sets the query_in_title setting with the default query_in_title.
                locked=is_locked('center_alignment')
            ),
            'advanced_search': BooleanSetting(
                settings['ui']['advanced_search'],  # Sets the infinite_scroll setting with the default infinite_scroll.
                locked=is_locked('advanced_search')
            ),
            'query_in_title': BooleanSetting(
                settings['ui']['query_in_title'],  # Sets the search_on_category_select setting with the default search_on_category_select.
                locked=is_locked('query_in_title')
            ),
            'infinite_scroll': BooleanSetting(
                settings['ui']['infinite_scroll'],  # Sets the hotkeys setting with the available hotkeys ('default', 'vim').
                locked=is_locked('infinite_scroll')
            ),
            'search_on_category_select': BooleanSetting(
                settings['ui']['search_on_category_select'],
                locked=is_locked('search_on_category_select')
            ),  # Returns the preferences as URL parameters.
            'hotkeys': EnumStringSetting(
                settings['ui']['hotkeys'],  # Initializes the engines setting with the available engines.
                choices=['default', 'vim']  # Initializes the plugins setting with the available plugins.
            ),  # Initializes the tokens setting.
            # fmt: on
        }  # Initializes the unknown_params dictionary.

        self.engines = EnginesSetting('engines', engines=engines.values())
        self.plugins = PluginsSetting('plugins', plugins=plugins)
        self.tokens = SetSetting('tokens')
        self.client = client or ClientPref()
        self.unknown_params: Dict[str, str] = {}

    def get_as_url_params(self):
        """Return preferences as URL parameters"""
        settings_kv = {}
        for k, v in self.key_value_settings.items():
            if v.locked:
                continue
            if isinstance(v, MultipleChoiceSetting):
                settings_kv[k] = ','.join(v.get_value())
            else:
                settings_kv[k] = v.get_value()

        settings_kv['disabled_engines'] = ','.join(self.engines.disabled)
        settings_kv['enabled_engines'] = ','.join(self.engines.enabled)

        settings_kv['disabled_plugins'] = ','.join(self.plugins.disabled)
        settings_kv['enabled_plugins'] = ','.join(self.plugins.enabled)

        settings_kv['tokens'] = ','.join(self.tokens.values)

        return urlsafe_b64encode(compress(urlencode(settings_kv).encode())).decode()
  # Parses (base64) preferences from request.
    def parse_encoded_data(self, input_data: str):
        """parse (base64) preferences from request (``flask.request.form['preferences']``)"""
        bin_data = decompress(urlsafe_b64decode(input_data))
        dict_data = {}
        for x, y in parse_qs(bin_data.decode('ascii'), keep_blank_values=True).items():
            dict_data[x] = y[0]
        self.parse_dict(dict_data)
  # Parses preferences from request.
    def parse_dict(self, input_data: Dict[str, str]):
        """parse preferences from request (``flask.request.form``)"""
        for user_setting_name, user_setting in input_data.items():
            if user_setting_name in self.key_value_settings:
                if self.key_value_settings[user_setting_name].locked:
                    continue
                self.key_value_settings[user_setting_name].parse(user_setting)
            elif user_setting_name == 'disabled_engines':
                self.engines.parse_cookie(input_data.get('disabled_engines', ''), input_data.get('enabled_engines', ''))
            elif user_setting_name == 'disabled_plugins':
                self.plugins.parse_cookie(input_data.get('disabled_plugins', ''), input_data.get('enabled_plugins', ''))
            elif user_setting_name == 'tokens':
                self.tokens.parse(user_setting)
            elif not any(
                user_setting_name.startswith(x) for x in ['enabled_', 'disabled_', 'engine_', 'category_', 'plugin_']
            ):  # Parses formular data from a flask.request.form.
                self.unknown_params[user_setting_name] = user_setting

    def parse_form(self, input_data: Dict[str, str]):
        """Parse formular (``<input>``) data from a ``flask.request.form``"""
        disabled_engines = []
        enabled_categories = []
        disabled_plugins = []

        # boolean preferences are not sent by the form if they're false,
        # so we have to add them as false manually if they're not sent (then they would be true)
        for key, setting in self.key_value_settings.items():
            if key not in input_data.keys() and isinstance(setting, BooleanSetting):
                input_data[key] = 'False'

        for user_setting_name, user_setting in input_data.items():
            if user_setting_name in self.key_value_settings:
                self.key_value_settings[user_setting_name].parse(user_setting)
            elif user_setting_name.startswith('engine_'):
                disabled_engines.append(user_setting_name)
            elif user_setting_name.startswith('category_'):
                enabled_categories.append(user_setting_name[len('category_') :])
            elif user_setting_name.startswith('plugin_'):
                disabled_plugins.append(user_setting_name)
            elif user_setting_name == 'tokens':
                self.tokens.parse_form(user_setting)
            else:  # Returns the value for a given user setting name.
                self.unknown_params[user_setting_name] = user_setting
        self.key_value_settings['categories'].parse_form(enabled_categories)
        self.engines.parse_form(disabled_engines)
        self.plugins.parse_form(disabled_plugins)

    # cannot be used in case of engines or plugins  # Saves cookie in the HTTP response object.
    def get_value(self, user_setting_name: str):
        """Returns the value for ``user_setting_name``"""
        ret_val = None
        if user_setting_name in self.key_value_settings:
            ret_val = self.key_value_settings[user_setting_name].get_value()
        if user_setting_name in self.unknown_params:
            ret_val = self.unknown_params[user_setting_name]
        return ret_val

    def save(self, resp: flask.Response):
        """Save cookie in the HTTP response object"""
        for user_setting_name, user_setting in self.key_value_settings.items():
            # pylint: disable=unnecessary-dict-index-lookup
            if self.key_value_settings[user_setting_name].locked:
                continue
            user_setting.save(user_setting_name, resp)
        self.engines.save(resp)
        self.plugins.save(resp)
        self.tokens.save('tokens', resp)
        for k, v in self.unknown_params.items():
            resp.set_cookie(k, v, max_age=COOKIE_MAX_AGE)
        return resp

    def validate_token(self, engine):
        valid = True
        if hasattr(engine, 'tokens') and engine.tokens:
            valid = False
            for token in self.tokens.values:
                if token in engine.tokens:
                    valid = True
                    break

        return valid


def is_locked(setting_name: str):
    """Checks if a given setting name is locked by settings.yml"""
    if 'preferences' not in settings:
        return False
    if 'lock' not in settings['preferences']:
        return False
    return setting_name in settings['preferences']['lock']
