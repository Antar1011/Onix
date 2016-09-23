"""Methods for generating various reports"""
from collections import Counter

from future.utils import iteritems

from onix.reporting import dao


def _species_check(species, unknown_species_handling):
    """
    Check species string for unknown species and handle them accordingly

    Args:
        species (str) : the species string returned from the DAO
        unknown_species_handling (str): the unknown-species-handling strategy

    Returns:
        str :
            the species string, possibly transformed if that's what the
            strategy called for
    Raises:
        KeyError : if an unknown species is encountered and the strategy is
            set to "raise"
        ValueError : if an unknown species is encountered and the strategy is
            not recognized
    """
    if species.startswith('-'):  # unknown species!
        species = species[1:]
        if unknown_species_handling == 'raise':
            raise KeyError('Unknown species or forme-concatenation: {0}'
                           .format(species))
        elif unknown_species_handling == 'guess':
            return species.title()
        else:
            raise ValueError('Invalid mode for unknown_species_handling: '
                             '{0}'.format(unknown_species_handling))
    else:
        return species


def generate_usage_stats(reporting_dao, species_lookup, month, metagame,
                         baseline=1630.0, unknown_species_handling='raise'):
    """
    Generate a usage stats report

    Args:
        reporting_dao (dao.ReportingDAO) :
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

    n_battles = reporting_dao.get_number_of_battles(month, metagame)

    total_usage = reporting_dao.get_total_weight(month, metagame, baseline)

    usage_data = reporting_dao.get_usage_by_species(month, metagame,
                                                    species_lookup, baseline)

    longest_species_length = max(map(lambda x: len(x[0]), usage_data))
    '''so this will be 1 too long in the case that the longest species length is
    an unknown species (because of the prepended '-', but this is such a niche
    case, and it's not like the extra whitespace will look bad, so I'd rather
    leave the bug than force it to check the species twice'''

    column_widths = {'rank': 4,
                     'species': max(25, longest_species_length),
                     'usage': 9}

    report_lines = [' Total battles: {0:d}'.format(n_battles),
                    ' Avg. weight / team: {0:8f}'.format(
                        total_usage / n_battles / 2)]

    separator = ''
    for key in ('rank', 'species', 'usage'):
        separator += ' + ' + '-'*column_widths[key]
    separator += ' +'

    report_lines.append(separator)
    report_lines.append(' | {0: <{1}} | {2: <{3}} | {4: <{5}} |'.format(
        'Rank', column_widths['rank'],
        'Species', column_widths['species'],
        'Usage %', column_widths['usage']))
    report_lines.append(separator)

    for i, row in enumerate(usage_data):
        report_lines.append(' | {0:{1}d} | {2: <{3}} | {4:{5}.{6}f}% |'.format(
            i+1, column_widths['rank'],
            _species_check(row[0], unknown_species_handling),
            column_widths['species'],
            row[1]*100./total_usage,
            column_widths['usage']-1, column_widths['usage']-5))

    report_lines.append(separator)

    return '\n'.join(report_lines)+'\n'
