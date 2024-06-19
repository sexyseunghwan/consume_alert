from config import global_logger
from utils.common_util import *
from import_data.common import *

"""
Object information to be updated in Elasticsearch
"""
class UpdateObj:

    def __init__(self, field_name, new_value):
        self.field_name = field_name
        self.new_value = new_value

"""
ES index object related to mealtime
"""
class EsIndexMeal:

    def __init__(self, doc_id, timestamp, laststamp, alarminfo):
        self.doc_id = doc_id 
        self.timestamp = timestamp
        self.laststamp = laststamp
        self.alarminfo = alarminfo

"""
"consuming_index_prod_new" index-related objects
"""
class EsIndexConsume:

    def __init__(self, name, date, cost):
        self.name = name
        self.date = date
        self.cost = cost


"""
Elasticsearch related objects
"""
class ESObject:

    def __init__(self):
        self.es_conn = self.elastic_conn()
    
    # Elasticsearch Cluster Connector
    def elastic_conn(self):
                
        ip_lists = os.getenv("ES_HOST").split(",")
        es_id = os.getenv("ES_ID")
        es_pw = os.getenv("ES_PW")

        try:

            es = Elasticsearch(ip_lists,sniff_on_connection_fail=True,sniffer_timeout=5,timeout=10,http_auth=(es_id,es_pw))
            es.ping()
            
            global_logger.info("Elasticsearch Cluster Connect!! {}".format(es))

            return es

        except Exception as e:
            es.transport.close()
            global_logger.error(str(e))
            return None
    
        
    # Function to release elasticsearch connection
    def conn_close(self):
        self.es_conn.transport.close()
    

    # Function that retrieves image information from Elasticsearch
    def get_image_query(self, input_text):

        # Create Elasticsearch DSL Query
        s = Search(using=self.es_conn, index="telegram_index_test")
        q = Q("match", subject={"query": input_text, "analyzer": "my_analyzer"})
        s = s.query(q)
        
        global_logger.info("Elasticsearch Query Executed : {}".format(s))

        try:
            # Execute Elasticsearch DSL Query
            response = s.execute().to_dict()

            return response['hits']['hits'][0]['_source']['img_path']
            
        except Exception as e:
            global_logger.error(str(e))
        finally:
            self.es_conn.transport.close()
            global_logger.info("Elasticsearch Cluster disconnected {}".format(self.es_conn))
    

    # Function that retrieves data within the @timestamp period of a specific index.
    def get_info_term(self, index_name, start_dt, end_dt):
        
        s = Search(using=self.es_conn, index=index_name)
        s = s.query('range', **{'@timestamp': {'gte': start_dt, 'lte': end_dt}})
        s = s.sort("@timestamp")
        s = s[:10000]

        resp = s.execute()

        return resp


    # Function that indexes data into an index with a specific name.
    def set_infos_index(self, index_name, input_document):

        # Index data into ES-INDEX
        return self.es_conn.index(index=index_name, document=input_document)



    # Query the total bill spent in a specific period
    def get_index_count(self, index_name, start_dt, end_dt):

        s = Search(using=self.es_conn, index=index_name)

        query = Q("range", **{"@timestamp": {"gte": start_dt, "lte": end_dt}})
        s = s.query(query)

        response = s.count()

        return response

    

    # Query the total bill spent in a specific period
    def get_consume_total_cost(self, index_name, start_dt, end_dt):
        
        s = Search(using=self.es_conn, index=index_name)
        s = s.query('range', **{'@timestamp': {'gte': start_dt, 'lte': end_dt}})
        s.aggs.bucket('total_money', 'sum', field='prodt_money')

        # Run query and get result
        resp = s.execute()

        return "{:,}".format(int(resp.aggregations.total_money.value))
    
    

    # Details of the list consumed during a specific period
    def get_consume_info_detail_list(self, index_name, start_dt, end_dt):
        
        cost_obj_list = []

        s = Search(using=self.es_conn, index=index_name)
        s = s.query('range', **{'@timestamp': {'gte': start_dt, 'lte': end_dt}})
        s = s.sort("@timestamp")
        s = s[:10000]
        response = s.execute()

        for i in range(0,len(response)):
            cost_obj = EsIndexConsume(response[i]['prodt_name'], response[i]['@timestamp'], response[i]['prodt_money'])
            cost_obj_list.append(cost_obj)

        return cost_obj_list
    


    # Function that shows how much money you spent per month in a specific year
    def get_consume_info_list_per_year(self, index_name, input_year):
        
        cost_obj_list = []

        for i in range(1,13):
            mon_start = '{}.{}.01'.format(input_year, i)

            start_date = datetime.strptime(mon_start, "%Y.%m.%d")
            mon_last_day = calendar.monthrange(start_date.year, start_date.month)[1]
            end_date = start_date.replace(day=mon_last_day, hour=23, minute=59, second=59, microsecond=0)

            # Total consumption for the month
            total_cost = self.get_consume_total_cost(index_name, start_date.strftime("%Y-%m-%dT%H:%M:%SZ"), end_date.strftime("%Y-%m-%dT%H:%M:%SZ"))
            
            target_date = start_date.strftime("%Y-%m")
            
            pair = (target_date, total_cost)
            cost_obj_list.append(pair)
            
        return cost_obj_list




    # [deprecated] Checks whether an ID with admin privileges exists.
    def check_group_auth(self, user_id, group_name):

        s = Search(using=self.es_conn, index='chat_limit_index') \
            .query('bool', must=[
                {'term': {'chat_group_name': group_name}},
                {'term': {'chat_group_id': user_id}}
            ])
        
        resp = s.execute()

        if (len(resp) == 1):
            return True
        else:
            return False
    
    
    # Function to get the most recent data of a specific index
    def get_recent_info_term(self, index_name, start_dt, end_dt, data_cnt):
        
        s = Search(using=self.es_conn, index=index_name)
        s = s.query('range', **{'@timestamp': {'gte': start_dt, 'lte': end_dt}})
        s = s.sort('-@timestamp')
        
        # how many data to select
        s = s[:data_cnt]
        
        return s.execute() 


    # Function that removes a specific index
    def delete_index_info(self, index_name, doc_id):
        self.es_conn.delete(index=index_name, id=doc_id)


    # Function that modifies a specific field of data that satisfies a specific ID of a specified index
    def set_modify_index_data(self, index_name, doc_id, update_list):
        
        update_body = {
            "doc": {}
        }
        
        for update_obj in update_list:
            field_name = update_obj.field_name
            new_value = update_obj.new_value

            update_body["doc"][field_name] = new_value
        
        self.es_conn.update(index=index_name, id=doc_id, body=update_body)