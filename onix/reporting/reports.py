"""Methods for generating various reports"""
import six

from onix.reporting import dao


def generate_usage_stats(dao, species_lookup, month, metagame,
                         baseline=1630.0, unknown_species_handling='raise'):
    """
    Generate a usage stats report

    Args:
        dao (dao) :
            access object used to grab usage data
        species_lookup (dict) :
            mapping of species names or forme-concatenations to their display
            names. This is what handles things like determing whether megas
            are tiered together or separately or what counts as an
            "appearance-only" forme.
        month (str) :
            the month to analyze in the format 'YYYY-MM'
        metagame (str) :
            the sanitized name of the metagame
        baseline (:obj:`float`, optional) :
            the baseline to use for  weighting. Defaults to 1630.
            .. note :
               a baseline of zero corresponds to unweighted stats
        unknown_species_handling (:obj:`str`, optional) :
            How should unknown species/formes be handled?
                * "raise" : raise a KeyError
                * "guess" : 'guess' at an appropriate name by title-casing it
            Defaults to "raise"

    Returns:
        str :
            the usage stats report, ready for printing to stdout or saving to
            file
    """
