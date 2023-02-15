# -*- coding: utf-8 -*-
# Copyright notice
#   --------------------------------------------------------------------
#   Copyright (C) 2016 Deltares
#       Gerrit Hendriksen, Joan Sala
#
#       gerrit.hendriksen@deltares.nl, joan.salacalero@deltares.nl
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

# $Id: info_nhiflux.py 15882 2019-11-01 14:53:49Z angelova $
# $Date: 2019-11-01 15:53:49 +0100 (vr, 01 nov 2019) $
# $Author: angelova $
# $Revision: 15882 $
# $HeadURL: https://svn.oss.deltares.nl/repos/openearthtools/trunk/python/applications/wps/nhidataportaal/processes/info_nhiflux.py $
# $Keywords: $

# core
import os
import operator
import math
import tempfile
import logging
import configparser
import time

# modules
import types
import simplejson as json
import io
from pywps import Format
from pywps.app import Process
from pywps.inout.inputs import ComplexInput, LiteralInput
from pywps.inout.outputs import LiteralOutput,ComplexOutput
from pywps.app.Common import Metadata
from pywps.inout.formats import FORMATS
# from pywps.Process import WPSProcess

# relative
from .opendap_nhi import nhi_invoer
from .ahn2 import ahn
from .coords import *
from processes.nutrientenmaas.bokeh_plots import bokeh_Plot

"""
Waterbodems nhi WPS start script

This is a redesigned WPS for the Waterbodems application, based in infoline_redesigned.

if it runs on localhost then:
getcapabilities:  http://localhost/cgi-bin/pywps.cgi?request=GetCapabilities&service=wps&version=1.0.0
describe process: http://localhost/cgi-bin/pywps.cgi?request=DescribeProcess&service=wps&version=1.0.0&identifier=info_nhiflux
execute:          http://localhost/cgi-bin/pywps.cgi?&service=wps&request=Execute&version=1.0.0&identifier=info_nhiflux&datainputs=[geom={%20%22type%22:%20%22FeatureCollection%22,%20%22features%22:%20[%20{%20%22type%22:%20%22Feature%22,%20%22properties%22:%20{},%20%22geometry%22:%20{%20%22type%22:%20%22Point%22,%20%22coordinates%22:%20[%204.3689751625061035,%2052.01105825338195%20]%20}%20}%20]%20}]
"""

# Default config file (relative path)
CONFIG_FILE = os.path.join(os.path.dirname(
    os.path.realpath(__file__)), '../../config/nutrientenmaas.txt')  # 'NHIconfig.txt'


class info_nhiflux(Process):
    def __init__(self):
        # init process; note: identifier must be same as filename
        inputs = [LiteralInput(identifier="location",
                                            title="Prik op een lokatie naar voorkeur.",
                                            abstract="input=mapselection",
                                            # type=type(""),
                                            uoms=["point"],
                                            default="Select a location on the map")]

        outputs = [ComplexOutput(identifier="json",
                                          title="Returns list of values for specified xy",
                                          abstract="""Returns list of values for specified xy""",
                                          supported_formats=[Format("text/plain"),Format("application/json")])]
        super(info_nhiflux,self).__init__(
                            self._handler,
                            identifier="info_nhiflux",
                            title="Toon laagopbouw volgens LHM3.3 [punt]",
                            version="1.3.3.7",
                            store_supported="true",
                            status_supported="true",
                            abstract="""Deze functie maakt het mogelijk om op een willekeurige plaats in Nederland de laag opbouw te visualiseren waarmee LHM3.3 is geschematiseerd.""",
                            grass_location=False,
                            inputs=inputs,
                            outputs=outputs)



    # Read configuration from file

    def readConfig(self):
        cf = configparser.RawConfigParser()
        cf.read(CONFIG_FILE)
        self.PLOTS_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), cf.get('Bokeh', 'plots_dir'))
        self.APACHE_DIR = cf.get('Bokeh', 'apache_dir')

    def _handler(self, request, response):
        # Read configuration file
        self.readConfig()

        # Output prepare
        json_output = io.StringIO()
        values = {}

        # Main loop (for every point of the line)
        values['nhi'] = []
        npoints = 0

        # Input (coordinates)
        # location_info = json.loads(self.location.getValue())
        location_info = json.loads(request.inputs["location"][0].data)
        logging.info(location_info)
        (xin, yin) = location_info['x'], location_info['y']


        # convert coordinates
        # epsg = self.epsg.getValue()
        epsg = 3857
        epsgin = 'epsg:'+str(epsg)
        logging.info(
            '''Input Coordinates {} {} in epsg={}'''.format(xin, yin, epsgin))
        (x, y) = change_coords(xin, yin, epsgin=epsgin, epsgout='epsg:28992')
        (x, y) = getCoords250(x, y)
        logging.info(
            '''INPUT [info_nhiflux]: coordinates_250_rdnew={},{}'''.format(x, y))

        # AHN
        try:
            hoogte = ahn(x, y)
            values['maaiveldhoogte'] = float(hoogte)
        except:
            hoogte = 0.0
            values['maaiveldhoogte'] = hoogte

        # x0,y0
        if npoints == 0:
            xo = x
            yo = y

        # NHI (x,y)
        data_error = False
        try:
            dt = {}
            ranges = [hoogte]
            fluxes = []
            dt['layers'] = []
            dt['dist'] = math.sqrt((x-xo)*(x-xo) + (y-yo)
                                   * (y-yo))  # euclidean distance
            dt['point'] = [round(x, 1), round(y, 1)]

            nhi = nhi_invoer(x, y)
            prev = float(hoogte)
            nhi_sort = sorted(list(nhi.items()), key=operator.itemgetter(0))
            logging.info(nhi_sort)
            for item in nhi_sort:
                key, value = item
                value = [float(x) if x is not None else None for x in value]
                flf, ghg, glg, top, base = value

                if not base or not top:
                    continue

                if base is not None:
                    ranges.append(base)
                if top is not None:
                    ranges.append(top)
                if flf is not None:
                    fluxes.append(flf)

                # NaN control
                if math.isnan(prev):
                    prev = None
                if math.isnan(top):
                    top = None
                if math.isnan(base):
                    base = None

                layer_fer = {"top": prev, "bottom": top,
                             "type": "aquifer", "GLG": glg, "GHG": ghg}
                layer_tar = {"flux": flf, "top": top,
                             "bottom": base, "type": "aquitard"}
                dt['layers'].append(layer_fer)
                dt['layers'].append(layer_tar)

                prev = base

            # Correction for maaiveld
            maaiveldhoogte = float(max(ranges))
            # for layer in dt['layers']:
            #    layer['top'] -= maaiveldhoogte
            #    layer['bottom'] -= maaiveldhoogte

            # because we've corrected with maaiveldhoogte
            #dt['max'] = 0
            #dt['min'] = float(min(ranges)) - maaiveldhoogte
            dt['max'] = float(max(ranges))
            dt['min'] = float(min(ranges))
            dt['maxFlux'] = float(max(fluxes))
            dt['minFlux'] = float(max(fluxes))

            # add to list
            values['nhi'].append(dt)
            npoints += 1
        except:
            data_error = True
            pass

        if data_error:
            values['error_html'] = "<p>Er zijn geen gegevens beschikbaar voor de geselecteerde locatie</p>"
        else:
            # Plot title
            values['title'] = """LHM3.3 (x={} m, y={} m, z={} m-NAP)""".format(
                int(xo), int(yo), int(maaiveldhoogte))

            # Output and graph (temporary files, outside of wps instance tempdir, otherwise they get deleted)
            dirname = str(time.time()).replace('.', '')
            temp_html = os.path.join(self.PLOTS_DIR, dirname+'.html')
            plot = bokeh_Plot(values, temp_html, colorTable='NHI')
            print("Plot has been generated", plot)
            plot.generate_plot()
            values['url_plot'] = self.APACHE_DIR + dirname + '.html'
            values['title'] = 'NHI plot'
            values['plot_xsize'] = 450
            values['plot_ysize'] = 650

        # Output finalize
        json_str = json.dumps(values)
        # json_output.write(json_str)
        logging.info('''OUTPUT [info_nhiflux]: {}'''.format(json_str))
        # self.json.setValue(json_output)
        response.outputs['json'].data = json_str
        return response
