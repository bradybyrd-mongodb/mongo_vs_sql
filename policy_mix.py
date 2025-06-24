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
from faker_vehicle import VehicleProvider

fake = Faker()
fake.add_provider(VehicleProvider)

def build_policy(ptype, cur_doc):
    return _policy_actions_[ptype](cur_doc)

def prove_it():
    print("# -- mix is active -- #")   

def policy_auto(cur_doc):
    #  accept the current doc and add policy_type and subdoc
    cur_doc["policy_type"] = "auto"
    vehicle = fake.vehicle_object()
    policy_details = {
        "risk_rating" : fake.random_element(("poor", "fair", "good", "excellent")),
        "year" : vehicle["Year"],
        "make" : vehicle["Make"],
        "model" : vehicle["Model"],
        "category" : vehicle["Category"],
        "vehicle_address" : synth_address(),
        "history" : [
            {"type" : "accident", "timestamp" : fake.past_datetime(start_date="-1000d"), "claim": "C-23959586"}
        ],
        "driver" : {
            "name" : fake.name(),
            "license" : fake.state_abbr(),
            "expiration" : random.randint(2025, 2032),
            "violations" : "yes",
        },
        "ownership" : {
            "owner_type" : fake.random_element(("self", "leased", "loan")),
            "owner" : fake.bs(),
            "note_value" : random.randint(10000, 30000),
            "end_date" : fake.future_datetime(end_date="+8y")
        }
    }
    cur_doc["policy_details"] = policy_details

def policy_motorcycle(cur_doc):
    #  accept the current doc and add policy_type and subdoc
    cur_doc["policy_type"] = "motorcycle"
    vehicle = fake.vehicle_object()
    policy_details = {
        "risk_rating" : fake.random_element(("poor", "fair", "good", "excellent")),
        "year" : vehicle["Year"],
        "make" : vehicle["Make"],
        "model" : vehicle["Model"],
        "category" : vehicle["Category"],
        "displacement" : fake.random_element(("375", "500", "650", "900", "1000", "1200")),
        "vehicle_address" : synth_address(),
        "history" : [
            {"type" : "accident", "timestamp" : fake.past_datetime(start_date="-1000d"), "claim": "C-23959586"}
        ],
        "driver" : {
            "name" : fake.name(),
            "license" : fake.state_abbr(),
            "expiration" : random.randint(2025, 2032),
            "violations" : fake.random_element(("yes", "no")),
        },
        "ownership" : {
            "owner_type" : fake.random_element(("self", "leased", "loan")),
            "owner" : fake.bs(),
            "note_value" : random.randint(5000, 20000),
            "end_date" : fake.future_datetime(end_date="+8y")
        }
    }
    cur_doc["policy_details"] = policy_details

def policy_homeowners(cur_doc):
    #  accept the current doc and add policy_type and subdoc
    cur_doc["policy_type"] = "homeowners"
    policy_details = {
        "risk_rating" : fake.random_element(("poor", "fair", "good", "excellent")),
        "year" : random.randint(1950, 2020),
        "category" : fake.random_element(("detached", "townhouse", "manufactured", "mobile")),
        "style" : fake.random_element(("colonial", "modern", "farmhouse", "shitbox")),
        "construction" : fake.random_element(("wood", "concrete", "block", "steel")),
        "floors" : random.randint(1, 3),
        "fair_market_value" : random.randint(100000, 4000000),
        "property_address" : synth_address(),
        "history" : [
            {"type" : "fire", "timestamp" : fake.past_datetime(start_date="-1000d"), "claim": "C-23959586"}
        ],
        "ownership" : {
            "owner_type" : fake.random_element(("self", "mortgage", "trust")),
            "owner" : fake.bs(),
            "note_value" : random.randint(100000, 400000),
            "end_date" : fake.future_datetime(end_date="+25y")
        },
        "risks" : {
            "flood_zone" : fake.random_element(("yes", "no")),
            "fire_danger" : fake.random_element(("low", "moderate", "high")),
            "earthquake_zone" : fake.random_element(("yes", "no"))
        }
    }
    cur_doc["policy_details"] = policy_details

def policy_condo(cur_doc):
    policy_homeowners(cur_doc)
    cur_doc["policy_type"] = "condo"
    cur_doc["policy_details"]["condo"] = {
        "association_size" : random.randint(3,25),
        "dues" : random.randint(300, 800)
    }

def policy_renters(cur_doc):
    cur_doc["policy_type"] = "renters"
    policy_details = {
        "risk_rating" : fake.random_element(("poor", "fair", "good", "excellent")),
        "year" : random.randint(1950, 2020),
        "category" : fake.random_element(("cluster", "high_rise", "detached", "mobile")),
        "valuation" : random.randint(10000, 40000),
        "property_address" : synth_address(),
        "history" : [
            {"type" : "fire", "timestamp" : fake.past_datetime(start_date="-1000d"), "claim": "C-23959586"}
        ],
        "risks" : {
            "flood_zone" : fake.random_element(("yes", "no")),
            "fire_danger" : fake.random_element(("low", "moderate", "high")),
            "earthquake_zone" : fake.random_element(("yes", "no"))
        },
        "rental" : {
            "num_units" : random.randint(10,225),
            "floor" : random.randint(3, 25),
            "lease_terms" : "1yr"
        }
    }
    cur_doc["policy_details"] = policy_details

def policy_boat(cur_doc):
    #  accept the current doc and add policy_type and subdoc
    cur_doc["policy_type"] = "boat"
    policy_details = {
        "risk_rating" : fake.random_element(("poor", "fair", "good", "excellent")),
        "year" : random.randint(2000, 2025),
        "make" : fake.random_element(("Pursuit", "Grady White", "Boston Whaler", "Sea Ray", "Catalina", "Axopar")),
        "length" : random.randint(15, 55),
        "category" : fake.random_element(("Power", "Pontoon", "Sail-monohull", "Sail-catamaran")),
        "power" : fake.random_element(("75", "100", "150", "200", "350")),
        "vehicle_address" : synth_address(),
        "history" : [
            {"type" : "accident", "timestamp" : fake.past_datetime(start_date="-1000d"), "claim": "C-23959586"}
        ],
        "ownership" : {
            "owner_type" : fake.random_element(("self", "leased", "loan")),
            "owner" : fake.bs(),
            "note_value" : random.randint(5000, 20000),
            "end_date" : fake.future_datetime(end_date="+8y")
        }
    }
    cur_doc["policy_details"] = policy_details

def policy_details(cur_doc):
    ptype = PolicyType()

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
_policy_types_ = OrderedDict([
    ("auto", 0.55),
    ("homeowners", 0.3),
    ("motocycle", 0.04),
    ("boat", 0.02),
    ("condo", 0.04),
    ("renters", 0.05)    
])
_policy_actions_ = {
    "auto": policy_auto,
    "homeowners": policy_homeowners,
    "motocycle": policy_motorcycle,
    "boat": policy_boat,
    "condo": policy_condo,
    "renters": policy_renters  
}

