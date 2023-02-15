# WPS Services
*WPS for Bodemweging application

For deployment you should:
- Add your wps processes in the processes folder
- Edit `requirements.txt` with the required packages
- Edit `pywps.wsgi` to import the processes you want to deploy
- Edit `pywps.cfg` with your details

For local testing run:
- Run `python pywps.wsgi`

For an actual deployment, see the *ansible* folder.

## Processes
- get boreholes
- get borehole information and present in graph
- get timeseries for groundwatermeasurements


*adapted from https://github.com/geopython/pywps-flask*
