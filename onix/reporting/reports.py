"""Methods for generating various reports"""
import six

from onix.reporting import dao


class SpeciesLookup(object):
    """
    An object that takes sanitized species names and forme lists and returns
    "display names," suitable for writing to a report

    Args:
        pokedex (dict) : the Pokedex to use, scraped from Pokemon Showdown
        aliases (dict) : the alias lookup to use, scraped from Pokemon
            Showdown
    """

    def __init__(self, pokedex, aliases):
        self.lookup = {species: entry['species']
                       for species, entry in six.iteritems(pokedex)}
        for pokemon in pokedex.keys():
            if 'otherForms' in pokedex[pokemon].keys():
                for form in pokedex[pokemon]['otherForms']:
                    self.lookup[form] = pokedex[pokemon]['species']

    def lookup(self, count_megas_separately=True):
        """
        Look up a Pokemon's display name from its sanitized concatenation of forme
        names, e.g. "venusaur,venusaurmega"

        Args:
            count_megas_separately (bool, optional) : Are mega formes counted
                separately? Defaults to True
            hackmons (bool, optional) : Is this a hackmons tier? Defaults to False.

        Returns:
            str :
                The Pokemon's display name

        """


def generate_usage_stats(dao, species_lookup, month, metagame,
                         baseline=1630.0):
    """
    Generate a usage stats report

    Args:
        dao (dao) :
            access object used to grab usage data
        species_lookup (SpeciesLookup) :
            object to handle the mapping of sanitized species names / forme
            lists to something one would actually want to display.
        month (str) :
                the month to analyze
        metagame (str) :
            the sanitized name of the metagame
        baseline (:obj:`float:, optional) :
            the baseline to use for  weighting. Defaults to 1630.
            .. note :
               a baseline of zero corresponds to unweighted stats

    Returns:
        str :
            the usage stats report, ready for printing to stdout or saving to
            file
    """
