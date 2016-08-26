"""Methods for generating various reports"""
from collections import Counter

import six

from onix.reporting import dao


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

    usage_data = reporting_dao.get_usage_by_species(month, metagame, baseline)

    total_usage = sum(usage_data.values())/6

    pct_usage = Counter()

    for species, value in six.iteritems(usage_data):

        if species is None:  # skip "empty" slots
            continue
        elif species in species_lookup.keys():
            pretty_species = species_lookup[species]
        else:
            if unknown_species_handling == 'raise':
                raise KeyError('Unknown species or forme-concatenation: {0}'
                               .format(species))
            elif unknown_species_handling == 'guess':
                pretty_species = species.title()
            else:
                raise ValueError('Invalid mode for unknown_species_handling: '
                                 '{0}'.format(unknown_species_handling))

        pct_usage[pretty_species] += 100.0*value/total_usage

    sorted_usage = sorted([(species, usage) for species, usage
                           in six.iteritems(pct_usage)], key=lambda x:-x[1])

    longest_species_length = max(map(lambda x:len(x), pct_usage))

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

    for i in range(len(sorted_usage)):
        report_lines.append(' | {0:{1}d} | {2: <{3}} | {4:{5}.{6}f}% |'.format(
            i+1, column_widths['rank'],
            sorted_usage[i][0], column_widths['species'],
            sorted_usage[i][1],
            column_widths['usage']-1, column_widths['usage']-5))

    report_lines.append(separator)

    return '\n'.join(report_lines)+'\n'
