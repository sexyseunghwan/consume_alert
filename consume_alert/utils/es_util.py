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
Class that have information about elements by keyword_type
"""
class EsClassification:

    def __init__(self, keyword_type, es_class_type_list):
        self.keyword_type = keyword_type
        self.es_class_type_list = es_class_type_list

"""
Class of information with keywords and their bias
"""
class EsClassificationType:

    def __init__(self, keyword, bias_value):
        self.keyword = keyword
        self.bias_value = bias_value

"""
Class with each consumption classification name and total consumption information
"""
class EsConsumeTypeInfo:

    def __init__(self, keyword_type, keyword_cost):
        self.keyword_type = keyword_type
        self.keyword_cost = keyword_cost


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


    
    # Function that can identify consumption details by consumption classification.
    def get_consume_classification_infos(self, consume_info_list):
        
        s = Search(using=self.es_conn, index='consuming_index_prod_type').extra(size=0)
        s.aggs.bucket('unique_keyword_types', 'terms', field='keyword_type', size=100)

        response = s.execute()
        key_list = [bucket.key for bucket in response.aggregations.unique_keyword_types.buckets]
        consume_type_list = []

        for keyword_type in key_list:
            
            elem_s = Search(using=self.es_conn, index='consuming_index_prod_type') \
                    .query('term', keyword_type=keyword_type) \
                    .extra(size=100)
            
            elem_response = elem_s.execute()

            type_obj_list = [EsClassificationType(hit.keyword, hit.bias_value) for hit in elem_response]

            consum_type_obj = EsClassification(keyword_type, type_obj_list)
            consume_type_list.append(consum_type_obj)
        
        total_dict = {}
        
        for elem in consume_type_list:
            total_dict[elem.keyword_type] = 0
        
        for consume_elem in consume_info_list:
            
            type_dict = {}

            consume_name = consume_elem.name
            consume_cost = consume_elem.cost
            
            for elem in consume_type_list:
                type_dict[elem.keyword_type] = 0
            
            for type in consume_type_list:
                type_name = type.keyword_type
                
                for comparison in type.es_class_type_list:
                    comp_keyword = comparison.keyword
                    comp_bias = comparison.bias_value

                    if comp_keyword.lower() in consume_name.lower():
                        type_dict[type_name] = int(type_dict[type_name]) + int(comp_bias)
            
            max_type_name = ""
            max_bias = 0
            
            for key, value in type_dict.items():
                type_name = key
                type_bias = value

                if (type_bias > max_bias):
                    max_type_name = type_name
                    max_bias = type_bias
            
            if (max_type_name != "" and max_bias > 0):
                total_dict[max_type_name] = int(total_dict[max_type_name]) + int(consume_cost)   
            else:
                total_dict["etc"] = total_dict["etc"] + consume_cost     
        
        
        #total_dict = {key: value for key, value in total_dict.items() if value != 0}
        
        consume_type_info_list = []

        for key, value in total_dict.items():
            if value != 0:
                consume_type_info = EsConsumeTypeInfo(key, value)
                consume_type_info_list.append(consume_type_info)

        return consume_type_info_list
    
                
    
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