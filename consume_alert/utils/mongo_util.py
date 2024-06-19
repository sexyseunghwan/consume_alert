from config import global_logger
from utils.common_util import *
from import_data.common import *


"""
MongoDB related objects
"""
class MongoObject:

    def __init__(self):
        self.m_conn = self.mongo_conn()

    # MongoDB Cluster Connector
    def mongo_conn(self):
        
        client = None

        try:
            
            mongos_list = os.getenv("MONGO_HOST").split(",")
            mongo_id = os.getenv("MONGO_ID")
            mongo_pw = os.getenv("MONGO_PW")
            
            list_idx=0

            for elem in mongos_list:
                list_idx += 1
                connection_string = f'mongodb://{mongo_id}:{mongo_pw}@{elem}'
                client = MongoClient(connection_string, connectTimeoutMS=2000)
                
                # Check whether it is connected to mongodb through ping.
                conn_resp = client.admin.command('ping')
                
                if (conn_resp['ok'] == 1.0):
                    global_logger.info(conn_resp)
                    break

                if (len(mongos_list) == list_idx):
                    raise Exception('cannot connect mongodb cluster')
                
        except Exception as e:
            global_logger.error(e)

        return client
    
    # Function to release mongodb connection
    def conn_close(self):
        self.m_conn.close()
    
    
    #
    def select_doc(self, db_name, collection_name, query_json):
        
        mongo_clent = None
        query_res = None

        try:
            mongo_clent = self.m_conn

            db = mongo_clent[db_name]
            collection = db[collection_name]

            query_res = collection.find(query_json)
            
        except Exception as e:
            global_logger.error(e)

        return query_res
    
    
    #
    def check_group_auth(self, user_id, group_name):

        try:
            query_json = {
                "chat_group_name": group_name,
                "chat_group_id": str(user_id)
            }

            q_res = self.select_doc('USERGRADE', 'rolecollection', query_json)
            
            res_cnt = 0
            
            for doc in q_res:
                res_cnt += 1

            if (res_cnt == 0): return False
            else: return True

        except Exception as e:
            global_logger.error(e)
            return False