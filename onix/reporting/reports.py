"""Methods for generating various reports"""
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
                         baseline=1630.0, min_turns=3,
                         unknown_species_handling='raise'):
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
            the baseline to use for weighting. Defaults to 1630.

            .. note ::
               a baseline of zero corresponds to unweighted stats
        min_turns (:obj:`int`, optional) :
                don't count any battles fewer than this many turns in length.
                Defaults value is 3.
        unknown_species_handling (:obj:`str`, optional) : The strategy for
          handling unknown species/formes. Options are:
            * "raise" : raise a KeyError
            * "guess" : 'guess' at an appropriate name by title-casing it
          Defaults to "raise"

    Returns:
        str :
            the usage stats report, ready for printing to stdout or saving to
            file

    Raises:
        KeyError : if an unknown species is encountered and the strategy is
            set to "raise"
        ValueError : if an unknown species is encountered and the strategy is
            not recognized
    """

    n_battles = reporting_dao.get_number_of_battles(month, metagame, min_turns)

    total_usage = reporting_dao.get_total_weight(month, metagame, baseline,
                                                 min_turns)

    usage_data = reporting_dao.get_usage_by_species(month, metagame,
                                                    species_lookup, baseline,
                                                    min_turns)

    if usage_data:
        longest_species_length = max(map(lambda x: len(x[0]), usage_data))
        '''so this will be 1 too long in the case that the longest species
        length is an unknown species (because of the prepended '-', but this is
        such a niche case, and it's not like the extra whitespace will look bad,
        so I'd rather leave the bug than force it to check the species twice'''
    else:
        longest_species_length = 0

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


MOVESET_REPORT_WIDTH = 48
MOVESET_REPORT_SEPARATOR = ' + ' + '-' * MOVESET_REPORT_WIDTH + ' +'


def _generate_moveset_subreport(usage_data, name, lookup,
                                 min_lines, min_pct):
    """
    Generate sub-reports (abilities report, items report...) for a Pokemon in a
    given metagame

    Args:
        usage_data (:obj:`list` of :obj:`tuple`) :
            weighted usage counts for each entry (sanitized entry name first
            value, weighted count second), sorted from highest count to lowest.
        name (str) :
            the name for this type of subreport (e.g. 'Abilities')
        lookup (dict) :
            mapping of sanitized names to display names for the entries in the
            report
        min_lines (int) :
            Report percentages for at least the top this-many abilities (if
            there are fewer abilities then that, then report all of them).
        min_pct (float) :
            Report abilities until the cumulative percentage exceeds at least
            this value.

    Returns:
        str : the subreport
    """

    report_lines = [' | {0: <{1}} |'.format(name, MOVESET_REPORT_WIDTH)]

    total = sum(map(lambda x: x[1], usage_data))

    cum_pct = 0.

    for i, row in enumerate(usage_data):

        pct = 100. * row[1] / total
        content = '{0} {1:.3f}%'.format(lookup[row[0]], pct)
        report_lines.append(' | {0: <{1}} |'.format(content,
                                                    MOVESET_REPORT_WIDTH))
        cum_pct += pct

        if i >= min_lines and cum_pct > min_pct:
            content = 'Other {0:.3f}%'.format(100.-cum_pct)
            report_lines.append(' | {0: <{1}} |'
                                .format(content, MOVESET_REPORT_WIDTH))
            break

    report_lines.append(MOVESET_REPORT_SEPARATOR)

    return '\n'.join(report_lines) + '\n'


def generate_abilities_reports(reporting_dao, abilities, species_lookup, month,
                              metagame, baseline=1630.0, min_turns=3,
                              min_lines=5, min_pct=95.):
    """
    Generate a report of abilities usage for Pokemon in a given metagame

    Args:
        reporting_dao (dao.ReportingDAO) :
            access object used to grab usage data
        abilities (dict) :
            the data encoded in `abilties.js` on PS. The keys are
            sanitized ability names, the values associated metadata, such as
            display name
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
            the baseline to use for weighting. Defaults to 1630.

            .. note ::
               a baseline of zero corresponds to unweighted stats
        min_turns (:obj:`int`, optional) :
            don't count any battles fewer than this many turns in length.
            Defaults value is 3.
        min_lines (:obj:`int`, optional) :
            Report percentages for at least the top this-many abilities (if
            there are fewer abilities then that, then report all of them).
            Default is 5.
        min_pct (:obj:`float`, optional) :
            Report abilities until the cumulative percentage exceeds at least
            this value. Default is 95.0.

    Returns
        dict :
            the ability reports for each species

    Notes:
        This report only covers the ability of the primary forme, since no
        mega evolutions, battle formes, etc. have more than one ability.
    """

    usage_data = reporting_dao.get_abilities(month, metagame, species_lookup,
                                             baseline, min_turns)

    lookup = {key: value['name'] for key, value in iteritems(abilities)}

    reports = {}

    for species, data in iteritems(usage_data):
        reports[species] = _generate_moveset_subreport(data, 'Abilities',
                                                       lookup,  min_lines,
                                                       min_pct)

    return reports


def generate_items_reports(reporting_dao, items, species_lookup, month,
                               metagame, baseline=1630.0, min_turns=3,
                               min_lines=5, min_pct=95.):
    """
    Generate a report of abilities usage for Pokemon in a given metagame

    Args:
        reporting_dao (dao.ReportingDAO) :
            access object used to grab usage data
        items (dict) :
            the data encoded in `items.js` on PS. The keys are
            sanitized ability names, the values associated metadata, such as
            display name
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
            the baseline to use for weighting. Defaults to 1630.

            .. note ::
               a baseline of zero corresponds to unweighted stats
        min_turns (:obj:`int`, optional) :
            don't count any battles fewer than this many turns in length.
            Defaults value is 3.
        min_lines (:obj:`int`, optional) :
            Report percentages for at least the top this-many abilities (if
            there are fewer abilities then that, then report all of them).
            Default is 5.
        min_pct (:obj:`float`, optional) :
            Report abilities until the cumulative percentage exceeds at least
            this value. Default is 95.0.

    Returns
        dict :
            the ability reports for each species

    Notes:
        This report only covers the ability of the primary forme, since no
        mega evolutions, battle formes, etc. have more than one ability.
    """

    usage_data = reporting_dao.get_items(month, metagame, species_lookup,
                                         baseline, min_turns)

    lookup = {key: value['name'] for key, value in iteritems(items)}
    lookup[None] = 'No Item'

    reports = {}

    for species, data in iteritems(usage_data):
        reports[species] = _generate_moveset_subreport(data, 'Items',
                                                       lookup, min_lines,
                                                       min_pct)

    return reports
