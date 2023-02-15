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

# $Id: gw_timeseries_plot.py 14128 2018-01-30 07:30:36Z sala $
# $Date: 2018-01-30 08:30:36 +0100 (Tue, 30 Jan 2018) $
# $Author: sala $
# $Revision: 14128 $
# $HeadURL: https://svn.oss.deltares.nl/repos/openearthtools/trunk/python/applications/wps/emisk/gw_timeseries_plot.py $
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

from geojson import LineString, Feature, FeatureCollection
from shapely import wkt
from sqlalchemy import create_engine, MetaData

# Self libraries
from .utils import *
from .bokeh_plots import *

def gw_timeseries(point_str,date_from,date_to):
        # Outputs prepare
        outdata = io.StringIO()
        values = {}

        # Read config
        PLOTS_DIR, APACHE_DIR, GEOSERVER_URL, _, _, POSTGIS_H, POSTGIS_U, POSTGIS_P = readConfig()
        engine = create_engine('''postgresql://{u}:{p}@{h}/{d}'''.format(h=POSTGIS_H, u=POSTGIS_U, p=POSTGIS_P, d='oet_data'))

        # Get values for selected xy in fixed epsg
        if isinstance(point_str, str):
            try:
                location_info = json.loads(point_str)
                (xin,yin) = location_info['x'], location_info['y']
            except:
                raise Exception('Select a location on the map.')
        else:
            location_info = point_str
            (xin,yin) = location_info[0], location_info[1]
        epsgout = 'epsg:28992'
        epsgin = 'epsg:3857'
        (xk,yk) = change_coords(xin, yin, epsgin=epsgin, epsgout=epsgout)

        # Query database
        res, gwm_id, loc_id, z = gettimeseries(engine, xk, yk, date_from, date_to)
        datax, datay = list(zip(*res))

        # Generate plot GW vs time
        if not os.path.isdir(PLOTS_DIR):
            os.makedirs (PLOTS_DIR)
        tmpfile = tempfile(PLOTS_DIR)
        bokeh = bokeh_Plot(datax, datay, str(loc_id)+' (referentie niveau {z} (cm NAP))'.format(z=str(z)), tmpfile)
        bokeh.plot_Tseries()

        # Send back result JSON
        values['url_plot'] = APACHE_DIR + os.path.basename(tmpfile)
        values['title'] = 'Geselecteerde tijdreeks'
        json_str = json.dumps(values)

        return json_str
