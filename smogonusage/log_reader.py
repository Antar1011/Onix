"""Functionality for taking PS logs & structuring them into a desired format"""

import abc
import json

from smogonusage.dto import Moveset
from smogonusage import scrapers
from smogonusage import utilities


def _is_a_mega_forme(species, pokedex):
    """
    Determines if a species is a mega forme.

    Args:
        species (str): the species or forme name (sanitized)
        pokedex (dict): data including base stats, species abilities and forme
            info

    Returns:
        bool: True if it's a mega forme, False if it's not

    """
    if 'baseSpecies' not in pokedex[species].keys():
        return False
    if species.endswith(('mega', 'megax', 'megay', 'primal')):
        return True
    return False


class LogReader(object):
    """
    An object which takes in a Pokemon Showdown log (in whatever format it
    exists) and returned structured data, ready for compiling or storing
    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def parse_log(self, log):
        """
        Parse the provided log and return structured data

        Args:
            log: the log to parse, in whatever format the reader can parse

        Returns:
            (tuple):
                * BattleInfo: metadata about the match
                * tuple(tuple(Moveset)): the movesets used in the battle,
                    grouped by team
                * list(Matchup): list of matchups

        Raises:
            ParsingException: if there's a problem parsing the log

        """
        pass


class JsonFileLogReader(LogReader):

    def __init__(self, sanitizer=None, pokedex=None, items=None):
        """
        Parses Pokemon Showdown ``.json`` files

        Args:
            sanitizer (Optional[Sanitizer]):
                used to normalize the data read in from the log. If none is
                    specified, will create its own
            pokedex (Optional[dict]):
                data including base stats, species abilities and forme info. If
                none is specified will attempt to load from file, and if the
                file doesn't exist will scrape the data from the Pokemon
                Showdown GitHub
            items (Optional[dict]):
                used for determining mega stones. If none is specified will
                attempt to load from file, and if the file doesn't exist will
                scrape it from the Pokemon Showdown GitHub
        """
        if sanitizer is None:
            sanitizer = utilities.Sanitizer()
        if pokedex is None:
            try:
                pokedex = json.load(open('.psdata/pokedex.json'))
            except IOError:
                pokedex = scrapers.scrape_battle_pokedex()
        if items is None:
            try:
                items = json.load(open('.psdata/items.json'))
            except IOError:
                items = scrapers.scrape_battle_items()

        self.sanitizer = sanitizer
        self.pokedex = pokedex
        self.items = items
        self.natures = utilities.load_natures()

        # diagnostics
        self.devolve_count = 0
        self.battle_forme_undo_count = 0
        self.ability_correct_count = 0


    def parse_log(self, log):
        """
        Parse the provided log and return structured data

        Args:
            log (str): file name of the battle log to parse

        Returns:
            (tuple):
                * BattleInfo: metadata about the match
                * tuple(tuple(Moveset)): the movesets used in the battle,
                    grouped by team
                * list(Matchup): list of matchups

        Raises:
            ParsingException: if there's a problem parsing the log
            FileNotFoundError: if the log doesn't exist
            json.decoder.JSONDecodeError: if the log is not a valid log

        """

        log = json.load(open(log))
        pass

    def _normalize_mega_evolution(self, species, item, moves,
                                  hackmons=False, mega_rayquaza_allowed=True):
        """
        We want (or at least want to be able to) count mega Pokemon separately
        from their base formes. So this function facilitates "mega evolving"
        base formes which can mega evolve during battle. It also "devolves"
        instances where the mega forme is specified as the species but, say,
        it's not actually holding the correct mega stone. Pokemon Showdown
        *should* devolve automatically, but we check just in case (and note it
        if it happens).

        Args:
            moveset (str): the sanitized species
            item (str): the sanitized held item
            moves (list[str]): the sanitized moves
            hackmons (Optional[bool]): is this a Hackmons meta (where Pokemon
                can start in their mega formes)? Default is False.
            mega_rayquaza_allowed (Optional[bool]): is Mega Rayquaza allowed in
                this metagame? Default is True. Note that if base-Rayquaza isn't
                allowed, there's no sense in setting this flag to False.

        Returns:
            str: the sanitized species
        """

        if hackmons:  # for Hackmons metas, the species in the log is king
            return species

        if species.startswith('rayquaza'):  # handle Rayquaza separately
            if mega_rayquaza_allowed and 'dragonascent' in moves:
                correct_species = 'rayquazamega'
            else:
                correct_species = 'rayquaza'
            if species != correct_species:
                if correct_species == 'rayquaza':
                    self.devolve_count += 1
            return correct_species

        if item is None:
            item = dict()
        elif item == 'redorb':  # manual fix
            item = {'megaEvolves': 'groudon', 'megaStone': 'groudonprimal'}
        elif item == 'blueorb':  # manual fix
            item = {'megaEvolves': 'kyogre', 'megaStone': 'kyogreprimal'}
        else:
            item = self.items[item]

        if 'megaStone' not in item.keys():  # devolve if no mega stone
            if _is_a_mega_forme(species, self.pokedex):
                self.devolve_count += 1
                return self.sanitizer.sanitize(
                    self.pokedex[species]['baseSpecies'])
            return species

        base_species = self.sanitizer.sanitize(item['megaEvolves'])
        mega_species = self.sanitizer.sanitize(item['megaStone'])

        if _is_a_mega_forme(species, self.pokedex) and species != mega_species:
            '''devolve if the mega species doesn't match the stone'''
            self.devolve_count += 1
            return self.sanitizer.sanitize(self.pokedex[species]['baseSpecies'])
        elif species == base_species:
            '''evolve if mega stone matches the base species'''
            return mega_species

        return species

    def _normalize_battle_formes(self, species):
        """
        Darmanitan-Zen and Meloetta-Pirouette aren't allowed in any metagame, so
        if you see it, replace it with its base form (and note that it showed
        up)

        Args:
            species (str): the species to normalize
        Returns:
            str: the normalized species
        """
        if species in ('darmanitanzen', 'meloettapirouette'):
            self.battle_forme_undo_count += 1
            return self.sanitizer.sanitize(
                self.pokedex[species]['baseSpecies'])
        return species

    def _normalize_ability(self, species, ability, any_ability=False):
        """
        So while we are treating Mega formes separately for counting, we still
        want to note the base forme's ability. That subtlety means we might need
        to *normalize* a moveset to make sure that the ability is a base forme
        ability (and not a mega forme ability). Pokemon Showdown should be
        doing this automatically, but we check just in case (and note it
        if we need to perform a correction).

        Args:
            species (str): the sanitized species
            ability (str): the sanitized ability
            any_ability (Optional[bool]): is this a Hackmons metagame or a meta
                like Almost-Any-Ability? Default is False.

        Returns:
            str: the normalized ability
        """

        if any_ability:  # movesets for these metas don't require normalization
            return ability

        if _is_a_mega_forme(species, self.pokedex):
            species = self.sanitizer.sanitize(
                self.pokedex[species]['baseSpecies'])

        if ability in self.sanitizer.sanitize(
                self.pokedex[species]['abilities'].values()):
            return ability  #no normalization needed

        self.ability_correct_count += 1
        return self.sanitizer.sanitize(self.pokedex[species]['abilities']['0'])



