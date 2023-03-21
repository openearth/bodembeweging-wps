# -*- coding: utf-8 -*-
# Copyright notice
#   --------------------------------------------------------------------
#   Copyright (C) 2020 Deltares
#       Lilia Angelova
#       lilia.angerlova@deltares.nl

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
# http://localhost:5000/wps?request=Execute&service=WPS&identifier=bodembore_plots&version=1.0.0&datainputs=locationid=1205457
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
from processes.bodembeweging.plot_functions import *

logger = logging.getLogger('PYWPS')
dirname = os.path.dirname(__file__)

class BodemBoreholePlots(Process):

    def __init__(self):
        # Input [in json format ]
        inputs = [LiteralInput('locationid', 'User specified location', data_type='string')]

        # Output [in json format]
        outputs = [ComplexOutput('output_html',
                                 'output plot',
                                  supported_formats=[Format('application/json')])]

        super(BodemBoreholePlots, self).__init__(
            self._handler,
            identifier='bodembore_plots',
            version='1.0',
            title='',
            abstract="""""",
            profile='',
            metadata=[Metadata('BodemBoreholePlots'), Metadata('')],
            inputs=inputs,
            outputs=outputs,
            store_supported=False,
            status_supported=False
        )

    ## MAIN
    def _handler(self, request, response):
        try:
            # Read input
            locid = request.inputs["locationid"][0].data.split(' ')[0]            
           
            #db connection params
            cfile = '/opt/pywps/config/bodembeweging.txt'
            if os.path.exists(cfile):
                print('pad naar configfile gevonden')
            else:
                print('misschien toch beter een ander pad gebruiken')
            db_config = cfile
            PLOTS_DIR, APACHE_DIR = readConfig()
                       
            if not os.path.isdir(PLOTS_DIR):
                os.makedirs(PLOTS_DIR)
            
            values = plot_bore_log(locid,PLOTS_DIR,db_config)

            # Set output
            response.outputs["output_html"].data = APACHE_DIR + os.path.basename(values)

        except Exception as e:
            res = { 'error_html' : 'ERROR: {}'.format(e) }
            print('''WPS [failed execution]: ERROR = {}'''.format(e))
            response.outputs['output_html'].data = json.dumps(res)

        return response


