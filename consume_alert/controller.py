from utils.common_util import *
from command import *
from config import global_logger

def run_app():

    load_dotenv()

    global_logger.info("Python Telegram Bot start")
    
    tele_token = os.getenv("TELE_TOKEN")

    updater = Updater(token=tele_token, use_context=True)
    dispatcher = updater.dispatcher    
    
    # CommandHandler Object List: To add a new object, put it inside the list below.
    handler_list = [ 
                    CommandHandler('call', lambda update, context: command_character(update, context, 'call_info')), 
                    CommandHandler('m', lambda update, context: command_currency(update, context, 'call_info')),
                    CommandHandler('c', lambda update, context: command_consumption(update, context, 'consume_info')),
                    CommandHandler('cm', lambda update, context: command_consumption_per_mon(update, context, 'consume_info')),
                    CommandHandler('ctr', lambda update, context: command_consumption_per_term(update, context, 'consume_info')),
                    CommandHandler('ct', lambda update, context: command_consumption_per_today(update, context, 'consume_info')),
                    CommandHandler('cs', lambda update, context: command_consumption_per_salary(update, context, 'consume_info')),
                    CommandHandler('cw', lambda update, context: command_consumption_per_week(update, context, 'consume_info')),
                    CommandHandler('mc', lambda update, context: command_last_meal_time_check(update, context, 'meal_check_info')),
                    CommandHandler('mt', lambda update, context: command_check_fasting_time(update, context, 'meal_check_info')),
                    CommandHandler('md', lambda update, context: command_delete_fasting_time(update, context, 'meal_check_info')),
                    CommandHandler('cy', lambda update, context: command_consumption_per_year(update, context, 'consume_info')),
                    CommandHandler('pi', lambda update, context: command_promise_put(update, context, 'promise_input'))
                    ]                   
    
    for handler in handler_list:
        dispatcher.add_handler(handler)
    
    #polling
    updater.start_polling()
    updater.idle()

    global_logger.info("Python Telegram Bot Stop")
