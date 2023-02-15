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

# $Id: kust_2danimation.py 14134 2018-01-31 07:01:10Z sala $
# $Date: 2018-01-31 08:01:10 +0100 (Wed, 31 Jan 2018) $
# $Author: sala $
# $Revision: 14134 $
# $HeadURL: https://svn.oss.deltares.nl/repos/openearthtools/trunk/python/applications/wps/mepduinen/kust_2danimation.py $
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
import urllib.request, urllib.parse, urllib.error
from PIL import Image

# modules
import types
import simplejson as json
import io

# Self libraries
from .utils import *

def animation(location,yrstart,yrend):
    # Outputs prepare
    # Read config
    values = {}
    PLOTS_DIR, APACHE_DIR, GEOSERVER_URL, GEOSERVER_ANIM_URL, GEOSERVER_ANIM_LAY, _ , _ , _ = readConfig()

    # Check bbox
    try:
        geom = shapely.wkt.loads(location)
    except:
         raise Exception('Geen locatie opgegeven in WKT-indeling [Polygoon]')


    # Get values for selected bbox
    (minx, miny, maxx, maxy) = geom.bounds
    if max(maxx-minx, maxy-miny) > 20000:
        raise Exception('Selecteer een kleiner gebied en probeer het opnieuw')

    epsgout = 'epsg:28992'
    epsgin = 'epsg:3857'
    epsglatlon = 'epsg:4326'
    (xmink, ymink) = change_coords(minx, miny, epsgin=epsgin, epsgout=epsgout)
    (xmaxk, ymaxk) = change_coords(maxx, maxy, epsgin=epsgin, epsgout=epsgout)
    (lonmin, latmin) = change_coords(minx, miny, epsgin=epsgin, epsgout=epsglatlon)
    (lonmax, latmax) = change_coords(maxx, maxy, epsgin=epsgin, epsgout=epsglatlon)
    bboxstr = '{},{},{},{}'.format(xmink,ymink,xmaxk,ymaxk)

    # For every year selected within the timespan
    time=[]
    for y in range(int(yrstart), int(yrend)+1): # configured on top
        time.append('{}-01-01T00:00:00.000Z'.format(y))
    timestr = ",".join(time)

    # Calculate shape
    if ((xmaxk-xmink) > (ymaxk-ymink)):
        resparam='width=1024'
    else:
        resparam='height=1024'

    # Build up url
    url='{}?layers={}&bbox={}&transparent=true&format=image/gif;subtype=animated&format_options=gif_loop_continuosly:true&aparam=TIME&avalues={}&{}'.format(
        GEOSERVER_ANIM_URL, GEOSERVER_ANIM_LAY, bboxstr, timestr, resparam)

    # Download gif
    try:
        if not os.path.isdir(PLOTS_DIR):
            os.makedirs (PLOTS_DIR)
        tmpfile = tempfile(PLOTS_DIR, typen='anim', extension='.gif')
        urllib.request.urlretrieve(url, tmpfile)
        im = Image.open(tmpfile)
        values['url_gif'] = APACHE_DIR + os.path.basename(tmpfile)
        values['url_gif_x0'] = minx
        values['url_gif_y0'] = miny
        values['url_gif_x1'] = maxx
        values['url_gif_y1'] = maxy
        values['url_gif_w'] = im.size[0]
        values['url_gif_h'] = im.size[1]
        json_str = json.dumps(values)
    except:
        raise Exception('No data for the selected bounding box. Please draw inside the available area.')

    return json_str
