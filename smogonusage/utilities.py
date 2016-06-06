"""Common utilities used across the package"""
from __future__ import print_function
import collections
import hashlib
import json
import re
import six

from smogonusage.dto import PokeStats, Moveset
from smogonusage import scrapers


class Sanitizer(object):

    filter_regex = re.compile('[\W_]+')  # Translation: any non-"word" character
                                         # or "_"

    def __init__(self, pokedex=None, aliases=None):
        """
        An object which normalizes inputs to ensure consistency, removing or
        replacing invalid characters and de-aliasing

        Args:
            pokedex (Optional(dict)): the Pokedex to use. If none is specified
                will attempt to load from file, and if the file doesn't exist
                will scrape it from the Pokemon Showdown github
            aliases (Optional(dict)): the aliases used by Pokemon Showdown. If
                none is specified will attempt to load from file, and if the
                file doesn't exist will scrape it from the Pokemon Showdown
                github
        """
        if pokedex is None:
            try:
                pokedex = json.load(open('resources/pokedex.json'))
            except IOError:
                pokedex = scrapers.scrape_battle_pokedex()

        if aliases is None:
            try:
                aliases = json.load(open('resources/aliases.json'))
            except IOError:
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
            >>> sanitizer.sanitize(['Volt Switch', 'Thunder', 'Giga Drain'
            ... , 'Web'])
            ['gigadrain', 'stickyweb', 'thunder', 'voltswitch']
        """
        if input_object is None:
            sanitized = input_object

        elif isinstance(input_object, str):
            sanitized = self._sanitize_string(input_object)
            if sanitized in self.aliases.keys():
                sanitized = self._sanitize_string(self.aliases[sanitized])
                if six.PY2:
                    sanitized = sanitized.encode('ascii')

        elif isinstance(input_object, Moveset):
            sanitized_dict = self.sanitize(input_object._asdict())
            sanitized = Moveset(**sanitized_dict)

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


def compute_sid(moveset, sanitizer=None):
    """
    Computes the Set ID for the given moveset

    Args:
        moveset (Moveset): the moveset to compute the SID for
        sanitizer (Optional(Sanitizer)): if no sanitizer is provided,
            ``moveset`` is assumed to be already sanitized. Otherwise, the
            provided ``Sanitizer`` is used to sanitize the moveset.

    Returns:
        the corresponding Set ID

    Examples
        >>> from smogonusage.dto import PokeStats, Moveset
        >>> from smogonusage import utilities
        >>> moveset = Moveset('Mamoswine', 'Thick Fat', 'F', 'Life Orb',
        ... ['Ice Shard', 'Icicle Crash', 'Earthquake', 'Superpower'],
        ... PokeStats(361,394,197,158,156,259), 100, 255)
        >>> equivalent = Moveset('mamo', 'thickfat', 'f', 'lorb',
        ... ['eq', 'IcicleCrash', 'superpower', 'iceshard'],
        ... PokeStats(361,394,197,158,156,259), 100, 255)
        >>> different = Moveset('mamo', 'thickfat', 'f', 'focus sash',
        ... ['eq', 'IcicleCrash', 'superpower', 'iceshard'],
        ... PokeStats(361,394,197,158,156,259), 100, 255)
        >>> sanitizer=utilities.Sanitizer()
        >>> moveset_sid = utilities.compute_sid(moveset, sanitizer)
        >>> moveset_sid # doctest: +ELLIPSIS
        'mamoswine-4a0b...'
        >>> equivalent_sid = utilities.compute_sid(equivalent, sanitizer)
        >>> equivalent_sid
        'mamoswine-4a0b...'
        >>> different_sid = utilities.compute_sid(different, sanitizer)
        >>> different_sid
        'mamoswine-bb16...'
        >>> moveset_sid == equivalent_sid
        True
        >>> moveset_sid == different_sid
        False
    """
    if sanitizer is not None:
        moveset = sanitizer.sanitize(moveset)

    moveset_hash = hashlib.sha512(repr(moveset).encode('utf-8')).hexdigest()

    # may eventually want to truncate hash, e.g.
    # moveset_hash = moveset_hash[:16]

    return '{0}-{1}'.format(moveset.species,moveset_hash)


def stats_dict_to_dto(stats_dict):
    """
    Converts a Pokemon Showdown-style stats ``dict`` to a ``PokeStats`` DTO

    Args:
        stats_dict (dict): the object to convert

    Returns:
        PokeStats: the converted object

    Raises:
        TypeError: if ``stats_dict`` doesn't have the correct keys

    Examples:
        >>> from smogonusage import utilities
        >>> utilities.stats_dict_to_dto({'hp': 361, 'atk': 394, 'def': 197,
        ... 'spa': 158, 'spd' : 156, 'spe': 259})
        PokeStats(hp=361, atk=394, dfn=197, spa=158, spd=156, spe=259)
    """
    stats_dict['dfn'] = stats_dict.pop('def')
    return PokeStats(**stats_dict)
