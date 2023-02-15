# -*- coding: utf-8 -*-
# Copyright notice
#   --------------------------------------------------------------------
#   Copyright (C) 2020 Deltares
#       Gerrit Hendriksen
#       gerrit.hendriksen@deltares.nl
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


# $Keywords: $
# 
# PyWPS

# http://localhost:5000/wps?request=GetCapabilities&service=WPS&version=1.0.0
# http://localhost:5000/wps?request=DescribeProcess&service=WPS&version=1.0.0&Identifier=endure_slreffects


from pywps import Process, Format
from pywps.inout.inputs import ComplexInput, LiteralInput
from pywps.inout.outputs import ComplexOutput
from pywps.app.Common import Metadata

# local
from .endure.slreffects import slreffects
from .endure.transects import enduretransectinformation


#other
import json
class ENDURESlrEffects(Process):

    def __init__(self):
        # Input [in json format ]
        inputs = [LiteralInput('return_period', 'User specified returnperiod', data_type='string', abstract = 'input=dropdownmenu', min_occurs = "0",
                                max_occurs = "1", allowed_values = ["100 years", "1000 years"], default = "100 years"),
                  LiteralInput('sealevel_rise', 'User specified sealevelrise', data_type='string', abstract = "input=dropdownmenu",  min_occurs = "0",
                                max_occurs = "1", allowed_values = ["0.5 metre", "1 metre", "2 metres"], default = "1 metre"),
                  LiteralInput('location', 'User specified location', data_type='string', abstract = "input=mapselection", uoms = ["point"], min_occurs = "0",
                                max_occurs = "1" )] 
                 
                
        # Output [in json format]
        outputs = [ComplexOutput('output_html',
		                         'ENDURE SLR Effects for profile as html page',
		                         supported_formats=[Format('application/json')])]

        super(ENDURESlrEffects, self).__init__(
		    self._handler,
		    identifier='endure_slreffects',
		    version='1.0',
		    title='Sea level rise effects',
		    abstract="""Discover the effect of sea level rise (SLR) for predefined profiles at various '2 Seas Area' locations.
                      Check for more information Background tab on the info page.""",
		    profile='',
		    metadata=[Metadata('ENDURESlrEffects'), Metadata('ENDURE/slreffects')],
		    inputs=inputs,
		    outputs=outputs,
		    store_supported=True,
		    status_supported=True
		)

    ## MAIN
    def _handler(self, request, response):
        try:
            # Read input
            returnperiod = request.inputs["return_period"][0].data.split(' ')[0]
            sealevelrise = request.inputs["sealevel_rise"][0].data.split(' ')[0]
            location_info_data = request.inputs["location"][0].data
            location_info_json = json.loads(location_info_data)

            # call the code that does the magic
            html = slreffects(returnperiod,sealevelrise,location_info_json)

            # Set output
            response.outputs['output_html'].data = html 

        except Exception as e:
            res = { 'errMsg' : 'ERROR: {}'.format(e) }
            print('''WPS [ENDURESlrEffects]: ERROR = {}'''.format(e))
            response.outputs['output_html'].data = res

        return response



class ENDUREShorelineTransect(Process):

    def __init__(self):
        # Input [in json format ]
        inputs = [LiteralInput('location', 'Click to select a location on the coast (NL,UK,FR).', data_type='string', abstract = "input= mapselection",
                                uoms = ["point"], min_occurs = "0", max_occurs = "1" )]

        # Output [in json format]
        outputs = [ComplexOutput('output_html',
		                         'ENDURE shorelinetransect characteristics for selected profile as html page.',
		                         supported_formats=[Format('application/json')])]

        super(ENDUREShorelineTransect, self).__init__(
		    self._handler,
		    identifier='endure_shorelinetransect',
		    version='1.0',
		    title='Shoreline changes (1985-2016)',
		    abstract="""Discover Long term changes of shoreline profiles for the 2 Seas area as derived from satellite imagery.
                      Check for more information Background tab on the info page.""",
		    profile='',
		    metadata=[Metadata('ENDUREShorelineTransect'), Metadata('ENDURE/shorelinetransect')],
		    inputs=inputs,
		    outputs=outputs,
		    store_supported=True,
		    status_supported=True
		)

    ## MAIN
    def _handler(self, request, response):
        try:
            # Read input
            location_info_data = request.inputs["location"][0].data

            # call the code that does the magic
            html = enduretransectinformation(location_info_data)
            
            # Set output
            response.outputs['output_html'].data = json.dumps(html)
        except Exception as e:
            res = { 'errMsg' : 'ERROR: {}'.format(e) }
            print('''WPS [ENDURESlrEffects]: ERROR = {}'''.format(e))
            response.outputs['output_html'].data = res

        return response
