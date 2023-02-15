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

# $Id: info_nhiflux.py 13800 2017-10-10 07:50:22Z sala $
# $Date: 2017-10-10 09:50:22 +0200 (Tue, 10 Oct 2017) $
# $Author: sala $
# $Revision: 13800 $
# $HeadURL: https://svn.oss.deltares.nl/repos/openearthtools/trunk/python/applications/wps/onlinemodelling/info_nhiflux.py $
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
# from pywps.Process import WPSProcess

# relative
from .opendap_nhi import nhi_invoer
from .ahn2 import ahn
from .coords import *
from .bokeh_plots import bokeh_Plot
from .utils import *

logger = logging.getLogger('PYWPS')

"""
Waterbodems nhi WPS start script

This is a redesigned WPS for the Waterbodems application, based in infoline_redesigned.

if it runs on localhost then:
getcapabilities:  http://localhost/cgi-bin/pywps.cgi?request=GetCapabilities&service=wps&version=1.0.0
describe process: http://localhost/cgi-bin/pywps.cgi?request=DescribeProcess&service=wps&version=1.0.0&identifier=info_nhiflux
execute:          http://localhost/cgi-bin/pywps.cgi?&service=wps&request=Execute&version=1.0.0&identifier=info_nhiflux&datainputs=[geom={%20%22type%22:%20%22FeatureCollection%22,%20%22features%22:%20[%20{%20%22type%22:%20%22Feature%22,%20%22properties%22:%20{},%20%22geometry%22:%20{%20%22type%22:%20%22Point%22,%20%22coordinates%22:%20[%204.3689751625061035,%2052.01105825338195%20]%20}%20}%20]%20}]
"""

def info_nhi(location):

        # Output prepare
        json_output = io.StringIO()
        values = {}

        # read config file #
        PLOTS_DIR, APACHE_DIR = readConfig()

        # Main loop (for every point of the line)
        values['nhi'] = []
        npoints = 0

        # Input (coordinates)
        location_info = json.loads(request.inputs["location"][0].data)
        logger.info(location_info)
        (xin, yin) = location_info['x'], location_info['y']

        # convert coordinates
        # epsg = self.epsg.getValue()
        epsg = 3857
        epsgin = 'epsg:'+str(epsg)
        logger.info('''Input Coordinates {} {} in epsg={}'''.format(xin,yin,epsgin))
        (x,y) = change_coords(xin, yin, epsgin=epsgin, epsgout='epsg:28992')
        (x,y) = getCoords250(x, y)
        logger.info('''INPUT [info_nhiflux]: coordinates_250_rdnew={},{}'''.format(x,y))
        values['title'] = 'LHM 3.3'

        # AHN
        try:
            hoogte = ahn(x, y)
            #values['maaiveldhoogte'] = float(hoogte)
        except:
            hoogte = 0.0
            #values['maaiveldhoogte'] = hoogte

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
            dt['dist'] = math.sqrt((x-xo)*(x-xo) + (y-yo)*(y-yo)) # euclidean distance
            dt['point'] = [round(x,1), round(y,1)]

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
                if math.isnan(prev):    prev = None
                if math.isnan(top):     top = None
                if math.isnan(base):    base = None

                layer_fer = {"top": prev, "bottom": top,
                             "type": "aquifer", "GLG": glg, "GHG": ghg}
                layer_tar = {"flux": flf, "top": top,
                             "bottom": base, "type": "aquitard"}
                dt['layers'].append(layer_fer)
                dt['layers'].append(layer_tar)

                prev = base

            maaiveldhoogte = float(max(ranges))

            # Correction for maaiveld
            #for layer in dt['layers']:
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
            npoints+=1
        except:
            data_error = True
            pass

        if data_error:
            values['error_html'] = "<p>There was an error accessing the given location, make sure you click inside the Netherlands</p>"
        else:
            # Output and graph (temporary files, outside of wps instance tempdir, otherwise they get deleted)
            dirname = str(time.time()).replace('.', '')
            temp_html = os.path.join(self.PLOTS_DIR, dirname+'.html')
            plot = bokeh_Plot(values, temp_html, colorTable='NHI')
            plot.generate_plot()
            values['url_plot'] = self.APACHE_DIR + dirname +'.html'
            values['plot_xsize'] = 350
            values['plot_ysize'] = 650

            # Output finalize
            json_str = json.dumps(values)
            json_output.write(json_str)
            logger.info('''OUTPUT [info_nhiflux]: {}'''.format(json_str))
            # self.json.setValue(json_output)
            response.outputs['json'].data = json_output

        return response
