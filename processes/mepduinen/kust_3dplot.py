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

from scipy import ndimage

# Self libraries
from .utils import *

def plot_3d(location,year):
    # Outputs prepare
    outdata = io.StringIO()
    values = {}

    # Read config
    PLOTS_DIR, APACHE_DIR, GEOSERVER_URL,_,_,_,_,_ = readConfig()

    # Check bbox
    try:
        geom = shapely.wkt.loads(location)
    except:
        raise Exception('Did not provide a location in wkt format [Polygon]')

    layer = 'Kust:{}'.format(year)
    # Bounds in UTM coord system
    (minx, miny, maxx, maxy) = geom.bounds
    epsgout = 'epsg:28992'
    epsgin = 'epsg:3857'
    (xmink, ymink) = change_coords(minx, miny, epsgin=epsgin, epsgout=epsgout)
    (xmaxk, ymaxk) = change_coords(maxx, maxy, epsgin=epsgin, epsgout=epsgout)

    # Layer to intersect [pre-defined]
    data=getDatafromWCS(GEOSERVER_URL, layer, xmink, ymink, xmaxk, ymaxk, all_box=True)
    if data is None:
        raise Exception('No data for the selected bounding box. Please draw inside the available area.')

    nx = data.shape[0]
    ny = data.shape[1]
    #data = ndimage.zoom(data, 0.5, order=0) # nearest neighbour [0.5 means from 5m to 20m res]
    resx = 5
    resy = 5
    zarray = np.asarray(data)
    zarray[np.logical_or(zarray<-999.0, zarray>999.0)] = 0.0 # msl
    #zarray = ndimage.zoom(zarray, 0.5, order=0) # nearest neighbour [0.5 means from 5m to 20m res]
    zarray = zarray.tolist()

    # Send back result JSON
    values['title'] = '3D Hoogte plot'

    # 3d values for VisJs [fixed resolution of 100meters]
    logging.info('3D-data size {} x {}'.format(nx,ny))
    if (nx*ny < 50000):
        values['z'] = zarray
        values['xstep'] = resx
        values['ystep'] = resy
        values['nx'] = nx
        values['ny'] = ny
        values['legendlabel'] = 'Hoogte [m-NAP]'
        json_str = json.dumps(values)
    else:
        raise Exception('Te veel waarden geselecteerd. Gelieve uw selectiekader te beperken')

    return json_str
