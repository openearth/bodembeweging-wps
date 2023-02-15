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

# $Id: info_nhiflux.py 13706 2017-09-13 09:29:46Z sala $
# $Date: 2017-09-13 11:29:46 +0200 (Wed, 13 Sep 2017) $
# $Author: sala $
# $Revision: 13706 $
# $HeadURL: https://svn.oss.deltares.nl/repos/openearthtools/trunk/python/applications/wps/NutrientenAanpakMaas/krw_tseries_doelgat.py $
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
def tserie_doelgat(location, param):
        # Outputs prepare
        values = {}

        # Read config
        PLOTS_DIR, APACHE_DIR = readConfig()

        # Error messaging
        okparams, msg, x, y = check_location(location)
        if not(okparams):
            # logging.info(msg)
            values['error_html'] = msg
            return values

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
            json_str = json.dumps(values)
            return values

        return values
