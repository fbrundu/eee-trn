# District Heating Simulator - Turin version

This repository is part of a collection, see also:
- BIM Service Provider - Context layer: https://github.com/fbrundu/dimc
- BIM Service Provider - Interface layer: https://github.com/fbrundu/bimp
- District Heating Simulator - Manchester version https://github.com/fbrundu/eee-man

Full citation: 
- Brundu, Francesco Gavino, et al. "IoT software infrastructure for energy management and simulation in smart cities." IEEE Transactions on Industrial Informatics 13.2 (2016): 832-840.

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
