#!/usr/bin/env python
"""
@package glider.py
@file glider.py
@author Stuart Pearce & Chris Wingard
@brief Module containing parser scripts for glider data set agents
"""
__author__ = 'Stuart Pearce & Chris Wingard'
__license__ = 'Apache 2.0'

import re
import numpy as np

from math import copysign
from functools import partial

from mi.core.log import get_logger
from mi.core.common import BaseEnum
from mi.core.exceptions import SampleException, DatasetParserException
from mi.core.instrument.chunker import StringChunker
from mi.core.instrument.data_particle import DataParticle, DataParticleKey
from mi.dataset.dataset_parser import BufferLoadingParser

# start the logger
log = get_logger()

# grumble, mumble, grumble
ROW_REGEX = r'^(.*)$'  # just give me the whole effing row.
ROW_MATCHER = re.compile(ROW_REGEX)


# Only statekey used herein is position
class StateKey(BaseEnum):
    POSITION = "position"


###############################################################################
# Define the Particle Classes for Global and Coastal Gliders, both the delayed
# (delivered over Iridium network) and the recovered (downloaded from a glider
# upon recovery) data sets.
#
# [TODO: Build Particle classes for global recovered datasets and for all
# coastal glider data (delayed and recoverd)]
#
###############################################################################
class DataParticleType(BaseEnum):
    # Data particle types for the Open Ocean (aka Global) and Coastal gliders
    ### Global Gliders (GGLDR).
    GGLDR_CTDGV_DELAYED = 'ggldr_ctdpf_delyaed'
    GGLDR_CTDGV_RECOVERED = 'ggldr_ctdpf_recovered'
    GGLDR_FLORD_DELAYED = 'ggldr_flord_delayed'
    GGLDR_FLORD_RECOVERED = 'ggldr_flord_recovered'
    GGLDR_DOSTA_DELAYED = 'ggldr_dosta_delayed'
    GGLDR_DOSTA_RECOVERED = 'ggldr_dosta_recovered'
    GGLDR_GLDR_ENG_DELAYED = 'ggldr_eng_delayed'
    GGLDR_GLDR_ENG_RECOVERED = 'ggldr_eng_recovered'
    ### Coastal Gliders (CGLDR).
    CGLDR_CTDGV_DELAYED = 'cgldr_ctdpf_delyaed'
    CGLDR_CTDGV_RECOVERED = 'cgldr_ctdpf_recovered'
    CGLDR_FLORD_DELAYED = 'cgldr_flort_delayed'
    CGLDR_FLORD_RECOVERED = 'cgldr_flort_recovered'
    CGLDR_DOSTA_DELAYED = 'cgldr_dosta_delayed'
    CGLDR_DOSTA_RECOVERED = 'cgldr_dosta_recovered'
    CGLDR_PARAD_DELAYED = 'cgldr_parad_delayed'
    CGLDR_PARAD_RECOVERED = 'cgldr_parad_recovered'
    CGLDR_GLDR_ENG_DELAYED = 'cgldr_eng_delayed'
    CGLDR_GLDR_ENG_RECOVERED = 'cgldr_eng_recovered'
    # ADCPA data will parsed by a different parser (adcpa.py)


class GgldrCtdgvDelayedParticleKey(DataParticleKey):
    KEY_LIST = [
        'm_present_time',
        'm_present_secs_into_mission',
        'sci_m_present_time',
        'sci_m_present_secs_into_mission',
        'm_gps_lat',
        'm_gps_lon',
        'm_lat',
        'm_lon',
        'sci_water_cond',
        'sci_water_pressure',
        'sci_water_temp'
    ]


class GgldrCtdgvDelayedDataParticle(DataParticle):
    _data_particle_type = DataParticleType.GGLDR_CTDGV_DELAYED

    def build_parsed_values(self, gpd):
        """
        Takes a GliderParser object and extracts CTD data from the
        data dictionary and puts the data into a CTD Data Particle.

        @param gpd A GliderParser class instance.
        @param result A returned list with sub dictionaries of the data
        """
        if not isinstance(gpd, GliderParser):
            raise SampleException("GGLDR_CTDGV_DELAYED: Object Instance is not \
                                  a Glider Parsed Data object")

        result = []
        for iRecord in range(0, gpd.num_records):
            record = []
            for key in GgldrCtdgvDelayedParticleKey.KEY_LIST:
                if key in gpd.data_keys:
                    # read the value from the gpd dictionary
                    value = gpd.data_dict[key]['Data'][iRecord]

                    # check to see that the value is not a 'NaN'
                    if value == 'NaN':
                        continue

                    # check to see if this is the time stamp
                    if key == 'm_present_time':
                        self.set_internal_timestamp(float(value))

                    # check to see if this is a lat/longitude string
                    if '_lat' in key or '_lon' in key:
                        # convert latitiude/longitude strings to decimal degrees
                        value = GliderParser._string_to_ddegrees(value)
                    else:
                        # otherwise store the values as floats
                        value = float(value)

                    # add the value to the record
                    record.append({DataParticleKey.VALUE_ID: key,
                                   DataParticleKey.VALUE: value})

                else:
                    log.warn("GGLDR_CTDGV_DELAYED: The particle defined in the \
                             ParticleKey, %s, is not present in the current \
                             data set", key)

            # add the record to total results
            result.append(record)

        return result


class GgldrDostaDelayedParticleKey(DataParticleKey):
    KEY_LIST = [
        'm_present_time',
        'm_present_secs_into_mission',
        'sci_m_present_time',
        'sci_m_present_secs_into_mission',
        'm_gps_lat',
        'm_gps_lon',
        'm_lat',
        'm_lon',
        'sci_oxy4_oxygen',
        'sci_oxy4_saturation',
        ]


class GgldrDostaDelayedDataParticle(DataParticle):
    _data_particle_type = DataParticleType.GGLDR_DOSTA_DELAYED

    def build_parsed_values(self, gpd):
        """
        Takes a GliderParser object and extracts CTD data from the
        data dictionary and puts the data into a CTD Data Particle.

        @param gpd A GliderParser class instance.
        @param result A returned list with sub dictionaries of the data
        """
        if not isinstance(gpd, GliderParser):
            raise SampleException("GGLDR_DOSTA_DELAYED: Object Instance is not \
                                  a GliderParser object")

        result = []
        for iRecord in range(0, gpd.num_records):
            record = []
            for key in GgldrDostaDelayedParticleKey.KEY_LIST:
                if key in gpd.data_keys:
                    # read the value from the gpd dictionary
                    value = gpd.data_dict[key]['Data'][iRecord]

                    # check to see that the value is not a 'NaN'
                    if value == 'NaN':
                        continue

                    # check to see if this is the time stamp
                    if key == 'm_present_time':
                        self.set_internal_timestamp(float(value))

                    # check to see if this is a lat/longitude string
                    if '_lat' in key or '_lon' in key:
                        # convert latitiude/longitude strings to decimal degrees
                        value = GliderParser._string_to_ddegrees(value)
                    else:
                        # otherwise store the values as floats
                        value = float(value)

                    # add the value to the record
                    record.append({DataParticleKey.VALUE_ID: key,
                                   DataParticleKey.VALUE: value})

                else:
                    log.warn("GGLDR_DOSTA_DELAYED: The particle defined in the \
                             ParticleKey, %s, is not present in the current \
                             data set", key)

            # add the record to total results
            result.append(record)

        return result


class GgldrFlordDelayedParticleKey(DataParticleKey):
    KEY_LIST = [
        'm_present_time',
        'm_present_secs_into_mission',
        'sci_m_present_time',
        'sci_m_present_secs_into_mission',
        'm_gps_lat',
        'm_gps_lon',
        'm_lat',
        'm_lon',
        'sci_flbb_bb_units',
        'sci_flbb_chlor_units',
    ]


class GgldrFlordDelayedDataParticle(DataParticle):
    _data_particle_type = DataParticleType.GGLDR_FLORD_DELAYED

    def build_parsed_values(self, gpd):
        """
        Takes a GliderParser object and extracts FLORD data from the
        data dictionary and puts the data into a FLORD Data Particle.

        @param gpd A GliderParser class instance.
        @param result A returned list with sub dictionaries of the data
        """
        if not isinstance(gpd, GliderParser):
            raise SampleException("GGLDR_FLORD_DELAYED: Object Instance is not \
                                  a GliderParser object")

        result = []
        for iRecord in range(0, gpd.num_records):
            record = []
            for key in GgldrFlordDelayedParticleKey.KEY_LIST:
                if key in gpd.data_keys:
                    # read the value from the gpd dictionary
                    value = gpd.data_dict[key]['Data'][iRecord]

                    # check to see that the value is not a 'NaN'
                    if value == 'NaN':
                        continue

                    # check to see if this is the time stamp
                    if key == 'm_present_time':
                        self.set_internal_timestamp(float(value))

                    # check to see if this is a lat/longitude string
                    if '_lat' in key or '_lon' in key:
                        # convert latitiude/longitude strings to decimal degrees
                        value = GliderParser._string_to_ddegrees(value)
                    else:
                        # otherwise store the values as floats
                        value = float(value)

                    # add the value to the record
                    record.append({DataParticleKey.VALUE_ID: key,
                                   DataParticleKey.VALUE: value})

                else:
                    log.warn("GGLDR_FLORD_DELAYED: The particle defined in the \
                             ParticleKey, %s, is not present in the current \
                             data set", key)

            # add the record to total results
            result.append(record)

        return result


class GgldrEngDelayedParticleKey(DataParticleKey):
    KEY_LIST = [
        'c_battpos',
        'c_wpt_lat',
        'c_wpt_lon',
        'm_battpos',
        'm_coulomb_amphr_total',
        'm_coulomb_current',
        'm_depth',
        'm_de_oil_vol',
        'm_gps_lat',
        'm_gps_lon',
        'm_lat',
        'm_lon',
        'm_heading',
        'm_pitch',
        'm_present_time',
        'm_present_secs_into_mission',
        'm_speed',
        'm_water_vx',
        'm_water_vy',
        'sci_m_present_time',
        'sci_m_present_secs_into_mission',
        'x_low_power_status',
    ]


class GgldrEngDelayedDataParticle(DataParticle):
    _data_particle_type = DataParticleType.GGLDR_ENG_DELAYED

    def build_parsed_values(self, gpd):
        """
        Takes a GliderParser object and extracts engineering data from the
        data dictionary and puts the data into a engineering Data Particle.

        @param gpd A GliderParser class instance.
        @param result A returned list with sub dictionaries of the data
        """
        if not isinstance(gpd, GliderParser):
            raise SampleException("GGLDR_ENG_DELAYED: Object Instance is not \
                                  a GliderParser object")

        result = []
        for iRecord in range(0, gpd.num_records):
            record = []
            for key in GgldrEngDelayedParticleKey.KEY_LIST:
                if key in gpd.data_keys:
                    # read the value from the gpd dictionary
                    value = gpd.data_dict[key]['Data'][iRecord]

                    # check to see that the value is not a 'NaN'
                    if value == 'NaN':
                        continue

                    # check to see if this is the time stamp
                    if key == 'm_present_time':
                        self.set_internal_timestamp(float(value))

                    # check to see if this is a latitude/longitude string
                    if '_lat' in key or '_lon' in key:
                        # convert latitiude/longitude strings to decimal degrees
                        value = GliderParser._string_to_ddegrees(value)
                    else:
                        # otherwise store the values as floats
                        value = float(value)

                    # add the value to the record
                    record.append({DataParticleKey.VALUE_ID: key,
                                   DataParticleKey.VALUE: value})

                else:
                    log.warn("GGLDR_ENG_DELAYED: The particle defined in the \
                             ParticleKey, %s, is not present in the current \
                             data set", key)

            # add the record to total results
            result.append(record)

        return result


class GliderParser(BufferLoadingParser):
    """
    GliderParser parses a Slocum Electric Glider data file that has been
    converted to ASCII from binary and merged with it's corresponding flight or
    science data file, and holds the self describing header data in a header
    dictionary and the data in a data dictionary using the column labels as the
    dictionary keys. These dictionaries are used to build the particles.
    """
    def __init__(self,
                 config,
                 state,
                 stream_handle,
                 state_callback,
                 publish_callback,
                 *args, **kwargs):
        super(GliderParser, self).__init__(config,
                                           stream_handle,
                                           state,
                                           partial(StringChunker.regex_sieve_function,
                                                   regex_list=[ROW_MATCHER]),
                                           state_callback,
                                           publish_callback,
                                           *args,
                                           **kwargs)
        self._timestamp = 0.0
        self._record_buffer = []  # holds tuples of (record, state)
        self._read_state = {StateKey.POSITION:0, StateKey.TIMESTAMP:0.0}

        if state:
            self.set_state(self._state)

    def set_state(self, state_obj):
        """
        Set the value of the state object for this parser
        @param state_obj The object to set the state to. Should be a list with
        a StateKey.POSITION value and StateKey.TIMESTAMP value. The position is
        number of bytes into the file, the timestamp is an NTP4 format timestamp.
        @throws DatasetParserException if there is a bad state structure
        """
        log.trace("Attempting to set state to: %s", state_obj)
        if not isinstance(state_obj, dict):
            raise DatasetParserException("Invalid state structure")
        if not ((StateKey.POSITION in state_obj) and (StateKey.TIMESTAMP in state_obj)):
            raise DatasetParserException("Invalid state keys")

        self._timestamp = state_obj[StateKey.TIMESTAMP]
        self._timestamp += 1
        self._record_buffer = []
        self._state = state_obj
        self._read_state = state_obj

        # seek to it
        self._stream_handle.seek(state_obj[StateKey.POSITION])

    def _increment_timestamp(self, increment=1):
        """
        Increment timestamp by a certain amount in seconds. By default this
        dataset definition takes one sample per minute between lines. This method
        is designed to be called with each sample line collected. Override this
        as needed in subclasses
        @param increment Number of seconds in increment the timestamp.
        """
        self._timestamp += increment

    def _increment_state(self, increment, timestamp):
        """
        Increment the parser position by a certain amount in bytes. This
        indicates what has been READ from the file, not what has been published.
        The increment takes into account a timestamp of WHEN in the data the
        position corresponds to. This allows a reload of both timestamp and the
        position.

        This is a base implementation, override as needed.

        @param increment Number of bytes to increment the parser position.
        @param timestamp The timestamp completed up to that position
        """
        log.trace("Incrementing current state: %s with inc: %s, timestamp: %s",
                  self._read_state, increment, timestamp)

        self._read_state[StateKey.POSITION] += increment
        self._read_state[StateKey.TIMESTAMP] = timestamp

    def _read_header(self):
        """
        Read in the self describing header lines of an ASCII glider data
        file.
        """
        # There are usually 14 header lines, start with 14,
        # and check the 'num_ascii_tags' line.
        num_hdr_lines = 14
        hdr_line = 1
        while hdr_line <= num_hdr_lines:
            line = self._fid.readline()
            split_line = line.split()
            if 'num_ascii_tags' in split_line:
                num_hdr_lines = int(split_line[1])
            self.hdr_dict[split_line[0][:-1]] = split_line[1]
            hdr_line += 1

        # Thomas, my monkey of a son wanted this inserted in the code.

    def _read_data(self):
        """
        Read in the column labels, data type, number of bytes of each
        data type, and the data from an ASCII glider data file.
        """
        column_labels = self._fid.readline().split()
        column_type = self._fid.readline().split()
        column_num_bytes = self._fid.readline().split()

        # read each row of data & use np.array's ability to grab a
        # column of an array
        data = []
        for line in self._fid.readlines():
            data.append(line.split())
        data_array = np.array(data)  # NOTE: this is an array of strings

        # warn if # of described data rows != to amount read in.
        num_columns = int(self.hdr_dict['sensors_per_cycle'])
        if num_columns != data_array.shape[1]:
            log.warn('Glider data file does not have the same' +
                     'number of columns as described in the header.\n' +
                     'Described: %d, Actual: %d' % (num_columns,
                                                    data_array.shape[1])
                     )

        # extract data to dictionary
        for ii in range(num_columns):
            self.data_dict[column_labels[ii]] = {
                'Name': column_labels[ii],
                'Units': column_type[ii],
                'Number_of_Bytes': int(column_num_bytes[ii]),
                'Data': data_array[:, ii]
            }
        self.data_keys = column_labels
        self.num_records = data_array.shape[0]

    def parse_chunks(self):
        """
        Break python's fileIO to fit the stream/chunker framework...sigh
        """

        result_particles = []

    @staticmethod
    def _string_to_ddegrees(pos_str):
        """
        Converts the given string from this data stream into a more
        standard latitude/longitude value in decimal degrees.
        @param pos_str The position (latitude or longitude) string in the
            format "DDMM.MMMM" for latitude and "DDDMM.MMMM" for longitude. A
            positive or negative sign to the string indicates north/south or
            east/west, respectively.
        @retval The position in decimal degrees
        """
        minutes = float(pos_str[-7:])
        degrees = float(pos_str[0:-7])
        ddegrees = copysign((abs(degrees) + minutes / 60), degrees)
        return ddegrees
