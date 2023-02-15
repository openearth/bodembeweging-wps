# -*- coding: utf-8 -*-
"""
Created on Fri Feb 01 17:31:17 2019

@author: Lilia Angelova
"""

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

  #Self libraries
from .pie_chart_plot import *
from .utils import *
logger = logging.getLogger('PYWPS')

"""
This is a redesigned WPS for the NutrientenAanpakMaas application
"""

# Execute wps service to get tseries
def pie_chart(location):
        # Outputs prepare
        values = {}

        # Read config
        PLOTS_DIR, APACHE_DIR = readConfig()

        okparams, msg, x, y = check_location(location)

        # change to epsg of database
        (xk,yk) = change_coords(x, y, epsgin='epsg:3857', epsgout='epsg:28992')

        #color palletes based on colorbrewer
        color_dict = {"act_bem":"#8dd3c7", "afw_ov":"#ffffb3", "antrop":"#bebada", "buitenl":"#fb8072", "dep_op":"#80b1d3", "his_bem":"#fdb462", "landb_bovens":"#b3de69",
        "landb_ov": "#fccde5", "nat_bovens":"#c0bb8f", "nlev_bod":"#bc80bd", "overst":"#ccebc5", "rijkswat":"#ffed6f", "rwzi_afw":"#F1DBB9", "rwzi":"#24b5a1",
        "ua_kwel":"#7591b0", "ua_nat":"#d090a9" , "combin": "#D3D3D3"}

        #database queries (gid should come from the wps depending on the user selection)
        n_query = "SELECT * FROM wur.data_zomer_n where ST_Within(ST_PointFromText('POINT({} {})','{}'), geom)".format(xk, yk, 28992)
        p_query = "SELECT * FROM wur.data_zomer_p where ST_Within(ST_PointFromText('POINT({} {})','{}'), geom)".format(xk, yk, 28992)
        name_query =  "SELECT aquarein_p FROM wur.data_zomer_p where ST_Within(ST_PointFromText('POINT({} {})','{}'), geom)".format(xk, yk, 28992)

        #sql
        cf = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../config/pgconnection.txt')
        engine = sql_engine(cf)


        # try:
        #Nitrogen
        n_data = engine.execute(n_query)
        name_plot = engine.execute(name_query).fetchone()
        if name_plot == None:
            raise Exception("Please select a point within the available areas. ")

        nitrogen = Pie_plot("Stikstof", "n", n_data, engine, color_dict)
        p_n = nitrogen.plot()

        #Phosphorus
        p_data = engine.execute(p_query)
        nitrogen = Pie_plot("Fosfor", "p", p_data, engine, color_dict)
        p_p = nitrogen.plot()

        # #combine both plots in one layout
        p = row(p_n,p_p)
        tmpfile = getTempFile(PLOTS_DIR)
        output_file(tmpfile)
        save(p)

        # Send back result JSON
        values['url_plot'] = APACHE_DIR + os.path.basename(tmpfile)
        values['plot_xsize'] = 1020
        values['plot_ysize'] = 500

        return values
