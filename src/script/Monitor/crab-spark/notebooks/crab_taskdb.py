#!/usr/bin/env python
# coding: utf-8

# # CRAB Spark taskdb
# 
# This jobs will "copy" some column from TaskDB table to opensearch to answer theses questions:
# - How many tasks are using each crab features? (Split algorithm, Ignorelocality, ScriptExe, GPU)
# - How many tasks each users submit?
# - How many tasks use ignorelocality?
# 

# ## Import lib

# In[ ]:


from datetime import datetime, timedelta, timezone
import os
import time
import pandas as pd

from pyspark import SparkContext, StorageLevel
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    current_user,
    col, collect_list, concat_ws, greatest, lit, lower, when,
    avg as _avg,
    count as _count,
    hex as _hex,
    max as _max,
    min as _min,
    round as _round,
    sum as _sum,
)
from pyspark.sql.types import (
    StructType,
    LongType,
    StringType,
    StructField,
    DoubleType,
    IntegerType,
)


# In[ ]:


# try to import osearch from current directory, fallback to $PWD/../workdir if not found
try:
    import osearch
except ModuleNotFoundError:
    import sys
    sys.path.insert(0, f'{os.getcwd()}/../workdir')
    import osearch


# In[ ]:


spark = SparkSession\
        .builder\
        .appName('crab-taskdb')\
        .getOrCreate()
spark


# In[ ]:


# clear any cache left, for working with notebook
# it safe to run everytime cronjob start
spark.catalog.clearCache()


# ## Arguments
# 
# We provide arguments to this script via env var. 
# - `OPENSEARCH_SECRET_PATH`: path to secretfile, contain a line of <username>:<password> of opensearch that we send the data to
# - `PROD`: if true index prefix will be `crab-`, otherwise `crab-test-`
# - `START`: start date (YYYY-MM-dd)
# - `END`: end date (YYYY-MM-dd).

# In[ ]:


# secret path, also check if file exists
secretpath = os.environ.get('OPENSEARCH_SECRET_PATH', f'{os.getcwd()}/../workdir/secret_opensearch.txt')
if not os.path.isfile(secretpath): 
    raise Exception(f'OS secrets file {secretpath} does not exists')
# if PROD, index prefix will be `crab-*`, otherwise `crab-test-*`
PROD = os.environ.get('PROD', 'false').lower() in ('true', '1', 't')
# FROM_DATE, in strptime("%Y-%m-%d")
START = os.environ.get('START_DATE', None) 
END = os.environ.get('END_DATE', None)


# ## Variables 
# Will be used throughout notebook

# In[ ]:


# For run playbook manually, set start/end date here
START_DATE = "2020-01-01"
END_DATE = "2024-10-01"
# if cronjob, replace constant with value from env
if START and END:
    START_DATE = START
    END_DATE = END


# In[ ]:


# index name
index_name = 'tape-recall-history' # always put test index prefix
# use prod index pattern if this execution is for production
if PROD:
    index_name = f'crab-{index_name}'
else:
    index_name = f'crab-test-{index_name}'


# In[ ]:


# datetime object
start_datetime = datetime.strptime(START_DATE, "%Y-%m-%d").replace(tzinfo=timezone.utc)
end_datetime = datetime.strptime(END_DATE, "%Y-%m-%d").replace(tzinfo=timezone.utc)
# sanity check
if end_datetime < start_datetime: 
    raise Exception(f"end date ({END_DATE}) is less than start date ({START_DATE})")
start_epochmilis = int(start_datetime.timestamp()) * 1000
end_epochmilis = int(end_datetime.timestamp()) * 1000
yesterday_epoch = int((end_datetime-timedelta(days=1)).timestamp())


# In[ ]:


# debug
print(START_DATE, 
      END_DATE, 
      index_name,
      sep='\n')


# ## Loading data

# In[ ]:


HDFS_CRAB_part = f'/project/awg/cms/crab/tasks/{END_DATE}/' # data each day in hdfs contain whole table
print("==============================================="
      , "CRAB Table"
      , "==============================================="
      , "File Directory:", HDFS_CRAB_part
      , "Work Directory:", os.getcwd()
      , "==============================================="
      , "===============================================", sep='\n')

tasks_df = spark.read.format('avro').load(HDFS_CRAB_part).cache()
tasks_df = ( 
    tasks_df.select("TM_TASKNAME","TM_START_TIME","TM_TASK_STATUS","TM_SPLIT_ALGO","TM_USERNAME","TM_USER_ROLE","TM_JOB_TYPE","TM_IGNORE_LOCALITY","TM_SCRIPTEXE","TM_USER_CONFIG")
             .filter(f"""\
                  1=1
                  AND TM_START_TIME >= {start_epochmilis}
                  AND TM_START_TIME < {end_epochmilis}"""
             .cache()
)
tasks_df.createOrReplaceTempView("tasks")


# ## Query

# In[ ]:


query = f"""\
WITH reqacc_tb AS (         
SELECT TM_TASKNAME, TM_START_TIME, TM_TASK_STATUS, TM_SPLIT_ALGO, TM_USERNAME, TM_USER_ROLE, TM_JOB_TYPE, TM_IGNORE_LOCALITY, TM_SCRIPTEXE,
       CASE 
           WHEN get_json_object(TM_USER_CONFIG, '$.requireaccelerator') = true THEN 'T'
           ELSE 'F'
       END AS REQUIRE_ACCELERATOR
FROM tasks
),
finalize_tb AS (
SELECT TM_TASKNAME, TM_START_TIME, TM_TASK_STATUS, TM_SPLIT_ALGO, TM_USERNAME, TM_USER_ROLE, TM_JOB_TYPE, TM_IGNORE_LOCALITY, TM_SCRIPTEXE, REQUIRE_ACCELERATOR,
       TM_START_TIME AS timestamp,
       'taskdb' AS type
FROM reqacc_tb
)
SELECT * FROM finalize_tb
"""

tmpdf = spark.sql(query)
tmpdf.show(10, False)



# ## Sending result to OpenSearch

# In[ ]:


# convert spark df to dicts
docs = tmpdf.toPandas().to_dict('records')


# In[ ]:


schema = {
            "settings": {"index": {"number_of_shards": "1", "number_of_replicas": "1"}},
            "mappings": {
                "properties": {
                    "TM_TASKNAME": {"ignore_above": 2048, "type": "keyword"},
                    "TM_START_TIME": {"format": "epoch_millis", "type": "date"},
                    'TM_TASK_STATUS': {"ignore_above": 2048, "type": "keyword"},
                    "TM_SPLIT_ALGO": {"ignore_above": 2048, "type": "keyword"},
                    "TM_USERNAME": {"ignore_above": 2048, "type": "keyword"},
                    "TM_USER_ROLE": {"ignore_above": 2048, "type": "keyword"},
                    "TM_JOB_TYPE": {"ignore_above": 2048, "type": "keyword"},
                    "TM_IGNORE_LOCALITY": {"ignore_above": 2048, "type": "keyword"},
                    "TM_SCRIPTEXE": {"ignore_above": 2048, "type": "keyword"},
                    "REQUIRE_ACCELERATOR": {"ignore_above": 2048, "type": "keyword"},
                    "type": {"ignore_above": 2048, "type": "keyword"},
                    "timestamp": {"format": "epoch_millis", "type": "date"},
        }
    }
}


# In[ ]:


# reload osearch in case the code is changed.
# useful for playbook and safe when run as cron
import importlib
importlib.reload(osearch)


# In[ ]:


osearch.send_os(docs, index_name, schema, secretpath, yesterday_epoch)

