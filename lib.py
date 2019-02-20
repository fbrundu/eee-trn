import cherrypy
from cherrypy import log
import json


# get list of parameters from Web Service invocation
def get_parameters(params, pname):

    parameters = params[pname]
    if type(parameters) == str:
        parameters = [parameters]
    return parameters


def handle_error(code, message):

    if code == 500:
        traceback = True
    else:
        traceback = False

    log.error(msg=message, context="HTTP", traceback=traceback)
    cherrypy.response.status = code
    ctype = "application/json;charset=utf-8"
    cherrypy.response.headers["Content-Type"] = ctype

    return json.dumps({"code": code, "message": message}).encode('utf8')
