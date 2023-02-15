# -*- coding: utf-8 -*-
# Copyright notice
#   --------------------------------------------------------------------
#   Copyright (C) 2015 Deltares
#       Maarten Pronk
#
#       maarten.pronk@deltares.nl
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

# $Id: regis.py 15872 2019-10-25 10:13:26Z pronk_mn $
# $Date: 2019-10-25 12:13:26 +0200 (vr, 25 okt 2019) $
# $Author: pronk_mn $
# $Revision: 15872 $
# $HeadURL: https://svn.oss.deltares.nl/repos/openearthtools/trunk/python/applications/wps/nhidataportaal/processes/regis.py $
# $Keywords: $

"""
Created on Tue Oct 13 14:22:36 2015
Regis (netcdf) Accessor
"""

from pyproj import Proj, transform
import numpy as np
from netCDF4 import Dataset
import psycopg2
from shapely.geometry import Point
from operator import itemgetter
from os.path import dirname, realpath, join
import os

from processes.nutrientenmaas.secrets_parser import pgconfig

dir_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../config/nutrientenmaas.txt')

def getregislayersdb(x, y):
    """Returns list of regis layers for given point.
    Uses database lookup."""

    dbcon = pgconfig(dir_path, section="regis")  # dbcon = pgconfig(join(dir_path, "dbconfig.ini"))
    table_geom = 'regis.regisshapes'

    # Set up connection
    try:
        con = psycopg2.connect(**dbcon)
    except Exception as e:
        print(e)
    cur = con.cursor()

    # Retrieves all geometry for point
    try:
        p = Point(x, y)
        cur.execute('''SELECT layer
                    FROM {}
                    WHERE geom && ST_SETSRID(ST_GeomFromText('{}'),28992)
                    '''.format(table_geom, p))
    except Exception as e:
        print(e)

    layers = [x[0] for x in cur.fetchall()]
    return layers


def getregisnamesdb():
    """Returns list of regis layers for given point.
    Uses database lookup."""

    dbcon = pgconfig(dir_path, section="regis")
    table_geom = 'regis.regisname'

    # Set up connection
    con = psycopg2.connect(**dbcon)
    cur = con.cursor()

    # Retrieves all geometry for point
    names = {}
    cur.execute('''SELECT afkorting, formatie_laagnaam
                FROM {} '''.format(table_geom))
    for x in cur.fetchall():
        names[x[0]] = x[1]
    return names


def getregiscolorsdb():
    """Returns list of regis layers for given point.
    Uses database lookup."""

    dbcon = pgconfig(dir_path, section="regis")
    table_geom = 'regis.regiscolors'

    # Set up connection
    con = psycopg2.connect(**dbcon)
    cur = con.cursor()

    # Retrieves all geometry for point
    colors = {}
    cur.execute('''SELECT name,hex
                FROM {}
                '''.format(table_geom))
    for x in cur.fetchall():
        colors[x[0]] = x[1]
    return colors
    print('Colors: ', colors)


def find_nearest(array, value):
    """Finds nearest value in array.
    taken from stack^ question 2566412"""
    idx = (np.abs(array - value)).argmin()
    return array[idx], int(idx)


def queryregis(regisurl, regislayers, x, y):
    # Open dataset
    rdata = Dataset(regisurl, 'r')

    layers_available = rdata.variables

    # Transfrom from RD NEW to WGS 84
    rdnew = Proj(init='epsg:28992')
    wgs84 = Proj(init='epsg:4326')
    nx, ny = transform(rdnew, wgs84, x, y)

    out = {}
    # Find the right place in the raster
    xnear, xi = find_nearest(rdata['lon'][:], nx)
    ynear, yi = find_nearest(rdata['lat'][:], ny)

    # Find value for each regislayer
    for layer in layers_available:
        value = rdata[layer]
        rl = layer.split('-')
        if len(rl) > 2:
            rlayer, type = rl[:2]
            if rlayer in regislayers and type in ['b', 't']:
                out[layer] = value[yi, xi]

    rdata.close()
    return out


def formatregis(regisdict, colors, names):
    """Format netcdf output for web."""

    # Combine bottom and top layers
    layerdic = {}
    for key in regisdict:
        layer = key.split('-')[0]
        if layer in layerdic:
            layerdic[layer].append(regisdict[key])
        else:
            layerdic[layer] = [regisdict[key]]

    # Make list from maaiveld downwards
    listout = []
    for k, v in layerdic.items():
        if k in colors:
            c = colors[k]  # look up colors
        else:
            c = "#000"  # fail color
        if k in names:
            n = names[k]
        else:
            n = k
        # filter out [0,0]
        if v[0] - v[1] == 0:
            continue
        # order b,t neatly
        if v[1] > v[0]:
            v = [v[1], v[0]]
            # layerdic[k] = v
        # print v[0], v[1], v[1] > v[0]
        listout.append([n, v[0], v[1], c])
    # sort list to second of each item
    l = sorted(listout, key=itemgetter(1))
    l.reverse()
    return l


def simplify_regis(formattedregis):
    simplifiedregis = []
    prevlaag = ["XXX"]
    for laag in formattedregis:
        if laag[0][:-2] == prevlaag[0][:-2]:  # name overlap
            if simplifiedregis[-1][2] > laag[2]:
                simplifiedregis[-1][2] = laag[2]  # diepste punt
        else:
            prevlaag = laag
            simplifiedregis.append(laag)

    for laag in simplifiedregis:
        try:
            int(laag[0][-1])
            laag[0] = laag[0][:-2]
        except:
            pass

    return simplifiedregis


def regiswps(x, y):
    regislayers = getregislayersdb(x, y)
    regiscolors = getregiscolorsdb()
    regisnames = getregisnamesdb()
    regisfn = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../static/regis/regis_combined.nc')
    rd = queryregis(regisfn, regislayers, x, y)
    rf = formatregis(rd, regiscolors, regisnames)
    return simplify_regis(rf)

# if __name__ == "__main__":
#    x = 93762
#    y = 450204

#    print regiswps(x , y)
#    regislayers = getregislayersdb(x, y)
#    regiscolors = getregiscolorsdb()
#    regiscurl = 'http://opendap-nhi-data.deltares.nl/thredds/dodsC/opendap/regis21/regis_combined.nc'
#    regisfn = 'D:/software/regis/regis_combined.nc'
#    rd = queryregis(regisfn, regislayers, x, y)
#    # print rd
#    print formatregis(rd,regiscolors)
