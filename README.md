# WPS Services
*One WPS to rule them all, One WPS to find them*

See http://dl-ng011.xtr.deltares.nl/

This is the central repository to store all PyWPS services.

For deployment you should:
- Add your wps processes in the processes folder
- Edit `requirements.txt` with the required packages
- Edit `pywps.wsgi` to import the processes you want to deploy
- Edit `pywps.cfg` with your details

For local testing run:
- Run `python pywps.wsgi`

For testing run:
`python -m unittest discover`

For an actual deployment, see the *ansible* folder.

## Processes
- ENDURE SLR effects
- ENDURE shorelinetransect



*adapted from https://github.com/geopython/pywps-flask*
