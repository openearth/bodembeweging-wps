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

# $Id: coords.py 13711 2017-09-13 14:52:48Z sala $
# $Date: 2017-09-13 16:52:48 +0200 (Wed, 13 Sep 2017) $
# $Author: sala $
# $Revision: 13711 $
# $HeadURL: https://svn.oss.deltares.nl/repos/openearthtools/trunk/python/applications/wps/onlinemodelling/coords.py $
# $Keywords: $

import os
from pyproj import Proj, transform
from osgeo import gdal, osr, ogr, gdal_array
from osgeo.gdalconst import *
from numpy import *
import matplotlib.pyplot as plt

# Change XY coordinates general function
def change_coords(px, py, epsgin='epsg:3857', epsgout='epsg:28992'):
    outProj = Proj(init=epsgout)
    inProj = Proj(init=epsgin)
    return transform(inProj, outProj, px, py)

# Get normalized 250m coordinates
def getCoords250(px, py, resolution=250):
	return round(px/resolution)*resolution, round(py/resolution)*resolution

# Change/Add raster projection
def changeProjRaster28992(gtifpath):
    # Source and destination
    dst_filename = gtifpath.replace('.tif','_rdnew.tif')
    src_ds = gdal.Open(gtifpath)
    driver = gdal.GetDriverByName("GTiff")
    dst_ds = driver.CreateCopy(dst_filename, src_ds, 0)
    # RD_new set
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(28992)
    dest_wkt = srs.ExportToWkt()
    dst_ds.SetProjection(dest_wkt)
    return dst_filename	

# Get Isolines from Raster
def raster2isolines(gtifpath, interval=0.05, offset=1):
    # Setup raster path
    dirname = os.path.dirname(gtifpath)
    basename = os.path.basename(dirname)
    shppath = os.path.join(dirname, basename+'_isolines.shp')

    # Read in raster data
    indataset1 = gdal.Open(gtifpath, GA_ReadOnly)
    in1 = indataset1.GetRasterBand(1)

    # Generate layer to save Contourlines in
    ogr_ds = ogr.GetDriverByName("ESRI Shapefile").CreateDataSource(shppath)
    contour_shp = ogr_ds.CreateLayer('contour')
    field_defn = ogr.FieldDefn("ID", ogr.OFTInteger)
    contour_shp.CreateField(field_defn)
    field_defn = ogr.FieldDefn("eff", ogr.OFTReal)
    contour_shp.CreateField(field_defn)

    # Generate Contourlines
    gdal.ContourGenerate(in1, interval, offset, [], 0, 0, contour_shp, 0, 1)
    ogr_ds = None
    del ogr_ds 

    # Return shapefile path   
    return shppath    
