# -*- coding: utf-8 -*-
# Copyright notice
#   --------------------------------------------------------------------
#   Copyright (C) 2019 Deltares
#       Gerrit Hendriksen,Joan Sala
#
#       joan.salacalero@deltares.nl, gerrit.hendriksen@deltares.nl
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

# $Id: utils.py 14277 2018-04-06 08:43:39Z sala $
# $Date: 2018-04-06 10:43:39 +0200 (vr, 06 apr 2018) $
# $Author: sala $
# $Revision: 14277 $
# $HeadURL: https://svn.oss.deltares.nl/repos/openearthtools/trunk/python/applications/wps/NutrientenAanpakMaas/utils.py $
# $Keywords: $

# core
import time
import configparser
import os
# libraries
import simplejson as json
from sqlalchemy import create_engine
from os.path import join, dirname, realpath, abspath



# additional python
from processes.common.coords import change_coords

# Parameters check
def check_location(location, epsgin='epsg:3857'):
    # Valid JSON
    try:
        # Input (coordinates)
        if isinstance(location, basestring):
            location_info = json.loads(location)
            (xin,yin) = location_info['x'], location_info['y']
        else:
            location_info = location
            (xin,yin) = location_info[0], location_info[1]

        (lon,lat) = change_coords(xin, yin)
        print('''Input Coordinates {} {} -> {} {}'''.format(xin,yin,lon,lat))
    except Exception as e:
        print(e)
        return False, '''<p>Please select a location first with the 'Select on map' button</p>''', -1, -1

    # Parameters check OK
    return True, '', xin, yin

# Get a unique temporary file
def getTempFile(tempdir):
    dirname = str(time.time()).replace('.','')
    return os.path.join(tempdir, dirname+'.html')

# Read configuration from file
# make the paths absolute. 

def readConfig():
    
    configf=join(dirname(realpath(__file__)), '../../config/endure.txt')
    cf = configparser.RawConfigParser()
    cf.read(configf)
    PLOTS_DIR = join(dirname(realpath(__file__)), cf.get('Bokeh', 'plots_dir')) # gives the absolute path of the plots dir
    APACHE_DIR = cf.get('Bokeh', 'apache_dir')
   
    ENGINE = create_engine('postgresql+psycopg2://'+cf.get('PostGIS', 'user')
    +':'+cf.get('PostGIS', 'pass')+'@'+cf.get('PostGIS', 'host')+':'+str(cf.get('PostGIS', 'port'))
    +'/'+cf.get('PostGIS', 'db'), strategy='threadlocal')
    IMG_DIR = cf.get('Images','img_dir')

    return PLOTS_DIR, APACHE_DIR, ENGINE, IMG_DIR
