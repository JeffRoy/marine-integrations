"""
@package mi.dataset.driver.moas.gl.engineering.driver
@file marine-integrations/mi/dataset/driver/moas/gl/engineering/driver.py
@author Stuart Pearce & Chris Wingard
@brief Driver for the glider Engineering
Release notes:

initial release
"""

__author__ = 'Stuart Pearce & Chris Wingard'
__license__ = 'Apache 2.0'

from mi.core.log import get_logger
log = get_logger()

from mi.core.common import BaseEnum
from mi.core.exceptions import ConfigurationException
from mi.dataset.parser.glider import GliderEngineeringParser
from mi.dataset.parser.glider import EngineeringTelemeteredDataParticle, EngineeringScienceTelemeteredDataParticle
from mi.dataset.parser.glider import EngineeringRecoveredDataParticle, EngineeringScienceRecoveredDataParticle
from mi.dataset.parser.glider import EngineeringMetadataDataParticle, EngineeringMetadataRecoveredDataParticle
from mi.dataset.harvester import SingleDirectoryHarvester
from mi.dataset.dataset_driver import MultipleHarvesterDataSetDriver, HarvesterType, DataSetDriverConfigKeys

class DataTypeKey(BaseEnum):
    ENG_TELEMETERED = 'eng_telemetered'
    ENG_RECOVERED = 'eng_recovered'

class EngineeringDataSetDriver(MultipleHarvesterDataSetDriver):

    @classmethod
    def stream_config(cls):
        return [EngineeringTelemeteredDataParticle.type(),
                EngineeringScienceTelemeteredDataParticle.type(),
                EngineeringMetadataDataParticle.type(),
                EngineeringRecoveredDataParticle.type(),
                EngineeringScienceRecoveredDataParticle.type(),
                EngineeringMetadataRecoveredDataParticle.type()]

    def __init__(self, config, memento, data_callback, state_callback,
                 event_callback, exception_callback):

        data_keys = [DataTypeKey.ENG_TELEMETERED, DataTypeKey.ENG_RECOVERED]

        harvester_type = {DataTypeKey.ENG_TELEMETERED: HarvesterType.SINGLE_DIRECTORY,
                          DataTypeKey.ENG_RECOVERED: HarvesterType.SINGLE_DIRECTORY}

        super(EngineeringDataSetDriver, self).__init__(config, memento, data_callback,
                                                       state_callback, event_callback,
                                                       exception_callback, data_keys, harvester_type)

    def _build_parser(self, parser_state, infile, data_key):
        """
        Build and return the specified parser as indicated by the data_key.
        @param parser_state previous parser state to initialize parser with
        @param data_key harvester / parser key
        @param infile file name
        """
        parser = None

        log.debug("DRIVER._build_parser(): data_key= %s", data_key)

        if data_key == DataTypeKey.ENG_TELEMETERED:
            log.debug("DRIVER._build_parser(): using a TELEMETERED Parser")
            parser = self._build_eng_telemetered_parser(parser_state, infile, data_key)

        elif data_key == DataTypeKey.ENG_RECOVERED:
            log.debug("DRIVER._build_parser(): using a RECOVERED Parser")
            parser = self._build_eng_recovered_parser(parser_state, infile, data_key)
        else:
            raise ConfigurationException("Parser Configuration incorrect: %s" % data_key)

        return parser

    def _build_eng_telemetered_parser(self, parser_state, infile, data_key):
        """
        Build and return the specified parser as indicated by the data_key.
        """
        config = self._parser_config

        config.update({
            DataSetDriverConfigKeys.PARTICLE_MODULE: 'mi.dataset.parser.glider',
            DataSetDriverConfigKeys.PARTICLE_CLASS: [EngineeringMetadataDataParticle,
                                                     EngineeringTelemeteredDataParticle,
                                                     EngineeringScienceTelemeteredDataParticle]
        })
        log.debug(" ## ## ## ")
        log.debug(" ## ## ## ")
        log.debug(" ## ## ## ")
        log.debug(" ## ## ## ")
        log.debug(" ## ## ## ")
        log.debug(" ## ## ##  DRIVER._build_eng_telemetered_parser(): parser_state= %s, input file= %s, data_key= %s",
                  parser_state, infile, data_key)
        log.debug(" ## ## ## ")
        log.debug(" ## ## ## ")
        log.debug(" ## ## ## ")
        log.debug(" ## ## ## ")
        log.debug(" ## ## ## ")



        parser = GliderEngineeringParser(config,
                                         parser_state,
                                         infile,
                                         lambda state,
                                         ingested: self._save_parser_state(state, data_key, ingested),
                                         self._data_callback,
                                         self._sample_exception_callback)

        return parser

    def _build_eng_recovered_parser(self, parser_state, infile, data_key):
        """
        Build and return the specified parser as indicated by the data_key.
        """
        config = self._parser_config

        config.update({
            DataSetDriverConfigKeys.PARTICLE_MODULE: 'mi.dataset.parser.glider',
            DataSetDriverConfigKeys.PARTICLE_CLASS: [EngineeringRecoveredDataParticle,
                                                     EngineeringScienceRecoveredDataParticle,
                                                     EngineeringMetadataRecoveredDataParticle],
        })

        log.debug(" ## ## ## ")
        log.debug(" ## ## ##  DRIVER._build_eng_recovered_parser(): parser_state= %s, input file= %s, data_key= %s",
                  parser_state, infile, data_key)
        log.debug(" ## ## ## ")

        parser = GliderEngineeringParser(config,
                                         parser_state,
                                         infile,
                                         lambda state, ingested: self._save_parser_state(state, data_key, ingested),
                                         self._data_callback,
                                         self._sample_exception_callback)

        return parser

    def _build_harvester(self, driver_state):
        """
        Build and return the list of harvesters
        """
        harvesters = []

        log.debug(" ## ## ## ")
        log.debug(" ## ## ##  DRIVER._build_harvester(): driver_state= %s", driver_state)
        log.debug(" ## ## ## ")

        harvester_telem = self._build_single_dir_harvester(driver_state, DataTypeKey.ENG_TELEMETERED)
        if harvester_telem is not None:
            log.debug(" ## ## ##  DRIVER._build_harvester(): adding a telem harvester to list")
            harvesters.append(harvester_telem)

        harvester_recov = self._build_single_dir_harvester(driver_state, DataTypeKey.ENG_RECOVERED)
        if harvester_recov is not None:
            log.debug(" ## ## ##  DRIVER._build_harvester(): adding a recovered harvester to list")
            harvesters.append(harvester_recov)
        else:
            log.debug(" ## ## ##  DRIVER._build_harvester(): !!!recovered harvester WAS NONE")

        return harvesters

    def _build_single_dir_harvester(self, driver_state, data_key):
        """
        Build and return a harvester
        """
        harvester = None
        if data_key in self._harvester_config:

            log.debug(" ## ## ## ")
            log.debug(" ## ## ##  DRIVER._build_single_dir_harvester(): driver_state= %s, data_key= %s", driver_state, data_key)
            log.debug(" ## ## ## ")

            harvester = SingleDirectoryHarvester(self._harvester_config.get(data_key),
                                                 driver_state[data_key],
                                                 lambda filename: self._new_file_callback(filename, data_key),
                                                 lambda modified: self._modified_file_callback(modified, data_key),
                                                 self._exception_callback)
        else:
            log.warn('No configuration for %s harvester, not building', data_key)

        return harvester