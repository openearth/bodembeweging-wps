# -*- coding: utf-8 -*-
# Copyright notice
#   --------------------------------------------------------------------
#   Copyright (C) 2019 Deltares
#       Joan Sala, Gerrit Hendriksen
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

# $Id: 3dDEM.py 14134 2018-01-31 07:01:10Z sala $
# $Date: 2018-01-31 08:01:10 +0100 (Wed, 31 Jan 2018) $
# $Author: sala $
# $Revision: 14134 $
# $HeadURL: https://svn.oss.deltares.nl/repos/openearthtools/trunk/python/applications/wps/endure/3dDEM.py $
# $Keywords: $

# core
import os
import operator
import math
import configparser
import time as tt

# modules
from sqlalchemy import create_engine
from pyproj import Proj, transform

import types
import simplejson as json
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

from processes.common.coords import change_coords
from .utils import readConfig

"""
This is a redesigned WPS for the endure application

Filename used to be mockup.py --> changed to slreffect.py
"""

def slreffects(returnperiod,sealevelrise,location_info):
    # Read configuration file
    PLOTS_DIR, APACHE_DIR, ENGINE, IMG_DIR = readConfig()
    returnp = returnperiod.split(' ')[0]
    sealevel = sealevelrise.split(' ')[0]
    # Outputs prepare
    outdata = StringIO()
    values = {}
    data_error = False

    
      # Inputs check
    (xin,yin) = location_info['x'], location_info['y']
    

    # convert coordinates to latlon
    print('''Input Coordinates {} {} in epsg={}'''.format(xin,yin,'3857'))
    (lon,lat) = change_coords(xin, yin, epsgin='epsg:3857', epsgout='epsg:4326')
    

    # Select transect [closest]
    #fields = 'transect,scenario,SLR,RP,regime,description,lon1,lon2,lat1,lat2,bruun,dhigh,dlow,beachslope,accomodation,SSL,Hs,Tp,regimepngname_current,resultpngname_current,regimepngname_SLR,resultpngname_SLR,wavepngname,desc_regime_slr'
    fields = 'transect,scenario,slr,rp,regime,description,lon1,lon2,lat1,lat2,bruun,dhigh,dlow,beachslope,accomodation,ssl,hs,tp,regimepngname_current,resultpngname_current,regimepngname_slr,resultpngname_slr,wavepngname,desc_regime_slr'
    table = 'endure_transects'
    where = 'slr = \'{slr}\' and rp = \'{rp}\''.format(slr=sealevel, rp=returnp)
    print('INFO: where statement {}'.format(where))
    transect, scenario, SLR, RP, regime,description, lon1, lon2, lat1, lat2, bruun, dhigh, dlow, beachslope, accomodation, SSL, Hs, Tp, regimepngname_current, resultpngname_current,regimepngname_SLR, resultpngname_SLR, wavepngname, desc_regime_slr, distclick = queryPostGISClosestPoint(ENGINE, lon, lat, fields, table, where)
    print('INFO: selected transect with id={}'.format(transect))
    
    # Generate html file name
    fname = str(tt.time()).replace('.','')+'.html'
    # Create html file path if not exist
    
    if not os.path.isdir(PLOTS_DIR):
      os.makedirs (PLOTS_DIR)

    temp_html = os.path.join(PLOTS_DIR, fname)
      
    generateHtml(temp_html, IMG_DIR, regimepngname_current, resultpngname_current, regimepngname_SLR, resultpngname_SLR, wavepngname, description, SSL, beachslope, bruun, dhigh, Hs, Tp,desc_regime_slr)
      
      
    
        
        
    
    # Output prepare
    values = {}
    if data_error:
        values['error_html'] = "<p>Please click on the Select on map button to specify the location.</p>"
    else:
        values['url_plot'] = APACHE_DIR + fname
        values['plot_xsize'] = 700
        values['plot_ysize'] = 500
        values['title'] = 'Selected scenario: Sea level rise of {} and a return period of {}'.format(sealevelrise, returnperiod)
        values['wkt_linestr'] = 'LINESTRING ({x0} {y0}, {x1} {y1})'.format(x0=lon1, x1=lon2, y0=lat1, y1=lat2)

    json_str = json.dumps(values)
    outdata.write(json_str)
    return json_str



# Get closest point to user click [shoreline transects]
def queryPostGISClosestPoint(engine, xk, yk, fields, table, where, epsg=4326):

    # I know it is not ideal but...
    if where == None:
        where = '1 = 1'

    # Look for closes transect ()
    sql = """SELECT {ff}, ST_Distance(ST_PointFromText('POINT({x} {y})','{e}'), geom) as clickdist
             FROM {t}
             WHERE {ww}
             ORDER BY clickdist
             LIMIT 1
            """.format(ff=fields, x=xk, y=yk, e=epsg, t=table, ww=where)
    res = engine.execute(sql)

    # TRANSECT DB info
    for r in res:
        return r
    return False # not found

# Generate html with tabs
def rr(f):
    try:
        return round(float(f),1)
    except:
        return f

def generateHtml(temp_html, img_dir, regimepngname_current, resultpngname_current, regimepngname_SLR, resultpngname_SLR, wavepngname, description, SSL, beachslope, bruun, dhigh, Hs, Tp,desc_regime_slr):
    html_str = '''<head>
      <link rel="stylesheet" type="text/css" href="https://endure.openearth.eu/endure/site/css/transect_tab.css">
    </head>

    <body onload="openTab(event, 'statslr')">
      <script src="https://endure.openearth.eu/endure/site/js/transect_tab.js"></script>

      <!-- Tab links -->
      <div class="tab">
        <button class="tablinks" onclick="openTab(event, 'statcur')">Current state</button>
        <button class="tablinks" onclick="openTab(event, 'regcur')">Current regime</button>
        <button id="defaultOpen" class="tablinks" onclick="openTab(event, 'statslr')">State + SLR</button>
        <button class="tablinks" onclick="openTab(event, 'regslr')">Regime + SLR</button>
        <button class="tablinks" onclick="openTab(event, 'background')">Background</button>
        <button class="tablinks" onclick="openTab(event, 'summary')">Parameters</button>
      </div>

      <!-- Tab content -->
      <div id="statcur" class="tabcontent">
        <img src="{img_dir}{rescur}" style="height: 370px; width: 670px" alt="current status">
      </div>

      <div id="regcur" class="tabcontent">
        <p>{desc}</p>
        <img src="{img_dir}{regcur}" style="width: 670px" alt="current regime">
        <p class="stext">Source of figure: Goslin, Jerome & Clemmensen, Lars. (2017). Proxy records of Holocene storm events in coastal barrier systems: Storm-wave induced markers. Quaternary Science Reviews. 174. 80-119. <a href"https://www.sciencedirect.com/science/article/abs/pii/S0277379117305516" target="_blank">10.1016/j.quascirev.2017.08.026</a></p>
      </div>

      <div id="statslr" class="tabcontent">
        <img src="{img_dir}{resslr}" style="height: 370px; width: 670px" alt="slr status">
      </div>

      <div id="regslr" class="tabcontent">
        <p>{desc_slr}</p>
        <img src="{img_dir}{regslr}" style="width: 670px" alt="slr regime">
        <p class="stext">Source of figure: Goslin, Jerome & Clemmensen, Lars. (2017). Proxy records of Holocene storm events in coastal barrier systems: Storm-wave induced markers. Quaternary Science Reviews. 174. 80-119. <a href"https://www.sciencedirect.com/science/article/abs/pii/S0277379117305516" target="_blank">10.1016/j.quascirev.2017.08.026</a></p>
      </div>

      <div id="background" class="tabcontent">
        <div id="content" class="row">
            <div class="scolumn">
                <p class="stext">The Swash regime describes a storm where wave runup is confined below the dune foot. During a storm the foreshore typically erodes and recovers afterwards.</p>
                <p class="stext">The Collision regime during is describing a storm where the wave runup exceeds the dune foot, but is below the top of the dune. The front of the dune is impacted by the storm.</p>
                <p class="stext">The Overwash regime describes a storm where wave runup overtops the top of the dune. Because of this sediment is transported landwards, the overtopping waves may lead to flooding issues in the hinterland.</p>
                <p class="stext">The Inundation regime describes a storm where the storm surge is sufficient to completely and continuously submerge the dune system. A lot of sediment is transported landward and there if significant flooding of the hinterland.</p>
                <p class="stext">Source of figures: Goslin, Jerome & Clemmensen, Lars. (2017). Proxy records of Holocene storm events in coastal barrier systems: Storm-wave induced markers. Quaternary Science Reviews. 174. 80-119. <a href"https://www.sciencedirect.com/science/article/abs/pii/S0277379117305516" target="_blank">10.1016/j.quascirev.2017.08.026</a></p>
            </div>
            <div class="bcolumn">
             <img src="{img_dir}{allreg}" style="width: 450px" alt="slr regime">
            </div>
            <br style="clear:both;"/>
        </div>
      </div>

      <div id="summary" class="tabcontent">
        <table style="width:100%">
          <tr>
            <th style="text-align: left">Parameter</th>
            <th style="text-align: left">Value</th>
            <th style="text-align: left">Units</th>
          </tr>
          <tr>
            <td>Storm surge level</td><td>{ssl}</td><td>meters</td>
          </tr>
          <tr>
            <td>Beach slope</td><td>{beachslope}</td><td>1/meters</td>
          </tr>
          <tr>
            <td>Dune retreat</td><td>{bruun}</td><td>meters</td>
          </tr>
          <tr>
            <td>Maximum runup height</td><td>{dhigh}</td><td>meters</td>
          </tr>
          <tr>
            <td>Offshore wave height</td><td>{hs}</td><td>meters</td>
          </tr>
          <tr>
            <td>Offshore wave period</td><td>{tp}</td><td>seconds</td>
          </tr>
        </table>
      </div>
    </body>'''.format(img_dir=img_dir, regcur=regimepngname_current, rescur=resultpngname_current, regslr=regimepngname_SLR, resslr=resultpngname_SLR, allreg='all_regimes.png', desc=description, ssl=rr(SSL), beachslope=rr(beachslope), bruun=rr(bruun), dhigh=rr(dhigh), hs=rr(Hs), tp=rr(Tp),desc_slr=desc_regime_slr)
    # Write to file
    with open(temp_html, "w") as tf:
        tf.write(html_str)
