# -*- coding: utf-8 -*-
# Copyright notice
#   --------------------------------------------------------------------
#   Copyright (C) 2018 Deltares
#       Joan Sala
#
#       joan.salacalero@deltares.nl
#
#   This library is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This library is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this library.  If not, see <http://www.gnu.org/licenses/>.
#   --------------------------------------------------------------------
#
# This tool is part of <a href="http://www.OpenEarth.eu">OpenEarthTools</a>.
# OpenEarthTools is an online collaboration to share and manage data and
# programming tools in an open source, version controlled environment.
# Sign up to recieve regular updates of this function, and to contribute
# your own tools.

# $Id: kust_3dplot.py 14134 2018-01-31 07:01:10Z sala $
# $Date: 2018-01-31 08:01:10 +0100 (Wed, 31 Jan 2018) $
# $Author: sala $
# $Revision: 14134 $
# $HeadURL: https://svn.oss.deltares.nl/repos/openearthtools/trunk/python/applications/wps/mepduinen/kust_3dplot.py $
# $Keywords: $

# core
import os
import operator
import math
import tempfile
import logging
import configparser
import time
import shapely

# modules
import types
import simplejson as json
import io
from pywps import Format
from pywps.app import Process
from pywps.inout.inputs import ComplexInput, LiteralInput
from pywps.inout.outputs import LiteralOutput, ComplexOutput
from pywps.app.Common import Metadata
from pywps.inout.formats import FORMATS

logger = logging.getLogger('PYWPS')

from .mepduinen.kust_3dplot import plot_3d
from .mepduinen.kust_gwtimeseries import gw_timeseries
from .mepduinen.animation import *
from .mepduinen.kust_transect import transect

"""
This is a redesigned WPS for the mepduinen application
"""

START_YEAR = 1996
END_YEAR = 2019

class Kust3dplot(Process):
    def __init__(self):

        inputs = [LiteralInput(identifier="location",
                                  title="Click here to start drawing. Get results by clicking on Execute",
                                  abstract="input=bbox",
                                  data_type="string",
                                  uoms=["Bbox"]),

                LiteralInput(identifier="year",
                                title="Kies start",
                                abstract="input=dropdownmenu",
                                data_type="integer",
                                allowed_values=list(range(START_YEAR, END_YEAR+1)),
                                default=END_YEAR)]

        outputs = [ComplexOutput(identifier="json",
                                  title="Returns list of values for specified xy",
                                  abstract="""Returns list of values for specified xy""",
                                  supported_formats=[Format("text/plain"),Format("application/json")])]

        super(Kust3dplot,self).__init__(
                            self._handler,
                            identifier="kust_3dplot",
                            title="Kust - 3D plot",
                            version='1.3.3.7',
                            abstract="""Selecteer een selectiekader en klik op Execute om een interactieve grafiek van de hoogtegegevens te krijgen.""",
                            metadata=[Metadata('Kust Transect'), Metadata('Maakt dwarsprofielen van de JARKUS grids')],
                            inputs=inputs,
                            outputs=outputs,
                            grass_location=False,
                            store_supported=True,
                            status_supported=True)


    def _handler(self, request, response):

        # Inputs check
        location = request.inputs["location"][0].data
        year = request.inputs["year"][0].data

        # Check bbox
        try:
            res = plot_3d(location,year)
        except Exception as e:
            print('''WPS [MepduinenTransect]: ERROR = {}'''.format(e))
            res = json.dumps({'error_html' : 'ERROR: {}'.format(e)})

        response.outputs['json'].data = res
        return

class GwTimeseries(Process):
    def __init__(self):

        inputs = [LiteralInput(identifier="location",
                                  title="Selecteer een locatie en druk op execute",
                                  abstract="input=mapselection",
                                  data_type="string",
                                  uoms=["point"]),

                LiteralInput(identifier="yrstart",
                            title="Kies start datum",
                            data_type="string",
                            default='01-01-1980'),

                LiteralInput(identifier="yrend",
                            title="Kies eind datum",
                            abstract="input=dropdownmenu",
                            data_type="string",
                            default='01-01-2020')]

        outputs = [ComplexOutput(identifier="json",
                                  title="Returns list of values for specified xy",
                                  abstract="""Returns list of values for specified xy""",
                                 supported_formats=[Format("text/plain"),Format("application/json")])]

        # init process; note: identifier must be same as filename
        super(GwTimeseries, self).__init__(
                            self._handler,
                            identifier="gw_timeseries_plot",
                            title="Grondwater plot",
                            version="1.3.3.7",
                            abstract="""Selecteer een grondwatermeetpunt, definieer van-tot datum en genereer een tijdreeks van de grondwaterstand""",
                            metadata=[Metadata('Groundwater Timeseries'), Metadata('Maakt tijdreeks van de grondwaterstand')],
                            inputs=inputs,
                            outputs=outputs,
                            grass_location=False,
                            store_supported=True,
                            status_supported=True)


    def _handler(self, request,response):
        # Inputs check

        point_str = request.inputs["location"][0].data
        date_from = request.inputs["yrstart"][0].data
        date_to = request.inputs["yrend"][0].data
        logging.info('''INPUT [gw_timeseries_plot]: location={}'''.format(str(point_str)))
        
        try:
            res = gw_timeseries(point_str,date_from,date_to)
        except Exception as e:
            print('''WPS [MepduinenTimeseries]: ERROR = {}'''.format(e))
            res = json.dumps({'error_html' : 'ERROR: {}'.format(e)})

        response.outputs['json'].data = res
        return

class Kust2danimation(Process):
    def __init__(self):

        inputs = [LiteralInput(identifier="location",
                              title="Click here to start drawing. Get results by clicking on Execute",
                              abstract="input=bbox",
                              data_type="string",
                              uoms=["Bbox"]),

                LiteralInput(identifier="yrstart",
                            title="Kies start",
                            abstract="input=dropdownmenu",
                            data_type="integer",
                            allowed_values=list(range(START_YEAR, END_YEAR+1)),
                            default=START_YEAR),

                LiteralInput(identifier="yrend",
                            title="Kies eind",
                            abstract="input=dropdownmenu",
                            data_type="integer",
                            allowed_values=list(range(START_YEAR, END_YEAR+1)),
                            default=END_YEAR)]


        outputs = [ComplexOutput(identifier="json",
                                  title="Returns list of values for specified xy",
                                  abstract="""Returns list of values for specified xy""",
                                  supported_formats=[Format("text/plain"),Format("application/json")])]

        # init process; note: identifier must be same as filename
        super(Kust2danimation,self).__init__(
                            self._handler,
                            identifier="kust_2danimation",
                            title="Kust - 2D animation",
                            version="1.3.3.7",
                            abstract="""Selecteer een selectiekader en klik op Execute om een interactieve grafiek van de hoogtegegevens te krijgen.""",
                            metadata=[Metadata('Kust 2D animation'), Metadata('Maakt interactieve grafiek van de hoogtegegevens te krijgen')],
                            inputs=inputs,
                            outputs=outputs,
                            grass_location=False,
                            store_supported=True,
                            status_supported=True)


    def _handler(self, request, response):
        # Inputs check
        location = request.inputs["location"][0].data
        yrstart = request.inputs["yrstart"][0].data
        yrend = request.inputs["yrend"][0].data

        try:
            res = animation(location,yrstart,yrend)
        except Exception as e:
            print('''WPS [Mepduinen2danimation]: ERROR = {}'''.format(e))
            res = json.dumps({'error_html' : 'ERROR: {}'.format(e)})

        response.outputs['json'].data = res
        return

class KustTransect(Process):
    def __init__(self):
        # init process; note: identifier must be same as filename
        inputs = [LiteralInput(identifier="transect",
                                          title="Teken een transect en klik op Execute",
                                          abstract="input=mapselection",
                                          data_type="string",
                                          uoms=["linestring"]),

                LiteralInput(identifier="yrstart",
                            title="Kies start",
                            abstract="input=dropdownmenu",
                            data_type="integer",
                            allowed_values=list(range(START_YEAR, END_YEAR+1)),
                            default=START_YEAR),

                LiteralInput(identifier="yrend",
                            title="Kies eind",
                            abstract="input=dropdownmenu",
                            data_type="integer",
                            allowed_values=list(range(START_YEAR, END_YEAR+1)),
                            default=END_YEAR)]


        outputs = [ComplexOutput(identifier="json",
                                      title="Returns list of values for specified xy",
                                      abstract="""Returns list of values for specified xy""",
                                      supported_formats=[Format("text/plain"),Format("application/json")])]

        super(KustTransect, self).__init__(
                            self._handler,
                            identifier="kust_transect",
                            title="Kust - Transect",
                            version='1.3.3.7',
                            abstract="""Deze functie maakt het mogelijk om dwarsprofielen van de JARKUS grids te maken. Teken een profiel (dubbel klik om het profiel af te sluiten) en klik op Execute om het dwarsprofiel te bepalen (dit is een dynamisch proces en kan even duren).""",
                            metadata=[Metadata('Kust Transect'), Metadata('Maakt dwarsprofielen van de JARKUS grids')],
                            inputs=inputs,
                            outputs=outputs,
                            grass_location=False,
                            store_supported=True,
                            status_supported=True,)

    def _handler(self, request, response):

        linestr_str = request.inputs["transect"][0].data
        yrstart = int(request.inputs["yrstart"][0].data)
        yrend = int(request.inputs["yrend"][0].data)

        try:
            res = transect(linestr_str, yrstart,yrend)
        except Exception as e:
            print('''WPS [MepduinenTransect]: ERROR = {}'''.format(e))
            res = json.dumps({'error_html' : 'ERROR: {}'.format(e)})

        response.outputs['json'].data = res
        return
