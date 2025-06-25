import sys
import os
from collections import defaultdict
from collections import OrderedDict
import json
import random
import time
import re
import multiprocessing
import pprint
import urllib
import copy
import uuid
from bson.objectid import ObjectId
from decimal import Decimal
base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(base_dir))
from bbutil import Util
#from id_generator import Id_generator
import process_csv_model as csvmod
import datetime
import pymongo
from pymongo import MongoClient
from pymongo.errors import BulkWriteError
from pymongo import UpdateOne
from pymongo import UpdateMany
from faker import Faker

fake = Faker()
settings_file = "settings.json"

def synth_data_load():
    # python3 relational_replace_loader.py action=load_data
    multiprocessing.set_start_method("fork", force=True)
    bb.message_box("Loading Data", "title")
    bb.logit(f'# Settings from: {settings_file}')
    passed_args = {"ddl_action" : "info"}
    if "template" in ARGS:
        template = ARGS["template"]
        passed_args["template"] = template
    elif "data" in settings:
        goodtogo = True
    else:
        print("Send template=<pathToTemplate>")
        sys.exit(1)    # Spawn processes
    num_procs = settings["process_count"]
    batch_size = settings["batch_size"]
    batches = settings["batches"]
    bb.logit(f'# Loading: {num_procs * batches * batch_size} docs from {num_procs} threads')
    jobs = []
    inc = 0
    for item in range(num_procs):
        p = multiprocessing.Process(target=worker_load, args = (item, passed_args))
        jobs.append(p)
        p.start()
        time.sleep(1)
        inc += 1

    main_process = multiprocessing.current_process()
    bb.logit('Main process is %s %s' % (main_process.name, main_process.pid))
    for i in jobs:
        i.join()

def worker_load(ipos, args):
    #  Called for each separate process
    cur_process = multiprocessing.current_process()
    random.seed()
    pid = cur_process.pid
    conn = client_connection()
    bb.message_box(f"[{pid}] Worker Data", "title")
    _details_["domain"] = "not-yet"
    _details_["job"] = {}
    _details_["id_generator"] = {}
    _details_["last_root"] = ""
    _details_["batching"] =  False
    _details_["mixin"] = {}
    _details_["batches"] = {}
        
    #IDGEN = args["idgen"]
    batch_size = settings["batch_size"]
    batches = settings["batches"]
    bb.logit('Current process is %s %s' % (cur_process.name, pid))
    start_time = datetime.datetime.now()
    db = conn[settings["mongodb"]["database"]]
    bulk_docs = []
    tot = 0
    if "template" in args:
        template = args["template"]
        master_table = master_from_file(template)
        job_info = {master_table : {"path" : template, "multiplier" : 1, "id_prefix" : f'{master_table[0].upper()}-'}}
    else:
        job_info = settings["data"]
    # Loop through collection files
    #pprint.pprint(job_info)
    for domain in job_info:
        _details_["domain"] = domain
        _details_["job"] = job_info[domain]
        _details_["batches"] = {}
        _details_["counter"] = 0
        batch_size = settings["batch_size"]
        prefix = _details_["job"]["id_prefix"]
        template = _details_["job"]["path"]
        if "size" in _details_["job"] and _details_["job"]["size"] < batch_size:
            batch_size = _details_["job"]["size"]
        multiplier = _details_["job"]["multiplier"]
        count = int(batches * batch_size * multiplier)
        base_counter = settings["base_counter"] + count * ipos + 1
        id_generator("init", prefix, {"base": settings["base_counter"], "size": count, "cur_base": base_counter, "next" : base_counter})
        #IDGEN.set({"seed" : base_counter, "size" : count, "prefix" : prefix})
        bb.logit(f'[{pid}] - {domain} | IDGEN - ValueHist: {_details_["id_generator"]}')
        bb.message_box(f'[{pid}] {domain} - base: {base_counter}', "title")
        tot = 0
        batches = int(count/batch_size)
        if count < batch_size:
            batch_size = count
        batch_map = csvmod.batch_digest_csv(domain, template)
        print(f"# ---------------------- {domain} Document Map ------------------------ #")
        pprint.pprint(batch_map) 
        print("# --------------------------------------------------------------- #")
        if batches == 0:
            batches = 1
        for cur_batch in range(batches):
            bb.logit(f"[{pid}] - {domain} Loading batch: {cur_batch}, {batch_size} records")
            cnt = 0
            bulk_docs = build_batch_from_template(domain, batch_map, {"batch" : cur_batch, "base_count" : base_counter, "size" : batch_size})
            cnt += 1
            #print(bulk_docs)
            db[domain].insert_many(bulk_docs)
            #cur_ids = list(map(get_id, bulk_docs))
            #print(f'[{pid}] - CurIDs: {pprint.pformat(cur_ids)}')
            siz = len(bulk_docs)
            tot += siz
            bulk_docs = []
            cnt = 0
            #bb.logit(f"[{pid}] - {domain} Batch Complete: {cur_batch} - size: {siz}, Total:{tot}\nIDGEN - ValueHist: {IDGEN.value_history}")
            bb.logit(f"[{pid}] - {domain} Batch Complete: {cur_batch} - size: {siz}, Total:{tot}")
    end_time = datetime.datetime.now()
    time_diff = (end_time - start_time)
    execution_time = time_diff.total_seconds()
    conn.close()
    bb.logit(f"{cur_process.name} - Bulk Load took {execution_time} seconds")

def get_id(doc):
    return doc["_id"]

def build_batch_from_template(domain, batch_map, details = {}):
    batch_size = settings["batch_size"]
    if "size" in details and details["size"] < batch_size:
        batch_size = details["size"]
    cnt = 0
    records = []
    for J in range(batch_size): # iterate through the bulk insert count
        # A dictionary that will provide consistent, random list lengths
        data = batch_build_doc(domain, batch_map)
        data["doc_version"] = settings["version"]
        cnt += 1
        records.append(data)
    #bb.logit(f'{batch_size} {cur_coll} batch complete')
    return(records)

def batch_build_doc(collection, batch_map):
    # Start with base fields, go next level n-times
    doc = {}
    last_key = ""
    sub_size = 5
    counts = random.randint(1, sub_size)
    is_list = False
    #print(f'C: {collection}')
    for key, value in batch_map.items():
        parts = key.split(",")
        cur_base = key.replace(last_key, "")
        res = ""
        print("# ------------------------------------------ #")
        print(f'Key: {key}, cur: {cur_base}, parts: {parts}')
        if key.lower() == collection:
            for item in value:
                #print(f'Field: {item["field"]}')
                ans = batch_generator_value(item["gen"], doc)
                if "CONTROL" not in item["type"]:
                    doc[item["field"]] = ans
        else:
            if parts[-1].endswith(')'):
                is_list = True
                res = re.findall(r'\(\d*\)',cur_base)[0]
                if res == "()":
                    lcnt = counts
                else:
                    lcnt = int(res.replace("(","").replace(")",""))
            else:
                is_list = False
                lcnt = 1
            
            inc = len(parts[1:])
            #print(f"doing parts {inc}")
            #print("# --- starting doc ---- #")
            #pprint.pprint(doc)
            handle_parts(doc, parts, 0, [key, value, lcnt, is_list], [])
    return doc
            
# ex Claim,claimLine(),payment
def handle_parts(doc, parts, cnt, args, ipath = []):
    curdoc = doc
    result = batch_sub(args[0],args[1],args[2],args[3], doc)
    if cnt == 0:
        handle_parts(doc, parts, cnt + 1, args, ipath)
    elif cnt >= len(parts):
        return
    else:
        ipart = parts[cnt]
        print(f'IPART: {ipart}, cnt: {cnt}, parts: {parts}, ipath: {ipath}')
        curdoc = doc_path(doc, ipart, ipath)
        result = batch_sub(args[0],args[1],args[2],args[3], curdoc)
        if cnt == len(parts) - 1:
            if part_is_list(parts[cnt - 1]):
                for k in curdoc:
                    result = batch_sub(args[0],args[1],args[2],args[3], curdoc)
                    k[cleaned(ipart)] = result
            else:
                curdoc[cleaned(ipart)] = result
            #print("# ---- curdoc ---- #")
            #pprint.pprint(curdoc)
        else:
            ipath.append(ipart)
            handle_parts(curdoc, parts, cnt + 1, args, ipath) 
        

def doc_path(doc, item, ipath):
    result = doc
    for k in ipath:
        result = doc[cleaned(k)]
    #print(f" --- curdoc --- {ipath}")
    #pprint.pprint(result)
    return result

def batch_sub(item, fields, cnt, isarr, cur_doc):
    sub_arr = []
    if not isarr:
        cnt = 1
    for k in range(cnt):
        sub_doc = {}
        for item in fields:
            sub_doc[item["field"]] = batch_generator_value(item["gen"], cur_doc)
        sub_arr.append(sub_doc)
    if not isarr:
        sub_arr = sub_arr[0]
    return(sub_arr)

def cleaned(str):
    str = re.sub(r'\(.*\)','', str)
    return str.strip()

def part_is_list(part):
    return part.endswith(')')

def batch_generator_value(generator, cur_doc):
    try:
        #bb.logit(f'Eval: {generator}')
        result = eval(generator) 
    except Exception as e:
        print("---- ERROR --------")
        pprint.pprint(generator)
        print("---- error --------")
        print(e)
        import traceback
        traceback.print_exc()
        exit(1)
    return(result)

#  Deprecated
def test_mix():
    # Takes template and evals the gnerators
    gen = "mix.get_sensors(fake.random_element(mix._sensor_types_), cur_doc)"
    for k in range(10):
        doc = {"name" : "brady", "id_val": f'BB-{random.randint(100000,200000)}'}
        res = batch_generator_value(gen, doc)
        pprint.pprint(doc)
    print("# ------------------------------------- #")
    for k in range(1000):
        mix.sensible_value(100.0)
    return

def master_from_file(file_name):
    ans = file_name.split("/")[-1].split(".")[0]
    with open(file_name) as handle:
        conts = handle.readlines()
        ans = conts[1].split(".")[0]
    return ans.lower()

def ensure_indexes(template, domain, db_conn):
    i_fields = csvmod.indexed_fields_from_template(template, domain)
    cur = db_conn[domain].index_information()
    keys = cur.keys()
    for fld in i_fields:
        if fld not in keys:
            bb.logit(f"Creating index: {fld}")
            db_conn[domain].create_index([(fld, pymongo.ASCENDING)])

#----------------------------------------------------------------------#
#   Data Helpers
#----------------------------------------------------------------------#
def local_geo():
    coords = fake.local_latlng('US', True)
    return [float(coords[1]), float(coords[0])]

def id_generator(action, prefix, details = {}):
    result = "none"
    if action != "init" and prefix not in _details_["id_generator"]:
        _details_["id_generator"][prefix] = {"base": 1000000, "size": 1000000, "cur_base": 1000000, "next" : 1000000}
    
    if action == "init":
        _details_["id_generator"][prefix] = {"base": details["base"], "size": details["size"], "cur_base": details["cur_base"], "next" : details["cur_base"]}
    elif action == "next":
         result =  f'{prefix}{_details_["id_generator"][prefix]["next"]}'
         _details_["id_generator"][prefix]["next"] += 1
    elif action == "batch":
        result =  _details_["id_generator"][prefix]["base"] + details["batch_size"]
        _details_["id_generator"][prefix]["next"] += details["batch_size"]
    elif action == "random":
        low = _details_["id_generator"][prefix]["cur_base"]
        high = _details_["id_generator"][prefix]["cur_base"] + _details_["id_generator"][prefix]["size"]
        result = f'{prefix}{fake.random_int(min=low,max=high)}'
    return result

# Still here for compatibliity with old csv templates
def ID(key):
    id_map[key] += 1
    return key + str(id_map[key]+base_counter)

#----------------------------------------------------------------------#
#   Utility Routines
#----------------------------------------------------------------------#
def bulk_writer(collection, bulk_arr, msg = ""):
    try:
        result = collection.bulk_write(bulk_arr, ordered=False)
        ## result = db.test.bulk_write(bulkArr, ordered=False)
        # Opt for above if you want to proceed on all dictionaries to be updated, even though an error occured in between for one dict
        #pprint.pprint(result.bulk_api_result)
        note = f'BulkWrite - mod: {result.bulk_api_result["nModified"]} {msg}'
        #file_log(note,locker,hfile)
        print(note)
    except BulkWriteError as bwe:
        print("An exception occurred ::", bwe.details)

def load_query():
    # read settings and echo back
    bb.message_box("Performing 10000 queries in 7 processes", "title")
    num_procs = 7
    jobs = []
    inc = 0
    for item in range(num_procs):
        p = multiprocessing.Process(target=run_query)
        jobs.append(p)
        p.start()
        time.sleep(1)
        inc += 1

    main_process = multiprocessing.current_process()
    for i in jobs:
        i.join()

def run_query():
    quotes = ['P-2016127','P-2049723','P-2049772','P-2049770','P-2049884','P-2049893','P-2049834','P-2049768','P-2049993','P-2047765','P-2049991','P-2049862','P-2049977','P-2018808','P-2049965','P-2049818','P-2049932','P-2049852','P-2049788','P-2049990''P-2001490','P-2049718','P-2049989','P-2049940','P-2049927','P-2049959','P-2049967','P-2049816','P-2049954','P-2049937','P-2049975','P-2049972','P-2049846','P-2049988','P-2049822','P-2049725','P-2049930','P-2049985','P-2003470','P-2049905''P-2049693','P-2049982','P-2049912','P-2049890','P-2049882','P-2049800','P-2049885','P-2049726','P-2015704','P-2049872','P-2049735','P-2038890','P-2049909','P-2001723','P-2049899','P-2049850','P-2049806','P-2049804','P-2049767','P-2014746''P-2036198','P-2049861','P-2049833','P-2001972','P-2049762','P-2049970','P-2006118','P-2049813','P-2045490','P-2012698','P-2049920','P-2013444','P-2049941','P-2049949','P-2049964','P-2049979','P-2049943','P-2044278','P-2049708','P-2049986''P-2049875','P-2006814','P-2049894','P-2049874','P-2049925','P-2049815','P-2049836','P-2049849','P-2049935','P-2049841','P-2043169','P-2049791','P-2049961','P-2049971','P-2010675','P-2049948','P-2031167','P-2049945','P-2049790','P-2049942']

    cur_process = multiprocessing.current_process()
    bb.logit('Current process is %s %s' % (cur_process.name, cur_process.pid))
    bb.logit("Performing 5000 queries")
    conn = client_connection()
    db = conn[settings["mongodb"]["database"]]
    coll = settings["mongodb"]["collection"]
    num = len(quotes)
    cnt = 0
    for k in range(int(1000/num)):
        for curid in quotes:
            start = datetime.datetime.now()
            output = db.claim.find_one({"quote_id" : curid })
            if cnt % 100 == 0:
                bb.timer(start, 100)
                #bb.logit(f"{cur_process.name} - Query: Disease: {term} - Elapsed: {format(secs,'f')} recs: {output} - cnt: {cnt}")
            cnt += 1
            #time.sleep(.5)
    conn.close()

def time_query():
    cur_process = multiprocessing.current_process()
    bb.logit('Current process is %s %s' % (cur_process.name, cur_process.pid))
    bb.logit("Performing 100 queries")
    conn = client_connection()
    query = json.loads(ARGS["query"])
    db = conn[settings["mongodb"]["database"]]
    cnt = 0
    for k in range(100):
        start = datetime.datetime.now()
        output = db.claim.find(query)
        inc = 0
        for it in output:
            inc += 1
        bb.timer(start, inc)
        cnt += 1
    conn.close()

import json  
  
def import_modules_from_config(module_list):    
    # Dynamically import modules, only one for now as "mix"
    global mix
    for module_name in module_list:  
        try:  
            mix = __import__(module_name)  
            print(f"Successfully imported module: {module_name}")  
        except ImportError as e:  
            print(f"Error importing module '{module_name}': {e}")  

def client_connection(type = "uri", details = {}):
    lsettings = settings["mongodb"]
    mdb_conn = lsettings[type]
    username = lsettings["username"]
    password = lsettings["password"]
    if "secret" in password:
        password = os.environ.get("_PWD_")
    if "username" in details:
        username = details["username"]
        password = details["password"]
    if "%" not in password:
        password = urllib.parse.quote_plus(password)
    mdb_conn = mdb_conn.replace("//", f'//{username}:{password}@')
    bb.logit(f'Connecting: {mdb_conn}')
    if "readPreference" in details:
        client = MongoClient(mdb_conn, readPreference=details["readPreference"]) #&w=majority
    else:
        client = MongoClient(mdb_conn)
    return client

#------------------------------------------------------------------#
#     MAIN
#------------------------------------------------------------------#
if __name__ == "__main__":
    mix = None
    bb = Util()
    ARGS = bb.process_args(sys.argv)
    settings = bb.read_json(settings_file)
    import_modules_from_config(settings["mixins"])
    base_counter = settings["base_counter"]
    #  IDGEN was failing because of random init issues in a sep class
    #IDGEN = Id_generator({"seed" : base_counter})
    id_map = defaultdict(int)
    mix.prove_it()
    _details_ = {} #set global to avoid passing args - note lives in a single process
    if "wait" in ARGS:
        interval = int(ARGS["wait"])
        if interval > 10:
            bb.logit(f'Delay start, waiting: {interval} seconds')
            time.sleep(interval)
    #conn = client_connection()
    if "action" not in ARGS:
        print("Send action= argument")
        sys.exit(1)
    elif ARGS["action"] == "load_data":
        synth_data_load()
    elif ARGS["action"] == "query":
        run_query()
    elif ARGS["action"] == "timer":
        time_query()
    elif ARGS["action"] == "test":
        test_mix()
    else:
        print(f'{ARGS["action"]} not found')
    #conn.close()
