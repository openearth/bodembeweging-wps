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

# $Id: info_regis.py 13801 2017-10-10 07:56:37Z sala $
# $Date: 2017-10-10 09:56:37 +0200 (Tue, 10 Oct 2017) $
# $Author: sala $
# $Revision: 13801 $
# $HeadURL: https://svn.oss.deltares.nl/repos/openearthtools/trunk/python/applications/wps/onlinemodelling/info_regis.py $
# $Keywords: $

# core
import os
import math
import tempfile
import logging
import time
import configparser

# modules
import types
import simplejson as json
import io
#from pywps.Process import WPSProcess

# relative
from .regis import regiswps
from .coords import *
from .bokeh_plots import bokeh_Plot
from .utils import *

logger = logging.getLogger('PYWPS')

"""
Waterbodems REGIS WPS start script

This is a redesigned WPS for the Waterbodems application, based in infoline_redesigned.

if it runs on localhost then:
getcapabilities:  http://localhost/cgi-bin/pywps.cgi?request=GetCapabilities&service=wps&version=1.0.0
describe process: http://localhost/cgi-bin/pywps.cgi?request=DescribeProcess&service=wps&version=1.0.0&identifier=info_regis
execute:          http://localhost/cgi-bin/pywps.cgi?&service=wps&request=Execute&version=1.0.0&identifier=info_regis&datainputs=[geom={%20%22type%22:%20%22FeatureCollection%22,%20%22features%22:%20[%20{%20%22type%22:%20%22Feature%22,%20%22properties%22:%20{},%20%22geometry%22:%20{%20%22type%22:%20%22Point%22,%20%22coordinates%22:%20[%204.3689751625061035,%2052.01105825338195%20]%20}%20}%20]%20}]
"""
def info_regis(location):
        # Output prepare
        json_output = io.StringIO()
        values = {}

        # Read configuration file
        PLOTS_DIR, APACHE_DIR = readConfig()

        # Main loop (for every point of the line)
        values['regis'] = []
        npoints = 0

        # Input (coordinates)
        #epsg = self.epsg.getValue()
        epsg = 3857
        epsgin = 'epsg:'+ str(epsg)
        location_info = json.loads(request.inputs["location"][0].data)
        # location_info = json.loads(self.location.getValue())
        (xin, yin) = location_info['x'], location_info['y']

        # convert coordinates
        logger.info('''Input Coordinates {} {} in epsg={}'''.format(xin, yin, epsgin))
        (x,y) = change_coords(xin, yin, epsgin=epsgin, epsgout='epsg:28992')
        (x,y) = getCoords250(x, y)
        logger.info('''INPUT [info_regis]: coordinates_250_rdnew={},{}'''.format(x,y))
        values['title'] = 'REGIS'

        # x0,y0
        if npoints == 0:
            xo = x
            yo = y

        # Regis (x,y)
        data_error = False
        try:
            regis = regiswps(x, y)
            minv = regis[0][1]
            maxv = regis[-1][2]

            # regis runs from NAP, not maaiveld
            maaiveldverschil = regis[0][1]
            dt = {}
            dt['dist'] = math.sqrt((x-xo)*(x-xo) + (y-yo)*(y-yo))  # euclidean distance
            dt['min'] = float(maxv)  # - maaiveldverschil
            dt['max'] = float(minv)  # - maaiveldverschil
            dt['layers'] = []
            dt['point'] = [round(x,1), round(y, 1)]

            for layer in regis:
                fromv = float(layer[1])   # - maaiveldverschil
                tov = float(layer[2])   # - maaiveldverschil
                typev = layer[0]
                dt['layers'].append(
                    {
                        "top": fromv, "bottom": tov, "type": typev
                    })
            dt['layers'] = dt['layers'][::-1]

            # to serialize results, avoiding NaN
            #if math.isnan(dt['top']):       dt['top'] = None
            #if math.isnan(dt['bottom']):    dt['bottom'] = None

            # add to list
            values['regis'].append(dt)
            npoints += 1
        except Exception as e:
            data_error = True
            logging.info(e)
            pass

        if data_error:
            values['error_html'] = "<p>There was an error accessing the given location, make sure you click inside the Netherlands</p>"
        else:
            # Output and graph (temporary files, outside of wps instance tempdir, otherwise they get deleted)
            dirname = str(time.time()).replace('.', '')
            temp_html = os.path.join(self.PLOTS_DIR, dirname+'.html')
            plot = bokeh_Plot(values, temp_html, colorTable='REGIS')
            plot.generate_plot()
            values['url_plot'] = self.APACHE_DIR + dirname + '.html'
            values['plot_xsize'] = 350
            values['plot_ysize'] = 650

        # Output finalize
        json_str = json.dumps(values, use_decimal=True)
        logger.info('''OUTPUT [info_regis]: {}'''.format(json_str))
        # json_output.write(json_str)
        # self.json.setValue(json_output)
        response.outputs['json'].data = json_str
        return response
