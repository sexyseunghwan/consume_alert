from import_data.common import *
from config import global_logger


"""
Function that reads a json file and returns a json object
"""
def read_file_to_json(file_path):

    return_data = None
    
    try:      
        with open(file_path, "r") as f:
            return_data = json.load(f)
    except Exception as e:
        return_data = None
        global_logger.error(str(e), exc_info=True)
    
    return return_data



"""
A function that checks whether an input string is a date type or not.
"""
def is_date(string_date, date_format):

    try:
        datetime.strptime(string_date, date_format)
        return True
    except Exception as e:
        global_logger.error(str(e))
        return False


"""
Function that sends exchange rate information and stock price information to the user
"""
def exchange_rate(query):

    currency_dict = {}

    try:
        
        global_logger.info('{} query executed'.format(query))
        
        # Access the search results page to get HTML code
        url = f"https://www.google.com/search?q={query}"
        response = requests.get(url)
        html = response.text
        
        # Analyze HTML code to extract desired data
        soup = BeautifulSoup(html, "html.parser")
        
        target_currency = soup.find("span", {"class": "r0bn4c rQMQod"}).get_text()
        korea_won = soup.find("div", {"class": "BNeawe iBp4i AP7Wnd"}).get_text()
        
        currency_dict['target_currency'] = target_currency
        currency_dict['korea_won'] = korea_won
    
    except Exception as e:
        global_logger.error(str(e))
    finally:
        return currency_dict

    
"""
Functions that send pictures to users
"""
def send_image(update, context, file_path):
    
    try:
        
        # Convert an image to a format that can be read and transferred
        with open(file_path, "rb") as f:
            img = cv2.imread(file_path)
            img_bytes = cv2.imencode(".jpg", img)[1].tobytes()
        
        # Transfer Image
        context.bot.send_photo(chat_id=update.effective_chat.id, photo=img_bytes)

        global_logger.info('A picture of a {} has been sent.'.format(file_path))

    except Exception as e:
        global_logger.error(str(e)) 