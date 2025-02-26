#  Relational Comparison Demo
This collection of scripts highlight differences working with the same data set in Postgres and MongoDB.  The comparisons include data generation, query performance, code complexity and transactions.  There is also a comparison of serving a json payload to an API - the most common application use case.


## Environment Setup ##
Standard GCP Debian instance, from an ssh terminal (with sudo rights)
```bash
$> vi env_setup.sh
Inside vi:
i (for insert)
- now copy the contents of the env_setup_deb.sh file and paste it into the vi prompt
esc + : + wq to save
$> chmod 755 env_setup.sh
sudo ./env_setup_deb.sh
```
The script will install a few components and end with a message like this:
`# -------------------- INFO --------------------------- #
  $> cd mongo_vs_sql
  $> source .venv/bin/activate
  Remember to set an environment variable for your passwords
  $> export _PWD_=<my mongodb password>
  $> export _PGPWD_=<my postgres password>`

Change into the mongo_vs_sql directory, invoke the venv and you are ready to go:
```bash
$> cd mongo_vs_sql
$> source .venv/bin/activate
```
Now you can run any of the python commands.  Note - each time you ssh into your machine, you will need to source the venv environment and export the password environment variable

### Postgres Schema Creation: ###
Unlike mongoDB, relational databases need a predefined schema for data to land in. The load_sql.py script can create the DDL statements for postgres from the csv files.  Here are a few command to illustrate the process.
```bash
python3 load_sql.py action=show_ddl template=model-tables/claim.csv
python3 load_sql.py action=execute_ddl task=create template=model-tables/claim.csv
```

The show_ddl command is great for both postgres and mongoDB as it will validate the format of the csv file and how the script will process it.  An important first step if you have modified any of the csv files.

The execute_ddl command will create the tables, sequences and constraints in postgres (make sure your postgres user has permissions to do this).  Note - if the database object already exists, it will ignore the step and move to the next object. 


## Data Loading ##
Data can be built in both Postgres and MongoDB using the same configuration files.  Samples are contained in the model-tables folder.  The files are csv format for simplicity.  Here is an example:

```csv
Resource.Property,Property Type,Generator
Member.member_id,String,"IDGEN.get(""M-"")"
Member.lastName,String,fake.last_name()
Member.dateOfBirth,date,"fake.past_datetime() - datetime.timedelta(365*20)"
Member.gender,String,"fake.random_element(('Male', 'Female', 'Other'))"
Member.Address().name,String,"fake.random_element(('Main', 'Summer', 'Old'))"
Member.Address().addressLine1,String,fake.street_address()
```

- In MongoDB this will create a collection with member_id, lastName, dateOfBirth and gender fields.  It will create an array of subdocuments for Address consisting of name and addressLine1.  The data generators for each invoke the Faker library to generate random data.  In order to preserve relational integrity, the system uses a method called IDGEN which will create and track ids based on the passed prefix ("M-" above).
- In Postgres the dotted depth of the property will create a system of related tables (max-depth = 5).  Thus, the above will create a Member table with 4 fields, then create a Member_Address table with the two defined fields + 2 id fields for relational joins: member_id and member_address_id, these will be automatically populated with the ids to connect the two tables.
- You can sepcify the number of subdocuments created by entering a number in the parenthesis like this:
Member.Address(12)

### Configuration: ###
Most properties are controlled by the relations_setting.json file.  This needs to be modified for your needs.  Here are a few of the key settings:
```json
{
  "version": "2.0",
  "process_count": 3,
  "batch_size": 1000,
  "batches": 10,
  "base_counter": 4000000,
  "mongodb": {
    "uri": "mongodb+srv://claims-demo.vmwqj.mongodb.net",
    "database": "healthcare_test",
    "collection": "member",
    "username": "main_admin",
    "password": "<secret>" 
  },
  "postgres": {
    "host": "34.172.34.239",
    "username": "postgres",
    "password": "<secret>",
    "database": "healthcare",
    "notes": "GCP CloudSQL Database"
  },
  "data": {
    "provider": {
      "path": "model-tables/provider.csv",
      "size": 2000,
      "id_prefix": "P-"
    },
    "member": {
      "path": "model-tables/member.csv",
      "size": 10000,
      "id_prefix": "M-"
    },
    "claim": {
      "path": "model-tables/claim.csv",
      "size": 50000,
      "id_prefix": "C-"
    }
  }
}
```

### Database Connections: ###

 For each database connection, enter the parameters in the section.  The collection parameter will be ignored in the mongodb section unless you are running some utility method.  Note that the password is masked here.  It will use a password if you enter one, however, that is not very secure.  If it says <secret>, the script will look for the environment variable _PWD_ for mongodb and _PGPWD_ for postgres.

### Data Volume: ###

 Several parameters govern the amount of data generated.  The loader uses a bulk load and the "batch_size" works with that.  In the absence of a specific size parameter in the settings file or command line, the script will use the "batches" parameter to build that data.  Additionally, the process count determines the number of threads in the loader.  You can also setup a group of files to load using the "data" parameter, this eliminates the need to define things on the command line. As an example, this will load the provider/member/claim system:
```bash
python3 load_sql.py action=load_data #(Postgres)
python3 load_mongo.py action=load_data #(MongoDB)
```

The script will use the "data" parameter which will create this much data in:
  - Provider - 2000 * 3 = 6,000, 2000/1000 = 2 batches/process thread
  - Member - 10000 * 3 = 30,000, 10000/1000 = 10 batches/process thread
  - Claim - 50000 * 3 = 150,000, 50000/1000 = 50 batches/process thread

*Note that on the sql side many more tables will be created to support the rich document depth.  In the absence of a scale parameter in the csv file, the engine will assign a number between 1-5.  Thus 1000's more records are produced in sql.

This will load the just the member.csv data:
```bash
python3 load_sql.py action=load_data template=model-tables/member.csv #(Postgres)
python3 load_mongo.py action=load_data template=model-tables/member.csv #(MongoDB)
```

The script will use the "batch size" and "batches" parameters which will create this much data:
  - Member - 1000 * 10 * 3 = 30,000, in 10 batches/process thread

In mongoDB, the "version" parameter will add a field called version with that value

## About the Data ##
The example CSV scripts will create a model of a health insurance Claim system.  A "member" goest to a "provider" and creates a "claim".  In mongoDB this creates 3 collections. Note that the claim has substantial depth to it: A claim can be delivered in multiple claim_lines, each of which may have different payment and diagnosis codes. In postgres this creates a system of nearly 30 tables.  The scripts in performance hide some of the complexity from the demo. Here is a postgres query to show a claim:
```sql
select c.*, cp.*, cn.*, cl.claim_claimline_id, cl.adjudicationdate, cl.attendingprovider_id as cl_attendingprovider_id, 
cl.modified_at as cl_modified_at, cl.operatingprovider_id, cl.orderingprovider_id, cl.otheroperatingprovider_id, cl.placeofservice, cl.procedurecode, cl.quantity, cl.referringprovider_id as cl_referringprovider_id, 
cl.renderingprovider_id as cl_renderingprovider_id, cl.serviceenddate as cl_serviceenddate, 
cl.servicefromdate as cl_servicefromdate, cl.supervisingprovider_id as cl_supervisingprovider_id, 
cl.unit, clp.approvedamount as clp_approvedamount, clp.coinsuranceamount as clp_coinsuranceamount, 
clp.copayamount as clp_copayamount, clp.allowedamount as clp_allowedamount, 
clp.paidamount as clp_paidamount, clp.paiddate as clp_paiddate, clp.patientpaidamount as clp_patientpaidamount, 
clp.patientresponsibilityamount as clp_patientresponsibilityamount, clp.payerpaidamount as clp_payerpaidamount
from claim_claimline cl inner join claim c on cl.claim_id = c.claim_id
left join claim_notes cn on cn.claim_id = c.claim_id 
left join claim_payment cp on cp.claim_id = c.claim_id
left join claim_claimline_payment clp on cl.claim_claimline_id = clp.claim_claimline_id
left join claim_claimline_diagnosiscodes cld on cld.claim_claimline_id = cl.claim_claimline_id
left join claim_diagnosiscode cd on c.claim_id = cd.claim_id
where c.claim_id in ('C-2100000')
order by c.claim_id
```
This produces a grid nearly 250 columns wide with nearly 100 rows per claim.

Here is the equivalent query in mongoDB:
```python
db.claim.findOne({claim_id: "C-2100000"})
```
This produces a single hierarchical json document that anyone can read.

## Performance Testing ##
Note - this is where the demo is specific to the Healthcare data set.  This is also the default load in in the relations_settings.json settings file.  The engine at this point does not optimize the performance in either postgres or mongodb.  To provide a fair performance comparison, a few indexes need to be created.

#### Indexes - MongoDB ####
- member.member_id
- provider.provider_id
- claim.claim_id
- claim.patient_id
- claim.attending_provider_id

#### Indexes - PostgreSQL ####
There are many indexes and constraints to provide the best performance.  These are collected into a sql script file.
- healthcare_indexes.sql
The file can be pasted into a query editor screen or run from the command line using psql.  Note, the script assumes that the database is in the "public" schema.


```bash
# --------------- Transactions ----------------- #
# 100 transactions Mongodb
python3 performance.py action=transaction_mongodb num_transactions=100 mcommit=false
python3 performance.py action=transaction_mongodb num_transactions=1 mcommit=true

# 100 Transactions Postgres
python3 performance.py action=transaction_postgres num_transactions=100

# --------------- Queries ----------------- #
python3 performance.py action=get_claims_sql query=claim patient_id=M-2030005 iters=100
python3 performance.py action=get_claims_sql query=claimLinePayments patient_id=M-2030005 iters=100
python3 performance.py action=get_claims_sql query=claimMemberProvider patient_id=M-2030005 iters=100

python3 performance.py action=get_claims_mongodb query=claim patient_id=M-2000071 iters=100
python3 performance.py action=get_claims_mongodb query=claimMemberProvider patient_id=M-2000071 iters=100

# -----  API Emulation ---------------- #
# SQL
python3 performance.py action=get_claim_api_sql claim_id=C-2030009 iters=10
# MongoDB
python3 performance.py action=get_claim_api claim_id=C-1000009 iters=10
```

###  SQL Queries ###

Simple member join to show member and address
```sql
select m.firstname, m.lastname, m.member_id, m.gender, ma.city, ma.state
from member m
left join (select member_id, city, state from member_address where member_id IN ('M-1000007','M-1000008','M-1000009','M-1000010') and name = 'Main') ma on ma.member_id = m.member_id
where m.member_id IN ('M-1000007','M-1000008','M-1000009','M-1000010');
```

Claim with resolved providers
```sql
select c.claim_id, c.claimstatus, c.claimtype, c.servicefromdate, m.firstname, m.lastname, m.dateofbirth, m.gender, cl.*, ap.firstname as ap_first, ap.lastname as ap_last, ap.gender as ap_gender, ap.dateofbirth as ap_birthdate, 
op.firstname as op_first, op.lastname as op_last, op.gender as op_gender, op.dateofbirth as op_birthdate, 
rp.firstname as rp_first, rp.lastname as rp_last, rp.gender as rp_gender, rp.dateofbirth as rp_birthdate, 
opp.firstname as opp_first, opp.lastname as opp_last, opp.gender as opp_gender, opp.dateofbirth as opp_birthdate, ma.city as city, ma.state as us_state, 
mc.phonenumber as phone, mc.emailaddress as email, me.employeeidentificationnumber as EIN
from claim c  
INNER JOIN member m on m.member_id = c.patient_id 
LEFT OUTER JOIN claim_claimline cl on cl.claim_id = c.claim_id 
INNER JOIN provider ap on cl.attendingprovider_id = ap.provider_id
INNER JOIN provider op on cl.orderingprovider_id = op.provider_id 
INNER JOIN provider rp on cl.referringprovider_id = rp.provider_id 
INNER JOIN provider opp on cl.operatingprovider_id = opp.provider_id 
LEFT JOIN (select member_id, city, state from member_address where member_id IN ('M-1000007','M-1000008','M-1000009','M-1000010') and name = 'Main') ma on ma.member_id = m.member_id 
INNER JOIN (select * from member_communication where emailtype = 'Work' and member_id IN ('M-1000007','M-1000008','M-1000009','M-1000010') limit 1) mc on mc.member_id = m.member_id
LEFT JOIN (select member_id, usage, language from member_languages where member_id IN ('M-1000007','M-1000008','M-1000009','M-1000010') and usage = 'Native') ml on ml.member_id = m.member_id 
LEFT JOIN (select member_id, employeeidentificationnumber from member_employment where member_id IN ('M-1000007','M-1000008','M-1000009','M-1000010') limit 1) me on me.member_id = m.member_id
WHERE c.patient_id IN ('M-1000007','M-1000008','M-1000009','M-1000010')
```

Claim joined with claimlines and diagnosiscode
```sql
select c.*, cl.adjudicationdate, cl.attendingprovider_id, cl.placeofservice, cl.procedurecode, cl.quantity, cl.servicefromdate, cl.serviceenddate, cp.approvedamount, cp.coinsuranceamount, cp.copayamount, cp.paidamount, cp.paiddate,
cp.patientpaidamount, cp.payerpaidamount, cp.modified_at as last_payment_activity, cd.code as diagnosis from claim c
    LEFT OUTER JOIN claim_claimline cl on cl.claim_id = c.claim_id
    LEFT JOIN claim_payment cp on cp.claim_id = c.claim_id
    LEFT JOIN claim_diagnosiscode cd on cd.claim_id = c.claim_id
WHERE c.claim_id = 'C-2003017'
```

###  Transaction in MongoDB ###
```python
with client.start_session() as session:
    logging.debug(f"Transaction started for claim {claim_id}")
    with session.start_transaction():
        claim_update = claim.find_one_and_update({"Claim_id": claim_id},{"$addToSet": {"Payment": payment[i]}},
            projection={"Patient_id": 1},
            session=session)
        member.update_one(
            {"Member_id": claim_update["Patient_id"]},
            {"$inc": {"total_payments": payment[i]["PatientPaidAmount"]}},
            session=session)
        session.commit_transaction()
```

###  Transaction in Postgres ###
```python
cur = conn.cursor()
SQL_INSERT = (
    f"INSERT INTO claim_payment(claim_payment_id, claim_id, approvedamount, coinsuranceamount, copayamount, latepaymentinterest, paidamount, paiddate, patientpaidamount, patientresponsibilityamount, payerpaidamount, modified_at)"
    f"VALUES ('{pmt['claim_payment_id']}', '{pmt['claim_id']}', {payment[i]['ApprovedAmount']}, {payment[i]['CoinsuranceAmount']}, {payment[i]['CopayAmount']}, {payment[i]['LatepaymentInterest']}, {payment[i]['PaidAmount']}, '{payment[i]['PaidDate']}', {payment[i]['PatientPaidAmount']}, {payment[i]['PatientResponsibilityAmount']}, {payment[i]['PayerPaidAmount']}, now() );"
)
# claim + update total payment claim
SQL_UPDATE_CLAIM = (
    f"UPDATE public.claim "
    f'SET totalpayments=  COALESCE(totalpayments ,0)  + {payment[i]["PatientPaidAmount"]} '
    f"WHERE claim_id = '{claim_id}';"
)
# FIND MEMBER ID
member_id = sql_query(
    f"select patient_id from claim WHERE claim_id = '{claim_id}'", conn
)
member_id = member_id["data"][0][0]
# members + update total payment
SQL_UPDATE_MEMBER = (
    f"UPDATE public.member "
    f'SET totalpayments = COALESCE(totalpayments ,0) + {payment[i]["PatientPaidAmount"]} '
    f"WHERE member_id = '{member_id}';"
)
SQL_TRANSACTION = (
    f"BEGIN;"
    f"{SQL_INSERT} "
    f"{SQL_UPDATE_CLAIM} "
    f"{SQL_UPDATE_MEMBER} "
    f"COMMIT;"
)
```

