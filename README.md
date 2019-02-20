# peak

## Dependencies

* Python3
* CherryPy
* pymatbridge
* paho-mqtt

## Start the service

    python3 peak.py

## Setting the configuration file

The configuration file must be saved in the directory `conf/` as `conf.json`.

## Description

The service allows the following methods:

* GET
* POST

Currently, the following actions are implemented:

* ping (GET)
* peak (GET) - retrieve results of a simulation as a zip file. Parameters:
    * reqid - the ID of the simulation
* peak (POST) - start a new simulation. Parameters:
    * subnets - the ID of the subnets on which to run the simulation (e.g. "28,29,29B")
