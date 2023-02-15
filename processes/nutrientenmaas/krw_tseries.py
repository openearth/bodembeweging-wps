# -*- coding: utf-8 -*-
# Copyright notice
#   --------------------------------------------------------------------
#   Copyright (C) 2016 Deltares
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

# $Id: krw_tseries.py 14275 2018-04-06 06:30:55Z sala $
# $Date: 2018-04-06 08:30:55 +0200 (vr, 06 apr 2018) $
# $Author: sala $
# $Revision: 14275 $
# $HeadURL: https://svn.oss.deltares.nl/repos/openearthtools/trunk/python/applications/wps/NutrientenAanpakMaas/krw_tseries.py $
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

# Self libraries
from .meetlocaties_plot import *
from .utils import *
logger = logging.getLogger('PYWPS')

"""
This is a redesigned WPS for the NutrientenAanpakMaas application
"""

# Execute wps service to get tseries
def krw_tseries(location, param):
        # Outputs prepare
        outdata = io.StringIO()
        values = {}

        # Read config
        PLOTS_DIR, APACHE_DIR = readConfig()

        # Error messaging
        okparams, msg, x, y = check_location(location)
        if not(okparams):
            values['error_html'] = msg
            json_str = json.dumps(values)
            return json_str

        # change to epsg of database
        (xk,yk) = change_coords(x, y, epsgin='epsg:3857', epsgout='epsg:28992')

        # Query Database by location
        locinfo = queryPostGISClosestPointKRW(xk, yk)
        # Get Fews identifier
        try:
                fewsid = locinfo[0][1]
                xfind = locinfo[0][3]
                yfind = locinfo[0][4]
        except:
                values['error_html'] = 'Er is een fout opgetreden tijdens het ondervragen van de database [search closest]'
                return values

        # Send back result JSON [pre-cooked plot]
        values['url_png'] = APACHE_DIR + "../../static/krwnutrend/" 'Trend-{}%20-%20{}tot.jpg'.format(fewsid, param[:1]) # N or P
        values['plot_xsize'] = 500
        values['plot_ysize'] = 350

        # Zoom and window title
        (xzoom,yzoom) = change_coords(xfind, yfind, epsgin='epsg:28992', epsgout='epsg:3857')
        values['zoomx'] = xzoom
        values['zoomy'] = yzoom
        #values['dist'] = dist
        values['title'] = 'Geselecteerde tijdreeksen / KRW ' + param
        return values
