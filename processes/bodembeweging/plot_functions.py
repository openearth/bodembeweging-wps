import pandas as pd
import os
from os.path import realpath,dirname
from bokeh.plotting import figure, ColumnDataSource, show, output_file, save
from bokeh.models import HoverTool, Legend
import time
# from pyproj import Proj, transform
import configparser
import psycopg2

# select a palette
from bokeh.palettes import Set3_12 as palette



dir_path = dirname(realpath(__file__))


# Read default configuration from file
def readConfig():
    # Default config file (relative path)
    cfile=os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../config/bodembeweging.txt')
    cf = configparser.RawConfigParser()
    cf.read(cfile)
    plots_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), cf.get('Bokeh', 'plots_dir')) # gives the absolute path of the plots dir
    apache_dir = cf.get('Bokeh', 'apache_dir')
    return plots_dir, apache_dir

       
def postgis_config(fn, section='PostgreSQL'):
    """Secrets parser."""
    config = configparser.ConfigParser()
    config.read(fn)
    secrets = {key: value for (key, value) in config.items(section)}
    return secrets


def get_soil_data(locid,fn):
    """ Connect to the PostgreSQL database server """
    conn = None
    try:
        # read connection parameters
        params = postgis_config(fn)
 
        # connect to the PostgreSQL server
        print('Connecting to the PostgreSQL database...')
        conn = psycopg2.connect(**params)
        cur = conn.cursor()
        
        # #OLD closest point to a given point
        # soildata = """
        #            SELECT l.locationkey, l.x, l.y, b.boreholekey,  c.colorkey, c.soiltype, c.depth
        #             FROM common.location l
        #             JOIN subsurface.borehole b ON l.locationkey=b.locationkey
        #             JOIN subsurface.soillayer c ON b.boreholekey = c.boreholekey
        #             WHERE l.locationkey = 
        #                 (SELECT l.locationkey
        #                 FROM common.location l
        #                 WHERE l.infotype = 'borehole'
        #                 ORDER BY l.geom <-> st_setsrid(st_makepoint({x},{y}),28992)
        #                 LIMIT 1);      
        #          """.format(x=x,y=y)
        
        soildata = """
                    SELECT l.locationkey, l.x, l.y, b.boreholekey,  c.colorkey, c.soiltype, c.depth
                    FROM common.location l
                    JOIN subsurface.borehole b ON l.locationkey=b.locationkey
                    JOIN subsurface.soillayer c ON b.boreholekey = c.boreholekey
                    WHERE b.locationkey = {locid}
                    """.format(locid=locid)
        cur.execute(soildata) 
        # print query result
        res = cur.fetchall()
        return(res)

       # close the communication with the PostgreSQL
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
            print('Database connection closed.')


# def change_coords(px, py, epsgin='epsg:3857', epsgout='epsg:4326'):
#     outProj = Proj(init=epsgout)
#     inProj = Proj(init=epsgin)
#     return transform(inProj, outProj, px, py)


def plot_bore_log(locid,plot_dir,fn):
    'Bar plot of the log data'
    
    res = get_soil_data(locid,fn)
    log = pd.DataFrame(res, columns =['locationkey', 'x', 'y', 'boreholekey', 'colorkey', 'soiltype', 'depth']) 
    log.sort_values(by=['depth'],ascending=False,inplace = True)

    types = []
    colorLookupTable = {'-': '#d8d8d8', 'bst': '#d8d8d8','gm': '#d8d8d8', 'gy': '#d8d8d8',
        'gz2': '#737373', 'g z3': '#666666', 'ho': '#85573d', 'ks1': '#99cc99','ks2': '#7fbf7f',
        'ks3': '#66b266', 'ks4':'#4ca64c', 'kz1': '#c7dd8a', 'kz2': '#bed776','kz3': '#b5d262',
        'lz3': '#3a2316', 'nbe':'#d8d8d8', 'stn': '#b8b09b', 'vcl': '#d8d8d8','vk1': '#836e5e',
        'vk3': '#745c4a', 'vkm':'#654a36', 'voh': '#d8d8d8', 'vz3': '#5a4230','z': '#ffff7f',
        'zk': '#ffff7f', 'zs1':'#ffff7f', 'zs1matig gesort"': '#ffff7f', 'zs2': '#e5e572','zs3': '#cccc65', 'zs4': '#b2b258' }
    
    
    patchX = []
    patchY = []
    colors = []
    n=0
    d=15
    
   # create a color iterator
    # color_pal = itertools.cycle(palette) 
   
    #since we have single depths here we define screens between the current and next point
    # for i,c in zip(range(log.shape[0]-1),color_pal):
    for i in range(log.shape[0]-1):
        y1 = log.iloc[i][6]
        y2 = log.iloc[i+1][6]
        type_str = log.iloc[i][5]
        types.append(type_str)
        colors.append(colorLookupTable[type_str])
        # colors.append(c)
        patchX.append([n, n, d, d])
        patchY.append([y2,y1, y1, y2])

    # - Source data dict
    source = ColumnDataSource(data=dict(
        types = types,
        x=patchX,
        y=patchY,
        color=colors,
    ))
    
    TOOLS = 'pan,wheel_zoom,box_zoom,reset,hover,save'
    p = figure(plot_width=350, plot_height=500,
               title='Bore log', tools=TOOLS)
    p.toolbar.logo = None
    p.grid.grid_line_color = '#d3d3d3'
    p.patches('x', 'y', source=source, fill_color= 'color',
              line_color='white', line_width=0.7, alpha=0.8, legend ='types' )

    p.legend.visible = False
    # p.legend.background_fill_alpha = 0.5

    lg = Legend(items=list(p.legend[0].items), location="bottom_right")

    p.add_layout(lg, 'right')
    p.xaxis.visible = False
    p.yaxis.axis_label = 'Depth'

    # - Mouse hover
    hover = p.select_one(HoverTool)
    hover.point_policy = 'follow_mouse'
    hover.tooltips = '''
    <div>
        <div>
            <span style='font-size: 12px;font-weight: bold;'>Layer:</span>
            <span style='font-size: 12px; color: #777777;'>@types</span>
        </div>
        <div>
            <span style='font-size: 12px;font-weight: bold;'>Depth (m):</span>
            <span style='font-size: 12px; color: #777777;'>$y</span>
        </div>
    </div>
    '''
    # show(p)
    # - Output HTML
    out_file = os.path.join(plot_dir, 'plot_{}.html'.format(int(time.time())))
    print('borehole html',out_file)
    output_file(out_file)
    save(p)
    return out_file


# if __name__ == '__main__':
#     db_config = r'..\..\config\bodembeweging.txt'
#     # fl = os.path.join(r'D:\new_orleans_viewer\pywps\data', plot_fn)
#     plot_dir = r'..\..\data\bodembeweging'
#     plot_bore_log(108655,446122,plot_dir,db_config)

