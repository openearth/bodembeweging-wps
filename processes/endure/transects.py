# core
import os
import math
import tempfile
import logging
import time as tt
import configparser

# modules
import types
import simplejson as json


try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

# relative
from processes.endure.utils import *
from processes.common.coords import change_coords
from processes.endure.bokeh_plots import bokeh_Plot
from .slreffects import queryPostGISClosestPoint




def enduretransectinformation(location):
    PLOTS_DIR, APACHE_DIR, ENGINE, IMG_DIR = readConfig()
    # Output prepare
    json_output = StringIO()
    values = {}
    data_error = False

    
    # Input (coordinates) - OpenLayers 3857
    epsg = 3857
    epsgin = 'epsg:'+str(epsg)
    location_info = json.loads(location)
    (xin,yin) = location_info['x'], location_info['y']

    # convert coordinates to latlon
    logging.info('''Input Coordinates {} {} in epsg={}'''.format(xin,yin,epsgin))
    (lon,lat) = change_coords(xin, yin, epsgin=epsgin, epsgout='epsg:4326')

    # Query DB, get transect, make plot
    # Select transect [closest]
    fields = 'transect_id, initial_lon, final_lon, initial_lat, final_lat, distance, change_rate, change_rate_unc, outliers, flag_sandy, country, intercept, time, b_unc'
    table = 'endure_transects_interreg'
    where = None
    transect_id, lon1, lon2, lat1, lat2, distance, change_rate, change_rate_unc, outliers, flag_sandy, country, intercept, time, b_unc, distclick = queryPostGISClosestPoint(ENGINE, lon, lat, fields, table, where)
    logging.info('INFO: selected transect with id={}'.format(transect_id))
    dirname = str(tt.time()).replace('.','')
    if not os.path.isdir(PLOTS_DIR):
        os.makedirs (PLOTS_DIR)
    temp_html = os.path.join(PLOTS_DIR, dirname+'.html')
    
    # Plot
    p = bokeh_Plot(temp_html)
    p.generate_plot(transect_id, distance, change_rate, change_rate_unc, outliers, flag_sandy, country, intercept, time, b_unc)



    # Output prepare
    if data_error:
        values['error_html'] = "<p>No transect found near the selected location. Please click on the Select on map button.</p>"
    else:
        values['title'] = """Shoreline transect with id={}""".format(transect_id)
        values['url_plot'] = APACHE_DIR + dirname +'.html'
        values['title'] = 'Shoreline transect plot'
        values['plot_xsize'] = 650
        values['plot_ysize'] = 370
        values['wkt_linestr'] = 'LINESTRING ({x0} {y0}, {x1} {y1})'.format(x0=lon1, x1=lon2, y0=lat1, y1=lat2)
    return values
