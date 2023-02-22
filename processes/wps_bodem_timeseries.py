# -*- coding: utf-8 -*-
# Copyright notice
#   --------------------------------------------------------------------
#   Copyright (C) 2020 Deltares
#       Lilia Angelova
#       lilia.angerlova@deltares.nl
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

# $HeadURL: $
# $Keywords: $
# http://localhost:5000/wps?request=Execute&service=WPS&identifier=bodemtime_plots&version=1.0.0&datainputs=location=526132,6803355
# PyWPS

# http://localhost:5000/wps?request=GetCapabilities&service=WPS&version=1.0.0
# http://localhost:5000/wps?request=DescribeProcess&service=WPS&version=1.0.0&Identifier=bodembore_plots
import logging
import simplejson as json
from pywps import Process, Format
from pywps.inout.inputs import LiteralInput
from pywps.inout.outputs import ComplexOutput
from pywps.app.Common import Metadata
import os

# local
from processes.bodembeweging.insar_ts import getcl_ts
from processes.bodembeweging.plot_functions import readConfig

logger = logging.getLogger('PYWPS')
dirname = os.path.dirname(__file__)

class BodemTimeseriesPlots(Process):

    def __init__(self):
        # Input [in json format ]
        inputs = [LiteralInput('location', abstract="input=mapselection",
                                            data_type='string')]

        # Output [in json format]
        outputs = [ComplexOutput('output_html',
                                 'output plot',
                                  supported_formats=[Format('application/json')])]

        super(BodemTimeseriesPlots, self).__init__(
            self._handler,
            identifier='bodemtime_plots',
            version='1.0',
            title='',
            abstract="""""",
            profile='',
            metadata=[Metadata('BodemTimeseriesPlots'), Metadata('')],
            inputs=inputs,
            outputs=outputs,
            store_supported=False,
            status_supported=False
        )

    ## MAIN
    def _handler(self, request, response):
        try:
            # Read input
            loc = request.inputs["location"][0].data.split(',')     
           
            #db connection params
            PLOTS_DIR, APACHE_DIR = readConfig()
            
            # plot_dir = os.path.join(dirname, r'../data/bodembeweging')
           
            if not os.path.isdir(PLOTS_DIR):
                os.makedirs(PLOTS_DIR)
                
            db_config = os.path.join(dirname,'./opt/pywps/config/bodembeweging.txt')
            location = loc[0],loc[1]
            begin_date = '1900-01-01'
            end_date = '2020-06-01'
            values = getcl_ts(PLOTS_DIR,begin_date,end_date,location,db_config,'relhoogte')            
            # Set output
            response.outputs["output_html"].data = APACHE_DIR + os.path.basename(values)

        except Exception as e:
            res = { 'error_html' : 'ERROR: {}'.format(e) }
            print('''WPS [failed execution]: ERROR = {}'''.format(e))
            response.outputs['output_html'].data = json.dumps(res)

        return response


