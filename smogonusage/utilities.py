"""Common utilities used across the package"""
import collections
import json
import re

from smogonusage import scrapers


class Sanitizer(object):

    filter_regex = re.compile('[\W_]+')  # Translation: any non-"word" character
                                         # or "_"

    def __init__(self, pokedex=None, aliases=None):
        """
        An object which normalizes inputs to ensure consistency, removing or
        replacing invalid characters and de-aliasing

        Args:
            pokedex (Optional(dict)): the Pokedex to use (if none is specified
                will attempt to load from file, and if the file doesn't exist
                will scrape it from the Pokemon Showdown github)
            aliases (Optional(dict)): the aliases used by Pokemon Showdown (if
                none is specified will attempt to load from file, and if the
                file doesn't exist will scrape it from the Pokemon Showdown
                github)
        """
        if pokedex is None:
            try:
                pokedex = json.load(open('resources/pokedex.json'))
            except FileNotFoundError:
                pokedex = scrapers.scrape_battle_pokedex()

        if aliases is None:
            try:
                aliases = json.load(open('resources/aliases.json'))
            except FileNotFoundError:
                aliases = scrapers.scrape_battle_aliases()

        self.aliases = aliases.copy()
        for pokemon in pokedex.keys():
            if 'otherForms' in pokedex[pokemon].keys():
                for form in pokedex[pokemon]['otherForms']:
                    self.aliases[self._sanitize_string(form)] = pokemon

    def sanitize(self, input_object):
        """
        Sanitizes the given object, sorting it, removing or replacing invalid
        characters, and de-aliasing, as required
        Args:
            input_object (object): the object to sanitize

        Returns:
            object: the sanitized object, of the same type as the input

        Raises:
            TypeError: if the type of the ``input_object`` is not supported

        Examples:
            >>> from smogonusage import utilities
            >>> sanitizer = utilities.Sanitizer()
            >>> sanitizer.sanitize('Wormadam-Trash')
            'wormadamtrash'
            >>> sanitizer.sanitize(['Volt Switch', 'Thunder', 'Giga Drain',
            ... 'Web'])
            ['gigadrain', 'stickyweb', 'thunder', 'voltswitch']
        """
        if input_object is None:
            sanitized = input_object
        elif isinstance(input_object, str):
            sanitized = self._sanitize_string(input_object)
            if sanitized in self.aliases.keys():
                sanitized = self._sanitize_string(self.aliases[sanitized])
        elif isinstance(input_object, dict):
            sanitized = dict()
            for key in input_object.keys():
                try:
                    sanitized[key] = self.sanitize(input_object[key])
                except TypeError:  # if the value can't be sanitized, leave it
                    sanitized[key] = input_object[key]
        elif isinstance(input_object, collections.Iterable):
            sanitized = sorted([self.sanitize(item) for item in input_object])
        else:
            raise TypeError("Sanitizer: cannot sanitize {0}"
                            .format(type(input_object)))
        return sanitized

    @classmethod
    def _sanitize_string(cls, input_string):
        """
        Strips all non-alphanumeric characters and puts everything in lowercase

        Args:
            input_string (str): string to be sanitized

        Returns:
            str: the sanitized string

        """
        return cls.filter_regex.sub('', input_string).lower()
