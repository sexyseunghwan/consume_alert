from config import global_logger
from utils.common_util import *
from utils.es_util import *
from utils.tele_util import *
from utils.mongo_util import *
from import_data.common import *
from utils.matplot_util import *

korea_tz = pytz.timezone('Asia/Seoul')

# command handler - 1 : Function that retrieves a picture of a person -> /call
def command_character(update, context, grant_group_name):
    
    tele_bot = TeleInfo(update)
    es_obj =  ESObject()
    mongo_obj = MongoObject()

    try:

        if (mongo_obj.check_group_auth(tele_bot.user_id, grant_group_name)):
            image_path = es_obj.get_image_query(tele_bot.argument)
            send_image(update, context, image_path) 
        else:
            raise Exception('Group {} attempted to access the "{}" permission.'.format(tele_bot.user_id, grant_group_name))

    except Exception as e:
        global_logger.error(str(e), exc_info=True)

    es_obj.conn_close()
    mongo_obj.conn_close()


# command handler - 2 : Functions that retrieve exchange rate information and stock price information -> /m
def command_currency(update, context, grant_group_name):
    
    tele_bot = TeleInfo(update)
    mongo_obj = MongoObject()

    try:

        if (mongo_obj.check_group_auth(tele_bot.user_id, grant_group_name)):
            
            currency_dict = exchange_rate(tele_bot.argument)

            result = '{} {}'.format(currency_dict['target_currency'], currency_dict['korea_won'])

            context.bot.send_message(chat_id=tele_bot.user_id, text=result)

        else:
            raise Exception('Group {} attempted to access the "{}" permission.'.format(tele_bot.user_id, grant_group_name))
    
    except Exception as e:
        global_logger.error(str(e), exc_info=True)

    mongo_obj.conn_close()



# command handler - 3 : Writes the expenditure details to the index in ElasticSearch. -> /c
def command_consumption(update, context, grant_group_name):
    
    tele_bot = TeleInfo(update)
    es_obj = ESObject()
    mongo_obj = MongoObject()
     
    try:
        
        if (mongo_obj.check_group_auth(tele_bot.user_id, grant_group_name)):

            if tele_bot.type == 2:

                input_data = tele_bot.argument.split(":")
                
                if (len(input_data) != 2):
                    tele_bot.send_message_text(context, "There is a problem with the parameter you entered. Please check again. \nEX) /c snack:15000")
                    raise Exception('There are not two parameters input to the "command_consumption_per_term()" function - input_data : {}'.format(input_data)) 
            
                # If the second input parameter is a number
                if (input_data[1][0] == '-' or input_data[1].isdigit()):
                    
                    now = datetime.now(tz=korea_tz).strftime("%Y-%m-%dT%H:%M:%SZ")

                    consume_name = input_data[0]
                    consume_cash = int(input_data[1])

                    input_document = {
                        '@timestamp': now,
                        'prodt_name': consume_name,
                        'prodt_money': consume_cash
                    }
                    
                    response = es_obj.set_infos_index("consuming_index_prod_new", input_document)
                    global_logger.info("Elasticsearch Query Executed : {}".format(response))

                # If the second input parameter is not a number
                else:
                    tele_bot.send_message_text(context, "There is a problem with the parameter you entered. Please check again. \nEX) /c snack:15000")
                    raise Exception('An error occurred because the second input parameter in the "command_consumption()" function was not a numeric type. - second input_data : {}'.format(input_data[1]))

            else:
                tele_bot.send_message_text(context, "There is a problem with the parameter you entered. Please check again. \nEX) /c snack:15000")
                raise Exception("'tele_bot.type' is not 2 in function 'command_consumption()' function. - tele_bot.type : {}".format(tele_bot.type))
                
        else:
            tele_bot.send_message_text(context, "The group does not have access.")
            raise Exception('Group {} attempted to access the "{}" permission.'.format(tele_bot.user_id, grant_group_name))

    except Exception as e:
        global_logger.error(str(e), exc_info=True)

    es_obj.conn_close()
    mongo_obj.conn_close()



# command handler - 4 : Checks how much you have consumed during a month -> /cm
def command_consumption_per_mon(update, context, grant_group_name):

    tele_bot = TeleInfo(update)
    es_obj = ESObject()
    mongo_obj = MongoObject()

    try:

        if (mongo_obj.check_group_auth(tele_bot.user_id, grant_group_name)):

            if (tele_bot.type == 1):
                
                now = datetime.now(tz=korea_tz).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                pre_now = now - relativedelta(months=1)
                
                now_str = '{}.{}.01'.format(now.year, now.month)
                pre_now_str = '{}.{}.01'.format(pre_now.year, pre_now.month)

                start_date = datetime.strptime(now_str, "%Y.%m.%d")
                pre_start_date = datetime.strptime(pre_now_str, "%Y.%m.%d")

                last_day = calendar.monthrange(start_date.year, start_date.month)[1]
                pre_last_day = calendar.monthrange(pre_start_date.year, pre_start_date.month)[1]
                
            else:
                
                input_val = tele_bot.argument.strip()

                if (not is_date(input_val, "%Y.%m")):
                    tele_bot.send_message_text(context, "There is a problem with the parameter you entered. Please check again. \nEX01) /cm 2023.07.01\nEX02) /cm")
                    raise Exception("The input parameter value of the 'command_consumption_per_mon()' function does not satisfy the specified date format. - input_val : {}".format(input_val))
                    
                input_mon = '{}.01'.format(input_val)
                
                start_date = datetime.strptime(input_mon, "%Y.%m.%d")
                pre_start_date = start_date - relativedelta(months=1)

                last_day = calendar.monthrange(start_date.year, start_date.month)[1]
                pre_last_day = calendar.monthrange(pre_start_date.year, pre_start_date.month)[1]

 
            end_date = start_date.replace(day=last_day, hour=23, minute=59, second=59, microsecond=0)
            pre_end_date = pre_start_date.replace(day=pre_last_day, hour=23, minute=59, second=59, microsecond=0)


            # Get total summed money value
            total_cost = es_obj.get_consume_total_cost('consuming_index_prod_new', start_date.strftime("%Y-%m-%dT%H:%M:%SZ"), end_date.strftime("%Y-%m-%dT%H:%M:%SZ"))
            consume_info_list = es_obj.get_consume_info_detail_list('consuming_index_prod_new', start_date.strftime("%Y-%m-%dT%H:%M:%SZ"), end_date.strftime("%Y-%m-%dT%H:%M:%SZ"))

            pre_total_cost = es_obj.get_consume_total_cost('consuming_index_prod_new', pre_start_date.strftime("%Y-%m-%dT%H:%M:%SZ"), pre_end_date.strftime("%Y-%m-%dT%H:%M:%SZ"))
            pre_consume_info_list = es_obj.get_consume_info_detail_list('consuming_index_prod_new', pre_start_date.strftime("%Y-%m-%dT%H:%M:%SZ"), pre_end_date.strftime("%Y-%m-%dT%H:%M:%SZ"))
            
            calculate_cosume_res_dual(consume_info_list, total_cost, start_date, end_date, pre_consume_info_list, pre_total_cost, pre_start_date, pre_end_date)
            
            tele_bot.send_message_consume(context, start_date, end_date , total_cost, consume_info_list, 10)

            send_image(update, context, './data/img/plot.png')

        else:
            tele_bot.send_message_text(context, "The group does not have access.")
            raise Exception('Group {} attempted to access the "{}" permission.'.format(tele_bot.user_id, grant_group_name))
        
    except Exception as e:
        global_logger.error(str(e), exc_info=True)

    es_obj.conn_close()
    mongo_obj.conn_close()


# command handler - 5 -> /ctr
# If you enter a specific period, 
# you can find out the total amount of money spent during that period.
def command_consumption_per_term(update, context, grant_group_name):

    tele_bot = TeleInfo(update)
    es_obj = ESObject()
    mongo_obj = MongoObject()
    
    try:
        
        if (mongo_obj.check_group_auth(tele_bot.user_id, grant_group_name)):

            if tele_bot.type == 2:
                
                input_data = tele_bot.argument.split("-")
                
                # Check if start date and end date are entered
                if (len(input_data) != 2):
                    tele_bot.send_message_text(context, "There is a problem with the parameter you entered. Please check again. \nEX) /ctr 2023.07.07-2023.08.01")
                    raise Exception('There are not two parameters input to the "command_consumption_per_term()" function - input_data : {}'.format(input_data))

                # Check whether the data format of the input start date and end date is a date type
                else:
                    for elem in input_data:
                        # Checks whether there is a problem with the entered date format.
                        if (not is_date(elem, "%Y.%m.%d")):
                            tele_bot.send_message_text(context, "There is a problem with the parameter you entered. Please check again. EX) \n/ctr 2023.07.07-2023.08.01")
                            raise Exception('The data type of the parameter input to the "command_consumption_per_term()" function is not a date type that satisfies the condition. - elem : {}'.format(elem))
                    
                    # === If there is no problem with the input date format, proceed with the rest of the work === 
                    start_date = datetime.strptime(input_data[0], "%Y.%m.%d")
                    formatted_start_date = start_date.strftime("%Y-%m-%dT%H:%M:%SZ")
                    
                    end_date = datetime.strptime(input_data[1], "%Y.%m.%d").replace(hour=23, minute=59, second=59, microsecond=0)
                    formatted_end_date = end_date.strftime("%Y-%m-%dT%H:%M:%SZ")
                    
                    # Get total summed money value
                    total_cost = es_obj.get_consume_total_cost('consuming_index_prod_new', formatted_start_date, formatted_end_date)
                    consume_info_list = es_obj.get_consume_info_detail_list('consuming_index_prod_new', formatted_start_date, formatted_end_date)
                    
                    calculate_cosume_res_single(consume_info_list, total_cost, start_date, end_date)

                    tele_bot.send_message_consume(context, start_date, end_date , total_cost, consume_info_list, 10)

                    send_image(update, context, './data/img/plot.png')

            else:
                tele_bot.send_message_text(context, "There is a problem with the parameter you entered. Please check again. \nEX) /ctr 2023.07.07-2023.08.01")
                raise Exception("'tele_bot.type' is not 2 in function 'command_consumption_per_term()' function. - tele_bot.type : {}".format(tele_bot.type))
            
        else:
            tele_bot.send_message_text(context, "The group does not have access.")
            raise Exception('Group {} attempted to access the "{}" permission.'.format(tele_bot.user_id, grant_group_name))
        
    except Exception as e:
        global_logger.error(str(e))
    
    es_obj.conn_close()
    mongo_obj.conn_close()


# command handler - 6 -> /ct
# 1) That function tells you the total amount you've spent today. 
# 2) That function tells you the total amount you've spent specific date
def command_consumption_per_today(update, context, grant_group_name):

    tele_bot = TeleInfo(update)
    es_obj = ESObject()
    mongo_obj = MongoObject()

    try:

        if (mongo_obj.check_group_auth(tele_bot.user_id, grant_group_name)):
            
            today_start = None
            today_end = None
            
            # 1) If you want to know the total amount spent today
            if tele_bot.type == 1:
                
                now = datetime.now(tz=korea_tz)
                today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
                today_end = now.replace(hour=23, minute=59, second=59, microsecond=0)

            # 2) If you want to know what you spent on a specific day
            elif tele_bot.type == 2:
                
                today_start = datetime.strptime(tele_bot.argument, "%Y.%m.%d")
                today_end = datetime.strptime(tele_bot.argument, "%Y.%m.%d").replace(hour=23, minute=59, second=59, microsecond=0)
            
            else :
                raise Exception("'tele_bot.type' is not 1 in function 'command_consumption_per_today()' function. - tele_bot.type : {}".format(tele_bot.type))

            # Get total summed money value
            total_cost = es_obj.get_consume_total_cost('consuming_index_prod_new', today_start.strftime("%Y-%m-%dT%H:%M:%SZ"), today_end.strftime("%Y-%m-%dT%H:%M:%SZ"))
            consume_info_list = es_obj.get_consume_info_detail_list('consuming_index_prod_new', today_start.strftime("%Y-%m-%dT%H:%M:%SZ"), today_end.strftime("%Y-%m-%dT%H:%M:%SZ"))

            tele_bot.send_message_consume(context, today_start.strftime("%Y-%m-%dT%H:%M:%SZ"), today_end.strftime("%Y-%m-%dT%H:%M:%SZ") , total_cost, consume_info_list, 10)

        else:
            tele_bot.send_message_text(context, "The group does not have access.")
            raise Exception('Group {} attempted to access the "{}" permission.'.format(tele_bot.user_id, grant_group_name))
    
    except ValueError as e:
        tele_bot.send_message_text(context, "There is a problem with the parameter you entered. Please check again. \nEX) /ct or /ct 2023.11.11")
        global_logger.error(str(e), exc_info=True)
    
    except Exception as e:
        global_logger.error(str(e), exc_info=True)

    es_obj.conn_close()
    mongo_obj.conn_close()


# command handler - 7 : Query the amount of money consumed by payday -> /cs
def command_consumption_per_salary(update, context, grant_group_name):
    
    tele_bot = TeleInfo(update)
    es_obj = ESObject()
    mongo_obj = MongoObject()

    try:

        if (mongo_obj.check_group_auth(tele_bot.user_id, grant_group_name)):
            
            if tele_bot.type == 1:
                
                start_date = datetime.now(tz=korea_tz)
                end_date = datetime.now(tz=korea_tz)

                # To compare with previous month's consumption.
                pre_start_date = datetime.now(tz=korea_tz)
                pre_end_date = datetime.now(tz=korea_tz)

                if (start_date.day >= 25):
                    start_date = start_date.replace(day=25, hour=0, minute=0, second=0, microsecond=0)
                    end_date = end_date.replace(day=25, hour=0, minute=0, second=0, microsecond=0) + relativedelta(months=1)

                    pre_start_date = start_date - relativedelta(months=1)
                    pre_end_date = end_date - relativedelta(months=1)

                else:
                    start_date = start_date.replace(day=25, hour=0, minute=0, second=0, microsecond=0) - relativedelta(months=1)
                    end_date = end_date.replace(day=25, hour=0, minute=0, second=0, microsecond=0)

                    pre_start_date = start_date - relativedelta(months=1)
                    pre_end_date = end_date - relativedelta(months=1)
                

                formatted_start_date = start_date.strftime("%Y-%m-%dT%H:%M:%SZ")
                formatted_end_date = end_date.strftime("%Y-%m-%dT%H:%M:%SZ")

                formatted_pre_start_date = pre_start_date.strftime("%Y-%m-%dT%H:%M:%SZ")
                formatted_pre_end_date = pre_end_date.strftime("%Y-%m-%dT%H:%M:%SZ")
                
                # Get total summed money value
                # This Month
                total_cost = es_obj.get_consume_total_cost('consuming_index_prod_new', formatted_start_date, formatted_end_date)
                consume_info_list = es_obj.get_consume_info_detail_list('consuming_index_prod_new', formatted_start_date, formatted_end_date)

                # Pre Month
                total_cost_pre = es_obj.get_consume_total_cost('consuming_index_prod_new', formatted_pre_start_date, formatted_pre_end_date)
                consume_pre_info_list = es_obj.get_consume_info_detail_list('consuming_index_prod_new', formatted_pre_start_date, formatted_pre_end_date)
                
                calculate_cosume_res_dual(consume_info_list, total_cost, start_date, end_date, consume_pre_info_list, total_cost_pre, pre_start_date, pre_end_date)
                
                tele_bot.send_message_consume(context, formatted_start_date, formatted_end_date , total_cost, consume_info_list, 10)
                
                send_image(update, context, './data/img/plot.png')
                
            else:
                tele_bot.send_message_text(context, "There is a problem with the parameter you entered. Please check again. \nEX) /cs")
                raise Exception("'tele_bot.type' is not 1 in function 'command_consumption_per_salary()' function. - tele_bot.type : {}".format(tele_bot.type))
            
        else:
            tele_bot.send_message_text(context, "The group does not have access.")
            raise Exception('Group {} attempted to access the "{}" permission.'.format(tele_bot.user_id, grant_group_name))
    
    except Exception as e:
        global_logger.error(str(e), exc_info=True)

    es_obj.conn_close()
    mongo_obj.conn_close()


# command handler - 8 -> /cw
# 1) Lets you see how much you've spent this week
# 2) If you enter a specific date, it shows the consumption details for that week.
def command_consumption_per_week(update, context, grant_group_name):
    
    tele_bot = TeleInfo(update)
    es_obj = ESObject()
    mongo_obj = MongoObject()

    try:
        
        if (mongo_obj.check_group_auth(tele_bot.user_id, grant_group_name)):
            
            # Lets you see how much you've spent this week
            if tele_bot.type == 1:
                
                now = datetime.now(tz=korea_tz)
                start_of_week = now - timedelta(days=now.weekday())
                end_of_week = start_of_week + timedelta(days=6)

                start_of_week_day = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")
                end_of_week_day = end_of_week.replace(hour=23, minute=59, second=59, microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")
                
                
            # If you enter a specific date, it shows the consumption details for that week.
            else:
                
                input_data = tele_bot.argument.strip()
                
                if (not is_date(input_data, "%Y.%m.%d")):
                    tele_bot.send_message_text(context, "There is a problem with the parameter you entered. Please check again. \nEX01) /cw 2023.07.23 \nEX02) /cw")
                    raise Exception('The data type of the parameter input to the "command_consumption_per_week()" function is not a date type that satisfies the condition. - date_format : {}'.format(input_data))

                std_day = datetime.strptime(input_data, "%Y.%m.%d")

                start_of_week_day = std_day - timedelta(days=std_day.weekday())
                end_of_week_day = start_of_week_day + timedelta(days=6)
            
            # Get total summed money value
            total_cost = es_obj.get_consume_total_cost('consuming_index_prod_new', start_of_week_day, end_of_week_day)
            consume_info_list = es_obj.get_consume_info_detail_list('consuming_index_prod_new', start_of_week_day, end_of_week_day)

            tele_bot.send_message_consume(context, start_of_week_day, end_of_week_day , total_cost, consume_info_list, 10)
        
        else:
            tele_bot.send_message_text(context, "The group does not have access.")
            raise Exception('Group {} attempted to access the "{}" permission.'.format(tele_bot.user_id, grant_group_name))


    except Exception as e:
        global_logger.error(str(e), exc_info=True)

    es_obj.conn_close()
    mongo_obj.conn_close()



# command handler - 9: Check the last meal time. -> /mc
def command_last_meal_time_check(update, context, grant_group_name):
    
    tele_bot = TeleInfo(update)
    es_obj = ESObject()
    mongo_obj = MongoObject()

    try:
        
        if (mongo_obj.check_group_auth(tele_bot.user_id, grant_group_name)):
            
            # time-related information
            now = datetime.now(tz=korea_tz)
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            today_end = now.replace(hour=23, minute=59, second=59, microsecond=0)
            today_start_format = today_start.strftime("%Y-%m-%dT%H:%M:%SZ")
            today_end_format = today_end.strftime("%Y-%m-%dT%H:%M:%SZ")

            # number of meals today
            today_meal_cnt = es_obj.get_index_count('meal_check_index', today_start_format, today_end_format)
            
            check_meal_cnt = 1

            input_document = {} # A json object to be inserted at a specific index
            meal_obj_list = []  # list containing meal_check_index schema information objects

            # If no additional parameters are entered
            if tele_bot.type == 1:
                input_time = now
                check_meal_cnt = today_meal_cnt + 1
                meal_obj_list.append(EsIndexMeal(None, input_time.strftime("%Y-%m-%dT%H:%M:%SZ"), check_meal_cnt, 0))        
            
            # If additional parameters are entered
            elif tele_bot.type == 2:
                
                input_data = tele_bot.argument.strip()
                
                # If the input parameter does not satisfy the specified time format, the function is stopped.
                if (not is_date(input_data, '%H:%M')):
                    tele_bot.send_message_text(context, "There is a problem with the parameter you entered. Please check again. \nEX01) /mc 22:30 \nEX02) /mc")
                    raise Exception('The data type of the parameter input to the "command_last_meal_time_check()" function is not a date type that satisfies the condition. - date_format : {}'.format(input_data))
                
                hour, minute = map(int, input_data.split(":"))
                input_time = datetime(now.year, now.month, now.day, hour, minute)
                
                today_meal_data = es_obj.get_info_term('meal_check_index', today_start_format, today_end_format)
                timestamp_index = 0

                for meal_data in today_meal_data:
                    
                    pres_data = datetime.strptime(meal_data['@timestamp'], "%Y-%m-%dT%H:%M:%SZ")
                    
                    if pres_data > input_time:
                        meal_obj_list.append(EsIndexMeal(meal_data.meta.id, meal_data['@timestamp'], meal_data['laststamp'] + 1, meal_data['alarminfo']))
                    else:
                        timestamp_index += 1
                
                meal_obj_list.append(EsIndexMeal(None, input_time.strftime("%Y-%m-%dT%H:%M:%SZ") ,timestamp_index + 1, 0))
                     
            
            for elem in meal_obj_list:  
                # insert new data.
                if elem.doc_id == None:
                    input_document = {
                        '@timestamp': elem.timestamp,
                        'laststamp' : elem.laststamp,
                        'alarminfo' : elem.alarminfo
                    }

                    check_meal_cnt = elem.laststamp

                # Update existing data.
                else:
                    update_list = [UpdateObj('@timestamp', elem.timestamp), UpdateObj('laststamp', elem.laststamp), UpdateObj('alarminfo', elem.alarminfo)]
                    es_obj.set_modify_index_data('meal_check_index', elem.doc_id, update_list)

            response = es_obj.set_infos_index('meal_check_index', input_document)

            if (response['result'] != 'created'):
                global_logger.error("Elasticsearch Query Executed : {}".format(response))
                send_text = 'Indexing to Elasticsearch failed. [index name : meal_check_index]'
            else:
                global_logger.info("Elasticsearch Query Executed : {}".format(response))
                send_text = 'The [{}] meal was finished at [ {} ]'.format(check_meal_cnt, input_time.strftime("%Y-%m-%dT%H:%M:%SZ"))

            tele_bot.send_message_text(context, send_text)  

        else:
            tele_bot.send_message_text(context, "The group does not have access.")
            raise Exception('Group {} attempted to access the "{}" permission.'.format(tele_bot.user_id, grant_group_name))

    except Exception as e:
        global_logger.error(str(e), exc_info=True)
    
    es_obj.conn_close()
    mongo_obj.conn_close()



# command handler - 10: Check the fasting time. -> /mt
def command_check_fasting_time(update, context, grant_group_name):
    
    tele_bot = TeleInfo(update)
    es_obj = ESObject()
    mongo_obj = MongoObject()

    try:

        if (mongo_obj.check_group_auth(tele_bot.user_id, grant_group_name)):
            
            if tele_bot.type == 1:
                
                cur_time = datetime.now(tz=korea_tz)
                cur_time_format = cur_time.strftime("%Y-%m-%dT%H:%M:%SZ")
                pre_time = 24

                while(True):
                    one_day_pre_time = cur_time - timedelta(hours=pre_time)
                    one_day_pre_time_format = one_day_pre_time.strftime("%Y-%m-%dT%H:%M:%SZ")
                
                    index_data = es_obj.get_recent_info_term('meal_check_index', one_day_pre_time_format, cur_time_format, 1)

                    if (len(index_data) != 0):
                        break
                    else:
                        pre_time += 24

                last_meal_time = datetime.strptime(index_data[0]['@timestamp'], "%Y-%m-%dT%H:%M:%SZ")
                fasting_time = (cur_time.replace(tzinfo=None) - last_meal_time).seconds

                fasting_h = fasting_time // 3600
                fasting_min = (fasting_time % 3600) // 60
                fasting_sec = fasting_time % 60

                send_text = "It's been {} hours and {} minutes and {} seconds since I kept the current fasting time.".format(fasting_h, fasting_min, fasting_sec)

                tele_bot.send_message_text(context, send_text) 

            else:

                input_data = tele_bot.argument.strip()
                tele_bot.send_message_text(context, "There is a problem with the parameter you entered. Please check again. \nEX) /mt")
                raise Exception('The data type of the parameter input to the "command_check_fasting_time()" function is not a data type that satisfies the condition. - input data format : {}'.format(input_data))

        else:
            tele_bot.send_message_text(context, "The group does not have access.")
            raise Exception('Group {} attempted to access the "{}" permission.'.format(tele_bot.user_id, grant_group_name))   
    
    except Exception as e:
        global_logger.error(str(e), exc_info=True)

    es_obj.conn_close()
    mongo_obj.conn_close()



# command handler - 11: Function that removes the last meal time if you enter the meal time incorrectly -> /md
def command_delete_fasting_time(update, context, grant_group_name):
    
    tele_bot = TeleInfo(update)
    es_obj = ESObject()
    mongo_obj = MongoObject()

    try:

        if (mongo_obj.check_group_auth(tele_bot.user_id, grant_group_name)):
            
            if tele_bot.type == 1:
                
                cur_time = datetime.now(tz=korea_tz)
                cur_time_format = cur_time.strftime("%Y-%m-%dT%H:%M:%SZ")

                one_day_pre_time = cur_time - timedelta(hours=24)
                one_day_pre_time_format = one_day_pre_time.strftime("%Y-%m-%dT%H:%M:%SZ")

                recent_index_resp = es_obj.get_recent_info_term('meal_check_index', one_day_pre_time_format, cur_time_format, 1)
                
                target_doc_id = recent_index_resp[0].meta.id
                taget_doc_laststamp = recent_index_resp[0]['laststamp']                
                taget_doc_timestamp = recent_index_resp[0]['@timestamp']
                
                # Remove data that satisfies doc_id
                es_obj.delete_index_info('meal_check_index', target_doc_id)
                
                send_text = "The [{}] meal record on [{}] was canceled.".format(taget_doc_laststamp, taget_doc_timestamp)
                tele_bot.send_message_text(context, send_text) 

            else:
                input_data = tele_bot.argument.strip()
                tele_bot.send_message_text(context, "There is a problem with the parameter you entered. Please check again. \nEX) /md")
                raise Exception('The data type of the parameter input to the "command_delete_fasting_time()" function is not a data type that satisfies the condition. - input data format : {}'.format(input_data))
            
        else:
            tele_bot.send_message_text(context, "The group does not have access.")
            raise Exception('Group {} attempted to access the "{}" permission.'.format(tele_bot.user_id, grant_group_name))

    except Exception as e:
        global_logger.error(str(e), exc_info=True)

    es_obj.conn_close()
    mongo_obj.conn_close()



# command handler - 12: Function that check yearly consumption details -> /cy
def command_consumption_per_year(update, context,grant_group_name):
    
    tele_bot = TeleInfo(update)
    es_obj = ESObject()
    mongo_obj = MongoObject()

    try:
        
        if (mongo_obj.check_group_auth(tele_bot.user_id, grant_group_name)):
            
            if tele_bot.type == 1:
                now = datetime.now(tz=korea_tz)

                # first day of the year
                first_day_of_year = datetime(now.year, 1, 1, 0, 0, 0)

                # last day of this year
                last_day_of_year = datetime(now.year, 12, 31, 23, 59, 59)
                
                # Get total summed money value
                total_cost = es_obj.get_consume_total_cost('consuming_index_prod_new', first_day_of_year, last_day_of_year)

                # List of objects with total consumption amount information per month
                cost_obj_list = es_obj.get_consume_info_list_per_year('consuming_index_prod_new', now.year)
                
                tele_bot.send_message_comsume_per_year(context, first_day_of_year, last_day_of_year, total_cost, cost_obj_list)
                
            # Case where tele_bot.type = 2
            else:
                
                if (tele_bot.argument.isdigit()):

                    check_year = int(tele_bot.argument)

                    if check_year < 2023:
                        tele_bot.send_message_text(context, "Data prior to 2023 cannot be viewed.")
                        raise Exception('User attempt to retrieve data prior to 2023')
                    
                    # first day of the year
                    first_day_of_year = datetime(check_year, 1, 1, 0, 0, 0)

                    # last day of this year
                    last_day_of_year = datetime(check_year, 12, 31, 23, 59, 59)
                    
                    # Get total summed money value
                    total_cost = es_obj.get_consume_total_cost('consuming_index_prod_new', first_day_of_year, last_day_of_year)
                    
                    # List of objects with total consumption amount information per month
                    cost_obj_list = es_obj.get_consume_info_list_per_year('consuming_index_prod_new', check_year)

                    tele_bot.send_message_comsume_per_year(context, first_day_of_year, last_day_of_year, total_cost, cost_obj_list)

                else:
                    input_data = tele_bot.argument.strip()
                    tele_bot.send_message_text(context, "There is a problem with the parameter you entered. Please check again. \nEX01) /cy\nEX02) /cy 2023")
                    raise Exception('The data type of the parameter input to the "command_delete_fasting_time()" function is not a data type that satisfies the condition. - input data format : {}'.format(input_data))

        else:
            tele_bot.send_message_text(context, "The group does not have access.")
            raise Exception('Group {} attempted to access the "{}" permission.'.format(tele_bot.user_id, grant_group_name))


    except Exception as e:
        global_logger.error(str(e), exc_info=True)

    es_obj.conn_close()
    mongo_obj.conn_close()




# command handler - 13: Function to enter appointment information -> /pi
def command_promise_put(update, context, grant_group_name):
    
    tele_bot = TeleInfo(update)
    es_obj = ESObject()
    mongo_obj = MongoObject()
    now = datetime.now(tz=korea_tz)

    try:
        
        if (mongo_obj.check_group_auth(tele_bot.user_id, grant_group_name)):
            
            if tele_bot.type == 2:
                
                parsed_text = tele_bot.argument.split("*")
                party_name = parsed_text[0]
                party_date = parser.parse(parsed_text[1]).strftime("%Y-%m-%dT%H:%M:%SZ")
                party_location = parsed_text[2]
                alarminfo = 0

                party_date_dt = datetime.fromisoformat(party_date.replace("Z", "+09:00"))
                
                if (now > party_date_dt):
                    tele_bot.send_message_text(context, "The appointment time cannot be earlier than the current time.")
                    return
                
                diff = party_date_dt - now 
                diff_sec = diff.days * 24 * 60 * 60 + diff.seconds

                if diff_sec > 86400 and diff_sec <= 259200:
                    alarminfo = 1
                elif diff_sec > 1800 and diff_sec <= 86400:
                    alarminfo = 2
                elif diff_sec <= 1800:
                    alarminfo = 3
                
                input_document = {
                    '@timestamp': now.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    'promise_name' : party_name,
                    'promise_date' : party_date,
                    'promise_location' : party_location,
                    'alarminfo' : alarminfo,
                    'end_yn' : False
                }
                
                response = es_obj.set_infos_index('promise_check_index', input_document)
                
                if (response['result'] != 'created'):
                    raise Exception('Failed to index into "promise_check_index" index. Indexing Information = {}'.format(input_document))
                
            else: 
                tele_bot.send_message_text(context, "The form is incorrect. Please fill out the form below. \n /pi company party*2024-02-03 19:20*jamsil station.")
        else:
            tele_bot.send_message_text(context, "The group does not have access.")
            raise Exception('Group {} attempted to access the "{}" permission.'.format(tele_bot.user_id, grant_group_name))


    except Exception as e:
        global_logger.error(str(e), exc_info=True)

    es_obj.conn_close()
    mongo_obj.conn_close()