import sys
import os
import csv
from collections import OrderedDict
from collections import defaultdict
import random
import time
import re
import multiprocessing
import pprint
import urllib
from bson.objectid import ObjectId
base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(base_dir))
from bbutil import Util
from id_generator import Id_generator
import process_csv_model as csvmod
import datetime
from pymongo import MongoClient
from pymongo.errors import BulkWriteError
from pymongo import UpdateOne
from pymongo import UpdateMany
from faker import Faker

settings_file = "relations_settings.json"
fake = Faker()
bb = Util()
settings = bb.read_json(settings_file)
base_counter = settings["base_counter"]
IDGEN = Id_generator({"seed" : base_counter})
id_map = defaultdict(int)
    
def synth_data_update():
    # read settings and echo back
    #  python3 vcf_loader.py action=emr_data
    multiprocessing.set_start_method("fork", force=True)
    bb.message_box("Updating Data", "title")
    start_time = datetime.datetime.now()
    bb.logit(f'# Settings from: {settings_file}')
    # Spawn processes
    num_procs = settings["process_count"]
    jobs = []
    inc = 0
    for item in range(num_procs):
        p = multiprocessing.Process(target=worker_updater, args = (item,))
        jobs.append(p)
        p.start()
        time.sleep(1)
        inc += 1

    main_process = multiprocessing.current_process()
    bb.logit('Main process is %s %s' % (main_process.name, main_process.pid))
    for i in jobs:
        i.join()
    end_time = datetime.datetime.now()
    time_diff = (end_time - start_time)
    execution_time = time_diff.total_seconds()
    bb.logit(f"{main_process.name} - Execution total took {execution_time} seconds")

def worker_updater(ipos):
    #  Updates documents and finds values
    cur_process = multiprocessing.current_process()
    pid = cur_process.pid
    conn = client_connection() # This ont work - need a better solution
    bb.message_box(f"[{pid}] Worker Data", "title")
    settings = bb.read_json(settings_file)
    base_counter = settings["base_counter"]
    procs = settings["process_count"]
    bb.logit('Current process is %s %s' % (cur_process.name, cur_process.pid))
    start_time = datetime.datetime.now()
    db = settings["mongodb"]["database"]
    job_info = settings["data"]
    # Loop through collection files
    for domain in job_info:
        details = job_info[domain]
        if "thumbnail" in details:
            prefix = details["id_prefix"]
            count = details["size"]
            low_id = base_counter + (count * ipos)
            high_id = base_counter + (count * (ipos + 1))
            criteria = {"$and" : [{f'{domain}_id' : {"$gt" : f'{prefix}{low_id}'}},{f'{domain}_id' : {"$lte" : f'{prefix}{high_id}'}}]}
            tasks = details["thumbnail"]
            bb.message_box(f'[{pid}] {domain}', "title")
            for item in tasks:
                if item["type"] == "many":
                    update_related_many(domain,conn[db],item,criteria)
                else:
                    update_related_one(domain,conn[db],item,criteria)
            tot = 0
    end_time = datetime.datetime.now()
    time_diff = (end_time - start_time)
    execution_time = time_diff.total_seconds()
    conn.close()
    bb.logit(f"{cur_process.name} - Bulk Load took {execution_time} seconds")

def update_related_one(domain, db, update_info, crit):
    bb.logit(f'UpdatingOne: {update_info}, crit: {crit}')
    cursor = db[domain].find(crit)
    interval = 10
    inc = 0
    for doc in cursor:
        cur_qry = eval(update_info["find_query"])
        adoc = db[update_info["coll"]].find_one(cur_qry)
        if adoc is not None:
            newdoc = {}
            #bb.message_box("DOC")
            #pprint.pprint(doc)
            #bb.message_box(f"ADOC - {cur_qry}")
            #pprint.pprint(adoc)
            for item in update_info["fields"]:
                res = adoc
                pnam = ""
                for level in item.split("."):
                    if level.isdigit():
                        level = int(level)
                    else:
                        pnam += level
                    res = res[level]

                newdoc[pnam] = res
            db[domain].update_one({"_id": doc["_id"]},{"$set": {update_info["name"] : newdoc}})
        if inc % interval == 0:
            bb.logit(f"UpdatingOne: {inc} completed")
        inc += 1
    bb.logit(f"All done - {inc} completed")

def update_related_many(domain, db, update_info, crit):
    bb.logit(f'UpdatingMany: {update_info}, crit: {crit}')
    cursor = db[domain].find(crit)
    interval = 10
    inc = 0
    for doc in cursor:
        many_crit = eval(update_info["find_query"])
        cntq = db[update_info["coll"]].count_documents(many_crit)
        cur2 = db[update_info["coll"]].find(many_crit)
        newd = []
        for adoc in cur2:
            newdoc = {}
            for item in update_info["fields"]:
                res = adoc
                pnam = ""
                for level in item.split("."):
                    if level.isdigit():
                        level = int(level)
                    else:
                        pnam += level
                    res = res[level]
                newdoc[pnam] = res
            newd.append(newdoc)
        db[domain].update_one({"_id": doc["_id"]},{"$set": {update_info["name"] : newd}})
        if inc % interval == 0:
            bb.logit(f'UpdatingMany: {inc} completed - many: db.{update_info["coll"]}.find({many_crit}), cnt: {cntq}')
        inc += 1
    bb.logit(f"All done - {inc} completed")

def fix_member_id(conn):
    db = conn["healthcare"]
    inc = 0
    cursor = db["member"].find({})
    for adoc in cursor:
        idnum = int(adoc["Member_id"].split("-")[1]) - 50
        new_id = f'M-{idnum}'
        db["member"].update_one({"_id": adoc["_id"]},{"$set": {"Member_id" : new_id}})
        bb.logit(f"Updating: {inc} completed")
        inc += 1

def fix_claim_status(conn):
    db = conn[settings["mongodb"]["database"]]
    status_codes = {100: "initiated", 101: "plan-check",102:"verify-rx",103:"verfiy-maximums",104:"oop-limits",105:"approved",106:"denied",
                    106:"pending",107:"exception-needed",108: "exception-denied",109:"provider-contacted",110:"contact-missing",
                    111:"manual-adjudication",112:"secondary-review",113:"suggest-generic",114:"maximun-exceeded",115:"minmum-met",
                    116:"sched-verification",117:"duplicate-rx",118:"duplicate-contact",119:"unknown-planid",120:"last-status"}
    inc = 0
    cursor = db["claim"].find({},{"_id" : 1})
    for adoc in cursor:
        code = random.randint(100,120)
        db["claim"].update_one({"_id": adoc["_id"]},{"$set": {"claimStatus" : code, "claimStatusDetail": status_codes[code]}})
        bb.logit(f"Updating: {inc} completed")
        inc += 1

def add_primary_provider_ids(conn):
    num_provs = 200
    base_val = 1000000
    query = {}
    bb.message_box(f" Updater", "title")
    db = conn[settings["mongodb"]["database"]]
    recs = db["member"].find(query)
    for item in recs:
        #print(f'item: {item}')
        #pid = f'P-{random.randint(base_val, base_val + num_provs)}'
        if "primaryProvider_id" in item:
            pid = item["primaryProvider_id"]
            prov = db["provider"].find_one({"provider_id" : pid})
            if prov is not None:
                prov_doc = {"primaryProvider" : {"provider_id" : pid, "nationalProviderIdentifier" : prov["nationalProviderIdentifier"], "firstName" : prov["firstName"], "lastName": prov["lastName"], "dateOfBirth": prov["dateOfBirth"], "gender" : prov["gender"]}}
                db["member"].update_one({"_id" : item["_id"]},{"$set" : prov_doc, "$unset" : {"primaryProvider_id": ""}})
        #print(sql)
        bb.logit(f'Update: {item["member_id"]}')

def update_phi(conn):
    # Adds phi fields and client_id for redaction scenario
    num_provs = 200
    base_val = 1000000
    query = {}
    bb.message_box(f" PHI Updater", "title")
    db = conn[settings["mongodb"]["database"]]
    recs = db["member"].find(query)
    for item in recs:
        #print(f'item: {item}')
        #pid = f'P-{random.randint(base_val, base_val + num_provs)}'
        if "primaryProvider_id" in item:
            pid = item["primaryProvider_id"]
            prov = db["provider"].find_one({"provider_id" : pid})
            if prov is not None:
                prov_doc = {"primaryProvider" : {"provider_id" : pid, "nationalProviderIdentifier" : prov["nationalProviderIdentifier"], "firstName" : prov["firstName"], "lastName": prov["lastName"], "dateOfBirth": prov["dateOfBirth"], "gender" : prov["gender"]}}
                db["member"].update_one({"_id" : item["_id"]},{"$set" : prov_doc, "$unset" : {"primaryProvider_id": ""}})
        #print(sql)
        bb.logit(f'Update: {item["member_id"]}')

def update_member_ids(conn):
    bb.message_box("MemberID alignment","title")
    bb.message_box(f" PHI Updater", "title")
    db = conn[settings["mongodb"]["database"]]
    batch_size = 2000
    member_ratio = 10
    totdocs = 350000
    num_batches = int(totdocs/(batch_size * member_ratio))
    pipe = [
        {"$sample" : {"size" : batch_size * member_ratio}},
        {"$project": {"patient_id": 1}}
    ]
    inc = 0
    settings["batch_size"] = batch_size
    m_ids = []
    get_list = 0
    g_cnt = 0
    tcnt = 0
    for curbatch in range(num_batches):
        if get_list == 0 or get_list == member_ratio - 1:
            bb.logit(f'Getting {batch_size * member_ratio} claim_ids')
            claims = list(db["claim_phi"].aggregate(pipe))
            m_ids = []
            get_list = 0    
        recs = build_batch_from_template("member", {"path" : "model-tables/member_phi.csv"})
        for icnt in range(batch_size):
            try:
                recs[icnt]["member_id"] = claims[icnt]["patient_id"]
                recs[icnt]["version"] = "1.5"
                m_ids.append(claims[icnt]["patient_id"])
                tcnt += 1
            except Exception as e:
                print(f'ERROR - {icnt}, recs: {len(recs)}')
                print(e)
                exit(1)
        db["member"].insert_many(recs)
        bb.logit(f"Saving batch (member) [{batch_size}] - total: {tcnt}")
        
        bulk_updates = []
        totcnt = 0
        for k in range(member_ratio):
            for icnt in range(batch_size):
                bulk_updates.append(
                    UpdateOne({"_id" : claims[totcnt]["_id"]},{"$set": {"patient_id": m_ids[icnt]}})
                )
                totcnt += 1
            if k > 0:
                bulk_writer(db["claim_phi"], bulk_updates)
                bb.logit(f'Updating claim-member_id [{batch_size}] - total: {totcnt}, grandTotal: {g_cnt}')
            bulk_updates = []
        get_list += 1
        g_cnt += totcnt
    bb.logit(f"All done - {inc} completed")

def update_member_thumbnail(conn):
    bb.message_box("MemberID de-norm","title")
    db = conn[settings["mongodb"]["database"]]
    batch_size = 2000
    batches = 5
    pipe = [
        {"$match" : {"version" : "1.6"}},
        {"$sample" : {"size" : batch_size}}
    ]
    inc = 0
    tcnt = 0
    bulk_updates = []
    for k in range(batches):
        members = db["member"].aggregate(pipe)
        for curdoc in members:
            #pprint.pprint(curdoc)
            newdoc = {"member_id" : curdoc["member_id"], "firstName" : curdoc["phi"]["firstName"], "lastName" : curdoc["phi"]["lastName"], "birthDate" : curdoc["phi"]["dateOfBirth"], "gender": curdoc["gender"]}
            bulk_updates.append(
                UpdateMany({"patient_id" : curdoc["member_id"]},{"$set": {"patient": newdoc}})
            )
            tcnt += 1
        
        bb.logit(f"Saving batch (member) [{batch_size}] - total: {tcnt}")
        bulk_writer(db["claim_phi"], bulk_updates)
        bulk_updates = []
    bb.logit(f"All done - {inc} completed")

def update_birthdate(conn):
    bb.message_box("Birthday alignment","title")
    db = conn[settings["mongodb"]["database"]]
    batch_size = 2000
    settings["batch_size"] = batch_size
    peeps = list(db["member"].find({"version": "1.6"},{"phi.dateOfBirth": 1}))
    bulk_updates = []
    numtodo = len(peeps)
    for icnt in range(numtodo - 1):
        year = 2023 - random.randint(16,87)
        month = random.randint(1,12)
        day = random.randint(1,28)
        new_date = datetime.datetime(year,month,day, 10, 45)
        bulk_updates.append(
            UpdateOne({"_id" : peeps[icnt]["_id"]},{"$set": {"phi.dateOfBirth": new_date}})
        )
        if icnt > 0 and icnt % batch_size == 0:
            bulk_writer(db["member"], bulk_updates)
            bb.logit(f'Updating member birthday [{batch_size}] - total: {icnt}')
            bulk_updates = []

    bb.logit(f"All done - {numtodo} completed")
