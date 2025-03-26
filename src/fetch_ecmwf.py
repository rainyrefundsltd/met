
import os
from config import ECMWF_API_URL, ECMWF_API_KEY, ECMWF_API_EMAIL
from ecmwfapi import ECMWFService

os.environ["ECMWF_API_URL"] = ECMWF_API_URL
os.environ["ECMWF_API_KEY"] = ECMWF_API_KEY
os.environ["ECMWF_API_EMAIL"] = ECMWF_API_EMAIL

server = ECMWFService("mars")
server.execute(
    {
    "class": "od",
    "date": "20150101",
    "expver": "1",
    "levtype": "sfc",
    "param": "167.128",
    "step": "0/to/240/by/12",
    "stream": "oper",
    "time": "00",
    "type": "fc"
    },
    "target.grib")
