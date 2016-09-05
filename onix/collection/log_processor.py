"""Functionality for processing of logs and routing parsed data to sinks"""
import os

from onix import contexts
from onix.collection import log_reader
from onix.collection import sinks


class LogProcessor(object):
    """
    Executor in charge of processing battle logs and routing the parsed data to
    the appropriate sinks. The LogProcessor is in charge of instantiating
    ``LogReader``s to process the logs that come in based on the format of the
    log (_e.g._ JSON file) and the metagame of the battle.

    Args:
        moveset_sink (sinks.MovesetSink) : The sink to route movesets data
        battle_info_sink (sinks.BattleInfoSink) :
            The sink to route battle metadata
        battle_sink (sinks.BattleSink) :
            The sink to route the actual turn-by-turn battle representations
        force_context_refresh (:obj:`bool`, optional) : Defaults to False. If
            True, any contexts that get loaded will be pull fresh data from
            Pokemon Showdown rather than rely on the local cache.
    """

    def __init__(self, moveset_sink, battle_info_sink, battle_sink,
                 force_context_refresh=False):

        self.moveset_sink = moveset_sink
        self.battle_info_sink = battle_info_sink
        self.battle_sink = battle_sink

        self._std_ctx = contexts.get_standard_context(force_context_refresh)
        self._readers = {}

    def _get_log_reader(self, log_ref):
        """
        Select the appropriate log reader to use to process the log. Instantiate
        one if none are available.

        Args:
            log_ref : an identifier specifying the log to parse

        Returns:
            log_reader.LogReader :
                A log reader suitable for parsing the log. If there are no
                suitable readers and it's not possible to instantiate one,
                returns ``None``.
        """

        # determine the metagame from the filename
        metagame = None
        path = log_ref.split(os.sep)
        filename = path[-1].split('-')
        if not filename[-1].endswith('.log.json'):
            """Currently only json logs are supported"""
            return None
        if len(filename) == 3:
            metagame = filename[1]

        if metagame is None:
            """can't determine the metagame :("""
            return None

        if metagame not in self._std_ctx.formats.keys():
            """no idea what the metagame is"""
            return None

        if 'mod' in self._std_ctx.formats[metagame].keys():
            """Non-standard metagames are not currently supported"""
            return None

        # Okay, phew. We're past all that. Now just return the standard reader

        if 'json_std' not in self._readers.keys():
            self._readers['json_std'] = log_reader.JsonFileLogReader(
                self._std_ctx)

        return self._readers['json_std']

    def process_logs(self, logs, ref_type='folder', error_handling='raise'):
        """
        Process the specified logs

        Args:
            logs : Reference to the logs to process
            ref_type (:obj:`str`, optional) :
                Description of the `logs` parameter specifying how to handle it.
                Options are:
                    * "file" : specifying a single JSON log
                    * "files" : specifying an iterable of JSON logs
                    * "folder" : specifying a directory or nested directory of
                        JSON logs
                Defaults to "folder"
            error_handling (:obj:`str`, optional) : The strategy for handling
                log-parsing errors. Options are:
                    * "raise" : raise an exception if an error is encountered.
                    * "skip" : silently skip problematic logs
                Defaults to "raise"

        Returns:
            int :
                the number of logs processed successfully
        """
        battle_infos = []
        all_movesets = dict()
        battles = []
        succesful_count = 0

        try:
            if ref_type == 'file':
                battle_info, movesets, battle = self._process_single_log(logs)
                battle_infos.append(battle_info)
                all_movesets.update(movesets)
                battles.append(battle)
                succesful_count += 1

            elif ref_type == 'files':
                for log_ref in logs:
                    battle_info, movesets, battle = self._process_single_log(
                        log_ref)
                    battle_infos.append(battle_info)
                    all_movesets.update(movesets)
                    battles.append(battle)
                    succesful_count += 1

            elif ref_type == 'folder':
                # if I only had to support python 3.5+, I could use glob.glob...
                for log_ref in [os.path.join(dirpath, filename)
                                for dirpath, _, filenames in os.walk(logs)
                                for filename in filenames
                                if filename.endswith('.log.json')]:
                    battle_info, movesets, battle = self._process_single_log(
                        log_ref)
                    battle_infos.append(battle_info)
                    all_movesets.update(movesets)
                    battles.append(battle)
                    succesful_count += 1
            else:
                raise ValueError('Unrecognized ref_type: '
                                 '{0}'.format(ref_type))

        except log_reader.ParsingError:
            if error_handling == 'raise':
                raise
            elif error_handling == 'skip':
                pass
            else:
                raise ValueError('Unrecognized error-handling strategy: '
                                 '{0}'.format(error_handling))

        if self.battle_info_sink:
            for battle_info in battle_infos:
                self.battle_info_sink.store_battle_info(battle_info)

        if self.moveset_sink:
            self.moveset_sink.store_movesets(all_movesets)

        if self.battle_sink:  # pragma: no cover TODO: remove when battles
            for battle in battles:
                self.battle_sink.store_battle(battle)

        return succesful_count

    def _process_single_log(self, log_ref):
        """
        Select the appropriate log reader and have it process the log

        Args:
            log_ref : an identifier specifying the log to parse

        Returns:
            (tuple):
                * BattleInfo : metadata about the match
                * :obj:`dict` of :obj:`str` to :obj:`Moveset` : a mapping of
                set IDs to movesets for the movesets appearing in the battle
                * Battle : a structured turn-by-turn recounting of the battle

        """
        reader = self._get_log_reader(log_ref)
        if reader is None:
            raise log_reader.ParsingError(log_ref, "Could not identify a "
                                                   "suitable reader for the "
                                                   "log")
        return reader.parse_log(log_ref)

