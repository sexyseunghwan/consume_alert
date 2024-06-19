from import_data.common import *
from config import global_logger
from utils.common_util import *


class TeleInfo:
    
    def __init__(self, update):
        self.update = update  
        self.get_tele_bot_pre_check()

    def get_tele_bot_pre_check(self):
        self.user_id = self.update.effective_chat.id
        self.user_text = self.update.message.text

        tele_list = self.user_text.split(" ", 1)

        if (len(tele_list) == 1):
            self.get_tele_bot_obj()
        elif (len(tele_list) == 2):
            self.get_tele_bot_param_obj()
        else:
            self.update = None
            self.user_id = None
            self.user_text = None
    
    ### If there is a parameter after the command, it is classified as type 2
    ### If there is no parameter, it is classified as type 1.
    def get_tele_bot_param_obj(self):
        self.type = 2
        command, argument = self.user_text.split(" ", 1)
        self.command = command
        self.argument = argument
   

    def get_tele_bot_obj(self):
        self.type = 1
        self.command = self.user_text.split(" ", 1)[0]


    # Function that sends a message through a telegram chat bot and then returns the response result.
    def send_msg_request(self, message):
        
        #bot_token = read_file_to_json('./data/conn_info/tele_info.json')['token']
        bot_token = os.getenv("TELE_TOKEN")
        send_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

        data = {
            "chat_id": self.user_id,
            "text": message
        }
        
        response = requests.post(send_url, data=data)
        
        return response.json()  # Return response result
    

    # Function that allows a Telegram bot to forward a message to a specific chat room
    def send_message_text(self, context, send_text):
        context.bot.send_message(chat_id=self.user_id, text=send_text)



    """
    When sending a message through telegram chat bot,
    A timeout error occurs when messages exceeding the threshold are sent within a certain time.
    To avoid this error, if the message is not sent due to timeout, stop the thread itself for 30 seconds and then send the message again.
    """
    def send_message_confirm(self, send_text):

        msg_flag = True

        while(msg_flag):
            resp = self.send_msg_request(send_text)
            
            if (resp['ok']):
                msg_flag = False
            else:
                time.sleep(30)


    # To solve the "ERROR: Message is too long" problem, modify the source code 
    # so that the telegram bot cuts off text of a certain length and sends it to the telegram chat room.
    def send_message_consume(self, context, start_dt , end_dt, total_cost, consume_info_list, cut_cnt):
        
        consume_list_len = len(consume_info_list)
        loop_cnt = 0
        consume_q = consume_list_len // cut_cnt
        consume_r = consume_list_len % cut_cnt

        if consume_r != 0:
            loop_cnt = consume_q + 1
        else:
            loop_cnt = consume_q

        if consume_list_len == 0:
            self.send_message_confirm("The money you spent from [{} ~ {}] is [ {} won ] \nThere is no consumption history to be viewed during that period.".format(start_dt, end_dt, total_cost))
    
        for i in range(0, loop_cnt):  
            
            send_text = ""
            end_idx = min(consume_list_len, (i+1)*cut_cnt)

            if (i == 0):
                send_text += "The money you spent from [{} ~ {}] is [ {} won ] \n=========[DETAIL]=========\n".format(start_dt, end_dt, total_cost)
            
            for j in range(cut_cnt*i, end_idx):
                send_text += '---------------------------------\n'
                send_text += 'name : {}\n'.format(consume_info_list[j].name)
                send_text += 'date : {}\n'.format(consume_info_list[j].date)
                send_text += 'cost : {:,}\n'.format(consume_info_list[j].cost) 
            
            self.send_message_confirm(send_text)
            
    
    # Function that sends a message about the amount spent per year
    def send_message_comsume_per_year(self, context, start_dt , end_dt, total_cost, consum_obj_list):
        
        send_text = "The money you spent from [{} ~ {}] is [ {} won ] \n=========[DETAIL]=========\n".format(start_dt.strftime("%Y-%m-%dT%H:%M:%SZ"), end_dt.strftime("%Y-%m-%dT%H:%M:%SZ"), total_cost)
        
        for elem in consum_obj_list:
            target_date = elem[0]
            cosume_cost = elem[1]
            send_text += "[{}] consumption amount : {} won.\n".format(target_date, cosume_cost)

        context.bot.send_message(chat_id=self.user_id, text=send_text)