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

# PyWPS

# http://localhost:5000/wps?request=GetCapabilities&service=WPS&version=1.0.0
# http://localhost:5000/wps?request=DescribeProcess&service=WPS&version=1.0.0&Identifier=endure_slreffects
import logging
from pywps import Process, Format
from pywps.inout.inputs import LiteralInput
from pywps.inout.outputs import ComplexOutput
from pywps.app.Common import Metadata

# local
from processes.nutrientenmaas.krw_tseries import krw_tseries
from processes.nutrientenmaas.avgtseries_meetnet import avg_tseries
from processes.nutrientenmaas.krw_tseries_doelgat import tserie_doelgat
from processes.nutrientenmaas.meetlocaties import ts_mnlso
from processes.nutrientenmaas.meetlocaties_nitraat import nitraat_app
from processes.nutrientenmaas.pie_chart import pie_chart

logger = logging.getLogger('PYWPS')

import simplejson as json

class NutrientenmaasKRWtseries(Process):

    def __init__(self):
        # Input [in json format ]
        inputs = [LiteralInput('location', 'User specified location', data_type='string', uoms = ["point"]),
                  LiteralInput('param', 'User specified parameter', data_type='string', allowed_values=["N-totaal", "P-totaal"])]

        # Output [in json format]
        outputs = [ComplexOutput('output_html',
                                 'meet reeksen KRW locaties',
                                  supported_formats=[Format('application/json')])]

        super(NutrientenmaasKRWtseries, self).__init__(
            self._handler,
            identifier='krw_tseries',
            version='1.0',
            title='Toon meetreeks op locaties van de Kaderrichtlijn Water',
            abstract="""Deze functie maakt het mogelijk om per KRW-meetlocatie een meetreeks weer te geven van nitraat of fosfaat""",
            profile='',
            metadata=[Metadata('NutrientenmaasKRWtseries'), Metadata('nutrientenmaas/krw_tseries')],
            inputs=inputs,
            outputs=outputs,
            store_supported=False,
            status_supported=False
        )

    ## MAIN
    def _handler(self, request, response):
        try:
            # Read input
            location_info = request.inputs["location"][0].data.split(' ')[0]
            param = request.inputs["param"][0].data.split(' ')[0]

            # call the code that does the magic
            values = krw_tseries(location_info, param)

            # Set output
            response.outputs['output_html'].data = json.dumps(values)

        except Exception as e:
            res = { 'error_html' : 'ERROR: {}'.format(e) }
            print('''WPS [fout bij het maken van tijdreeks KRW locatie]: ERROR = {}'''.format(e))
            response.outputs['output_html'].data = json.dumps(res)

        return response


class NutrientenmaasAVGtseries(Process):

    def __init__(self):
        # Input [in json format ]
        inputs = [LiteralInput('location', 'User specified location', data_type='string', uoms = ["point"])]


        # Output [in json format]
        outputs = [ComplexOutput('output_html',
                                 'gemiddelde meetreeksen krw locaties',
                                  supported_formats=[Format('application/json')])]

        super(NutrientenmaasAVGtseries, self).__init__(
            self._handler,
            identifier='avgtseries_meetnet',
            version='1.0',
            title='Landelijk meetnet grondwater',
            abstract="""Landelijk meetnet grondwater bevat data van het landelijk meetnet grondwater. De tool maakt het het mogelijk om NO3, NH4+ en P-totaal per locaties op te vragen. De data wordt gepresenteerd per filter en in 3 grafieken (voor iedere parameter 1).
            De dichtstbijzijnde beschikbare locatie wordt geselecteerd.""",
            profile='',
            metadata=[Metadata('NutrientenmaasAVGtseries'), Metadata('nutrientenmaas/avgtseries_meetnet')],
            inputs=inputs,
            outputs=outputs,
            store_supported=False,
            status_supported=False
        )

    ## MAIN
    def _handler(self, request, response):
        try:
            # Read input
            location_info = request.inputs["location"][0].data.split(' ')[0]

            # call the code that does the magic
            values = avg_tseries(location_info)

            # Set output
            response.outputs['output_html'].data = json.dumps(values)

        except Exception as e:
            res = { 'error_html' : 'ERROR: {}'.format(e) }
            print('''WPS [fout bij het maken van gemiddelde tijdreeks]: ERROR = {}'''.format(e))
            response.outputs['output_html'].data = json.dumps(res)

        return response


class NutrientenmaasDoelgattseries(Process):

    def __init__(self):
        # Input [in json format ]
        inputs = [LiteralInput('location', 'User specified location', data_type='string', uoms = ["point"]),
                  LiteralInput('param', 'User specified parameter', data_type='string', allowed_values=["Stikstof", "Fosfaat"])]


        # Output [in json format]
        outputs = [ComplexOutput('output_html',
                                 'tijdserie van dichtstbijzijnde locatie',
                                  supported_formats=[Format('application/json')])]

        super(NutrientenmaasDoelgattseries, self).__init__(
            self._handler,
            identifier='krw_tseries_doelgat',
            version='1.0',
            title='KRW tijdseries',
            abstract="""Maak een tijdreeks. De dichtstbijzijnde beschikbare locatie wordt geselecteerd.""",
            profile='',
            metadata=[Metadata('NutrientenmaasDoelgattseries'), Metadata('nutrientenmaas/krw_tseries_doelgat')],
            inputs=inputs,
            outputs=outputs,
            store_supported=False,
            status_supported=False
        )

    ## MAIN
    def _handler(self, request, response):
        try:
            # Read input
            location_info = request.inputs["location"][0].data.split(' ')[0]
            param = request.inputs["param"][0].data.split(' ')[0]

            # call the code that does the magic
            values = tserie_doelgat(location_info, param)

            # Set output
            response.outputs['output_html'].data = json.dumps(values)

        except Exception as e:
            res = { 'error_html' : 'ERROR: {}'.format(e) }
            print('''WPS [fout bij het maken van tijdreeks dichtstbijzijnde locatie]: ERROR = {}'''.format(e))
            response.outputs['output_html'].data = json.dumps(res)

        return response


class NutrientenmaasMNLSOtseries(Process):

    def __init__(self):
        # Input [in json format ]
        inputs = [LiteralInput('location', 'User specified location', data_type='string', uoms = ["point"]),
                  LiteralInput('param', 'User specified parameter', data_type='string', allowed_values=["N-totaal", "P-totaal"])]


        # Output [in json format]
        outputs = [ComplexOutput('output_html',
                                 'tijdserie van mnlso locaties',
                                  supported_formats=[Format('application/json')])]

        super(NutrientenmaasMNLSOtseries, self).__init__(
            self._handler,
            identifier='meetlocaties',
            version='1.0',
            title='Meetlocaties MNLSO tijdseries',
            abstract="""Toon meetreeks van de locaties uit het Meetnet Nutrienten Landbouw Specifiek Oppervlaktewater (MNLSO)""",
            profile='',
            metadata=[Metadata('NutrientenmaasMNLSOtseries'), Metadata('nutrientenmaas/meetlocaties')],
            inputs=inputs,
            outputs=outputs,
            store_supported=False,
            status_supported=False
        )

    ## MAIN
    def _handler(self, request, response):
        try:
            # Read input
            location_info = request.inputs["location"][0].data.split(' ')[0]
            param = request.inputs["param"][0].data.split(' ')[0]


            # call the code that does the magic
            values = ts_mnlso(location_info, param)

            # Set output
            response.outputs['output_html'].data = json.dumps(values)

        except Exception as e:
            res = { 'error_html' : 'ERROR: {}'.format(e) }
            print('''WPS [fout bij tijdreesk MNLSO]: ERROR = {}'''.format(e))
            response.outputs['output_html'].data = json.dumps(res)

        return response


class NutrientenmaasNitraatapp(Process):

    def __init__(self):
        # Input [in json format ]
        inputs = [LiteralInput('location', 'User specified location', data_type='string', uoms = ["point"]),
                  LiteralInput('param', 'User specified parameter', data_type='string', allowed_values=["Nitraat meting grondwater",
                                 "Nitraat meting drainwater",
                                 "Nitraat meting plaswater",
                                 "Nitraat meting overig",
                                 "Nitraat meting oppervlaktewater"])]


        # Output [in json format]
        outputs = [ComplexOutput('output_html',
                                 'metingen nitraatapp',
                                  supported_formats=[Format('application/json')])]

        super(NutrientenmaasNitraatapp, self).__init__(
            self._handler,
            identifier='meetlocaties_nitraat',
            version='1.0',
            title='Toon Nitraat app metingen',
            abstract="""Deze functie maakt het mogelijk om Nitraat app metingen weer te geven. Meerdere metingen op dezelfde locatie worden samengevoegd in 1 meetreeks.
            Betekenis van de kleuren:
            - groen vierkant   = NO3 meting grondwater
            - rode cirkel      = NO3 meting drainwater
            - blauwgrijze ster = NO3 meting plaswater
            - grijze cirkel    = NO3 meting overig
            - blauwe driehoek  = NO3 meting oppervlaktewater""",
            profile='',
            metadata=[Metadata('NutrientenmaasNitraatapp'), Metadata('nutrientenmaas/meetlocaties_nitraat')],
            inputs=inputs,
            outputs=outputs,
            store_supported=False,
            status_supported=False
        )

    ## MAIN
    def _handler(self, request, response):
        try:
            # Read input
            location_info = request.inputs["location"][0].data
            param = request.inputs["param"][0].data

            # call the code that does the magic
            values = nitraat_app(location_info, param)

            # Set output
            response.outputs['output_html'].data = json.dumps(values)

        except Exception as e:
            res = { 'error_html' : 'ERROR: {}'.format(e) }
            print('''WPS [fout bij selectie nitraatapp metingen]: ERROR = {}'''.format(e))
            response.outputs['output_html'].data = json.dumps(res)

        return response


class NutrientenmaasPiechart(Process):

    def __init__(self):
        # Input [in json format ]
        inputs = [LiteralInput('location', 'User specified location', data_type='string', uoms = ["point"])]

        # Output [in json format]
        outputs = [ComplexOutput('output_html',
                                 'piecharts',
                                  supported_formats=[Format('application/json')])]

        super(NutrientenmaasPiechart, self).__init__(
            self._handler,
            identifier='pie_chart',
            version='1.0',
            title='Taartdiagram',
            abstract="""Maak een taartdiagram van de bronnenverdeling van N en P. Selecteer eerst een vanggebied van een KRW-lichaam.""",
            profile='',
            metadata=[Metadata('NutrientenmaasPiechart'), Metadata('nutrientenmaas/pie_chart')],
            inputs=inputs,
            outputs=outputs,
            store_supported=False,
            status_supported=False
        )

    ## MAIN
    def _handler(self, request, response):
        try:
            # Read input
            location_info = request.inputs["location"][0].data.split(' ')[0]
            # call the code that does the magic
            values = pie_chart(location_info)
            # Set output
            response.outputs['output_html'].data = json.dumps(values)

        except Exception as e:
            res = {'error_html' : 'ERROR: {}'.format(e)}
            print('''WPS [fout bij het maken van Taartdiagram]: ERROR = {}'''.format(e))
            response.outputs['output_html'].data = json.dumps(res)

        return response
