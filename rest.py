import cherrypy
import json
from lib import get_parameters, handle_error
from multiprocessing import Pool
import os
import paho.mqtt.client as mqtt
from pymatbridge import Matlab
import requests
import shutil
import uuid
from xml.etree import ElementTree


# load configuration into global dictionary
with open("conf/conf.json", "r") as cfile:
    pbc = json.load(cfile)


# Ping microservice
class Ping(object):
    exposed = True

    def GET(self):

        if validate(cherrypy.request.headers):
            try:
                return handle_error(200, "Pong")
            except:
                return handle_error(500, "Internal Server Error")
        else:
            return handle_error(401, "Unauthorized")


class Peak(object):
    exposed = True

    def __init__(self, mlab_path, pool, broker):
        self.mlab_path = mlab_path
        self.pool = pool
        self.broker = broker

    def GET(self, *paths, **params):

        if validate(cherrypy.request.headers):

                try:
                    try:
                        reqid = get_parameters(params, "reqid")[0]
                    except KeyError:
                        return handle_error(400, "Bad Request")

                    fname = os.path.join("results", reqid + ".zip")
                    with open(fname, "rb") as archive:
                        response = archive.read()

                    # set response header for zip
                    ctype = "application/zip"
                    cherrypy.response.headers["Content-Type"] = ctype
                    cdisp = 'attachment; filename="' + reqid + '.zip"'
                    cherrypy.response.headers["Content-Disposition"] = cdisp

                    return response
                except:
                    return handle_error(500, "Internal Server Error")
        else:
            return handle_error(401, "Unauthorized")

    def POST(self, *paths, **params):

        if validate(cherrypy.request.headers):

            try:
                reqid = str(uuid.uuid4())
                try:
                    subnets = get_parameters(params, "subnets")
                except KeyError:
                    return handle_error(400, "Bad Request")
                respath = os.path.abspath("results")
                srcpath = os.path.abspath("mlab")
                os.makedirs(os.path.join(respath, reqid))
                wargs = [(self.mlab_path, reqid, respath, srcpath, subnets)]
                self.pool.apply_async(Peak.worker, wargs,
                                      callback=self.publish)

                return handle_error(202, "Request ID: " + reqid)
            except:
                return handle_error(500, "Internal Server Error")
        else:
            return handle_error(401, "Unauthorized")

    @classmethod
    def worker(cls, args):

        mlab_path, reqid, respath, srcpath, subnets = args
        mlab = Matlab(executable=mlab_path)
        mlab.start()

        try:
            # setting variables
            log.error(msg="Setting Matlab variables", context="HTTP")
            success = True
            success &= mlab_setvar(mlab, "DH_Simulator_AllSubnets", ','.join(subnets))
            success &= mlab_setvar(mlab, "DH_Simulator_SimulationID", reqid)
            success &= mlab_setvar(mlab, "DH_Simulator_ResultsPath", respath)
            success &= mlab_setvar(mlab, "DH_Simulator_ScriptPath", srcpath)

            if not success:
                log.error(msg="Unable to set some variables", context="HTTP")
            else:
                # running simulation
                log.error(msg="Starting simulation", context="HTTP")
                mlab.run_code("cd mlab")
                mlab.run_code("peak")
                log.error(msg="Simulation ended", context="HTTP")
        finally:
            mlab.stop()
            archive_dir = os.path.join(respath, reqid)
            shutil.make_archive(archive_dir, "zip", archive_dir)

        return reqid

    def publish(self, result):

        client = mqtt.Client("eee-peak", clean_session=False)
        client.connect(self.broker, 1883)
        client.publish("eee/peak/results", result)
        client.disconnect()


def quote(value):

    return "'" + value + "'"


def mlab_setvar(mlab, key, value):

    if type(value) == str:
        value = quote(value)
    else:
        value = str(value)

    statement = key + " = " + value + ";"
    log.error(msg=statement, context="MATLAB")
    result = mlab.run_code(statement)

    if not result["success"]:
        log.error(msg="Unable to set matlab variable " + key + ": " +
                  result["content"]["stdout"], context="HTTP")
        return False

    return True


# to start the Web Service
def start():

    # start the service registrator utility
    # FIXME
    # p = sp.Popen([os.path.join(pbc["binpath"], "service-registrator"),
    #               "-conf", pbc["confpath"], "-endpoint", pbc["scatalog"]])

    # start Web Service with some configuration
    if pbc["stage"] == "production":
        global_conf = {
               "global":    {
                                "server.environment": "production",
                                "engine.autoreload.on": True,
                                "engine.autoreload.frequency": 5,
                                "server.socket_host": "0.0.0.0",
                                "log.screen": False,
                                "log.access_file": "peak.log",
                                "log.error_file": "peak.log",
                                # FIXME
                                # "server.socket_port": 443,
                                "server.socket_port": pbc["port"]
                                # "server.ssl_module": "builtin",
                                # "server.ssl_certificate": pbc["cert"],
                                # "server.ssl_private_key": pbc["priv"],
                                # "server.ssl_certificate_chain": pbc["chain"]
                            }
        }
        cherrypy.config.update(global_conf)
    conf = {
        "/": {
            "request.dispatch": cherrypy.dispatch.MethodDispatcher(),
            "tools.encode.debug": True,
            "request.show_tracebacks": False
        }
    }

    pool = Pool(3)

    cherrypy.tree.mount(Ping(), "/eee/ping", conf)
    cherrypy.tree.mount(Peak(pbc["mlab_path"], pool, pbc["broker"]),
                        "/eee/peak", conf)

    # activate signal handler
    if hasattr(cherrypy.engine, "signal_handler"):
        cherrypy.engine.signal_handler.subscribe()

    # subscribe to the stop signal
    # cherrypy.engine.subscribe("stop", p.terminate)

    # start serving pages
    cherrypy.engine.start()
    cherrypy.engine.block()


def validate(headers):

    token = headers["X-Auth-Token"]

    # FIXME
    serviceID = "eee"
    url = ("<validation_url>" +
           serviceID + "&ticket=" + token)
    r = requests.get(url, verify="/etc/ssl/certs/ca.pem")
    root = list(ElementTree.fromstring(r.content))

    return root[0].tag.endswith("authenticationSuccess")
