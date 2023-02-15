# -*- coding: utf-8 -*-
"""
Created on Fri Jun  5 10:06:49 2020

@author: hendrik_gt

#  Copyright notice
#   --------------------------------------------------------------------
#   Copyright (C) 2020 Deltares for bodembewegingen.nl based on FEWS datamodel in 
#                 PostgreSQL/PostGIS database used in Water Information Systems
#   Gerrit Hendriksen@deltares.nl
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

# $Id: loadtimeseriesdata.py 16367 2020-05-06 07:42:48Z hendrik_gt $
# $Date: 2020-05-06 09:42:48 +0200 (wo, 06 mei 2020) $
# $Author: hendrik_gt $
# $Revision: 16367 $
# $HeadURL: https://svn.oss.deltares.nl/repos/openearthtools/trunk/python/applications/datamodels/subsurface/loadtimeseriesdata.py $
# $Keywords: $
"""

import os
# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker
from bokeh.plotting import figure, output_file, show, ColumnDataSource, save
from bokeh.models import HoverTool
import time

from .plot_functions import readConfig
from .plot_functions import postgis_config
import psycopg2

# def createengine(fc):
#     f = open(fc)
#     engine = create_engine(f.read(), echo=False,pool_size=10, max_overflow=20)
#     f.close()
#     # engine = create_engine(cfile)    
#     Session = sessionmaker(bind = engine)
#     session = Session()
#     # session.rollback()
#     return session

   
def getlocationid(location, parameter, cfile):    
    conn = None
    try:
        # read connection parameters
        params = postgis_config(cfile)
 
        # connect to the PostgreSQL server
        # print('Connecting to the PostgreSQL database...')
        conn = psycopg2.connect(**params)
        cur = conn.cursor()
    
    # session = createengine(cfile)

        lon,lat = location
        strSql = """select l.locationkey, l.name,ST_distance(geom
                 ,st_transform(st_setsrid(st_makepoint({lon},{lat}),4326),28992)) as distance
                 from common.location l
                 join timeseries.timeseries ts on ts.locationkey = l.locationkey
                 join common.parameter p on p.parameterkey = ts.parameterkey
                 where p.id = '{p}'
                 order by distance
                 limit 1""".format(lon=lon,lat=lat,p=parameter)
                 
        cur.execute(strSql) 
        # print query result
        pid,name,distance = cur.fetchall()[0]            
        # pid,name,distance = session.execute(strSql).fetchall()[0]
        return pid,name
       # close the communication with the PostgreSQL
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
            # print('Database connection closed.')

def getdata(pid, begin_date, end_date, cfile, parameter):
    conn = None
    try:
        # read connection parameters
        params = postgis_config(cfile)
 
        # connect to the PostgreSQL server
        # print('Connecting to the PostgreSQL database...')
        conn = psycopg2.connect(**params)
        cur = conn.cursor()
    
    # session = createengine(cfile)

        strSql = """
            select d.datetime,d.scalarvalue from timeseries.timeseriesvaluesandflags d
            join timeseries.timeseries ts on ts.serieskey = d.serieskey
            join common.location l on l.locationkey = ts.locationkey
            join common.parameter p on p.parameterkey = ts.parameterkey
            where l.locationkey = {pid} and datetime between '{sd}'::timestamp and '{ed}'::timestamp
            and p.id = '{param}'
            order by d.datetime""".format(pid=pid,sd=begin_date,ed=end_date,param=parameter)
                 
        cur.execute(strSql) 
        # print query result
        data = cur.fetchall()    
        # pid,name,distance = session.execute(strSql).fetchall()[0]
        return data
       # close the communication with the PostgreSQL
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
            # print('Database connection closed.')
    
def getcl_ts(plot_dir,begin_date, end_date, location, cfile, parameter):
    """ begin_date  = from date (date)
        end_date    = to date (date)
        begin_depth = from depth this should be the top depth (float)
        end_depth   = to depth this should be the bottom depth (float)
        location    = list with lon, lat
        
        bear in mind location is in wgs84
    """
    pf = ''

    pid,name = getlocationid(location,parameter,cfile)
    # if parameter == 'relhoogte':
    e = getdata(pid,begin_date,end_date, cfile, parameter)
    for i in e:
        elev = i[1]
    pf = '(NAP hoogte {e})'.format(e=str(elev))

    properties = {}
    properties['x'] = location[0]
    properties['y'] = location[1]
    properties['id'] = id 
    
    res = e
    dates = []
    values = []
    for i in res:
        dates.append(i[0])
        values.append(i[1])
        
    source = ColumnDataSource(data=dict(
        x=dates,
        y=values,
        ))
    
    TOOLS = 'pan,wheel_zoom,box_zoom,reset,save'
    p = figure(title=' '.join([parameter,'data for location',name,pf]), plot_width=500, plot_height=500, x_axis_type="datetime", tools = TOOLS)
    
    c = p.circle(x=dates, y=values, fill_color="blue", size=4.5)
    

    p.add_tools(HoverTool(
    renderers = [c],   
    mode = 'vline',
    tooltips=[
        ( 'Date',   '@x{%Y-%m-%d}'            ),
        ( 'Depth',  '@{y}{0.33f}' ), # use @{ } for field names with spaces
    ],
    formatters={
        'x'      : 'datetime', # use 'datetime' formatter for 'date' field
        'y' : 'numeral',   # use default 'numeral' formatter for other fields                                  
    }
    ))
    p.line(x='x', y='y', source = source, line_dash= 'dotted', line_width=2.5)
    
    out_file = os.path.join(plot_dir, 'plot_{}.html'.format(int(time.time())))
    output_file(out_file)
    save(p)
    return out_file


# if __name__ == "__main__":
#     cfile = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..\..\config\connection_bodemdata.txt')
#     plot_dir = r'D:\Bodembeweging\BackEnd\data\bodembeweging'
#     location = (526132,6803355)
#     begin_date = '1900-01-01'
#     end_date = '2020-06-01'
#     getcl_ts(plot_dir,begin_date,end_date,location,cfile,'relhoogte')



