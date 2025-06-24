import sys
import os
from collections import OrderedDict
import json
import random
import time
from bson.objectid import ObjectId
import datetime
from pymongo import MongoClient
from faker import Faker

fake = Faker()

_outlier_frequency_ = 1000 # 1 every 1000 values is outlier
_executions_ = 0

def build_asset(ptype, cur_doc):
    return False

def prove_it():
    val = random.randint(1,1000)
    print(f"# -- mix is active -- [{val}]#")   

def get_sensors(sensor_type, cur_doc):
    global _executions_
    #  accept the current doc and add policy_type and subdoc
    measures = {
        "channel_id": random.randint(1000000,2500000),
        "container_AmbientTemp": sensible_value(31.21),
        "container_CargoTemp": sensible_value(-50),
        "container_CompressorCurrentLimit": sensible_value(131),
        "container_CompressorHourMeter": sensible_value(1826),
        "container_CondenserPressure": sensible_value(193),
        "container_ControllerType": "ML3 PrimeLINE",
        "container_DTS": sensible_value(9.41),
        "container_DataGateFirmware": "20.1.46",
        "container_DataGateModel": "LYNXFLEET 52 L",
        "container_DischargePressure": sensible_value(167),
        "container_DischargeTemp": sensible_value(73.08),
        "container_GPSStatus": 3,
        "container_LastTripStart": "2024-06-03T20:00:00Z",
        "container_LineVoltage": sensible_value(461),
        "container_MinsToDefrost": sensible_value(395),
        "container_ModelNumber": "69NT40-561-236",
        "container_setpoint": sensible_value(7.2),
        "device_name": "D-865167061579117",
        "protocol_id": 39,
        "triplink_AssetStatusID": "b126acb6-5fd0-4f66-bcc6-115248a0cf67",
        "type": "container"
    }
    cur_doc["current_state"] = measures
    cur_doc["counter"] = _executions_

def sensible_value(cur_val):
    global _executions_
    global _outlier_frequency_
    denom = 100
    factor = random.randint(-10,10)
    if _executions_ % _outlier_frequency_ == 0:
        denom = denom * 0.5
        #print(" -- OUTLIER ---")
    typ = type(cur_val).__name__
    new_val = cur_val + cur_val * (factor/denom)
    if typ == 'int':
        new_val = int(new_val)
    _executions_ += 1
    #print(f'Seed: {cur_val}, val: {new_val}, #: {_executions_}')
    return new_val

def synth_address():
    return {
        "name" : fake.random_element(('Main', 'Summer', 'Old')),
        "addressLine1" : fake.street_address(),
        "addressLine2" : fake.secondary_address(),
        "city" : fake.city(),
        "state" : fake.state_abbr(),
        "postalCode" : fake.postcode(),
        "country" : fake.country(),
        "last_verified" : fake.past_datetime(start_date="-1000d")
    }

# Use an instance to track the current record being processed
_asset_types_ = OrderedDict([
    ("truck-mounted", 0.75),
    ("container", 0.3),
    ("modular-structure", 0.04),
    ("kiosk", 0.02),
    ("fridge", 0.04)    
])
_sensor_types_ = {
    "trim",
    "normal",
    "verbose"
}

