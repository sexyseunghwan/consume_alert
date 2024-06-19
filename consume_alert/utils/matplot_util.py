from utils.common_util import *
from import_data.common import *


# An object containing information in a consumption trend
class ConsumeInfoDict:

    def __init__(self, totals_cost, start_date, end_date, consume_res_list):
        self.totals_cost = totals_cost
        self.start_date = start_date
        self.end_date = end_date
        self.consume_res_list = consume_res_list


# Function that objectifies data on consumption trends
def parsing_consume_object(totals_cost, start_date, end_date, consume_list):

    order_dict = OrderedDict()
    consume_res_list = []
    current_date = start_date

    while current_date <= end_date:
        order_dict[current_date.strftime('%Y-%m-%d')] = 0
        current_date += timedelta(days=1)

    for elem in consume_list:
        
        elem_date = elem.date 
        elem_cost = elem.cost 
        
        # parsing into datetime objects
        dt = datetime.fromisoformat(elem_date.rstrip('Z'))
        # Extract date in year-month-day format
        date_only = dt.date().isoformat()
        
        order_dict[date_only] += elem_cost
        
    total_consume = 0

    for date, total_cost in order_dict.items():
        total_consume += total_cost
        consume_res_list.append(total_consume)

    consume_info = ConsumeInfoDict(totals_cost, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'), consume_res_list)
    
    return consume_info


# Function that visualizes two consumption trends
def calculate_cosume_res_dual(consume_list, totals_cost, start_date, end_date, consume_pre_list, totals_pre_cost, pre_start_date, pre_end_date):
    
    consume_info = parsing_consume_object(totals_cost, start_date, end_date, consume_list)
    consume_info_pre = parsing_consume_object(totals_pre_cost, pre_start_date, pre_end_date, consume_pre_list)
    
    draw_graph_dual(consume_info, consume_info_pre)


# Function that visualizes consumption trends
def calculate_cosume_res_single(consume_list, totals_cost, start_date, end_date):
    
    consume_info = parsing_consume_object(totals_cost, start_date, end_date, consume_list)
    
    draw_graph_single(consume_info)


# Formatter Function Definition
def thousands_formatter(x, pos):
    return f'{int(x):,}'


# Function that draws a graph
def draw_graph(plt, title, x_label, y_label, save_fig):

    # y-axis label formatting
    formatter = FuncFormatter(thousands_formatter)
    plt.gca().yaxis.set_major_formatter(formatter)
    
    plt.title(title)
    plt.xlabel(x_label)
    plt.ylabel(y_label)  

    plt.legend()
    plt.savefig(save_fig)  
    plt.close()      


# Function that plots a graph of two consumption trends
def draw_graph_dual(consume_info_1, consume_info_2):
    
    longer_len = 0

    consume_info_1_len = len(consume_info_1.consume_res_list)
    consume_info_2_len = len(consume_info_2.consume_res_list)

    if consume_info_1_len != consume_info_2_len:
        # Determine the shorter list and the gap in length
        shorter_info = consume_info_1 if consume_info_1_len < consume_info_2_len else consume_info_2
        longer_len = max(consume_info_1_len, consume_info_2_len)
        gap = longer_len - len(shorter_info.consume_res_list)
        
        # Append the last element of the shorter list to itself until lengths match
        last_element = shorter_info.consume_res_list[-1]
        shorter_info.consume_res_list.extend([last_element] * gap)
    else:
        longer_len = consume_info_1_len
    
    x = [i+1 for i in range(longer_len)]
    
    # Create Graphs
    plt.figure(figsize=(10,7))
    plt.plot(x, consume_info_1.consume_res_list, color='red', label="[{} ~ {}]".format(consume_info_1.start_date, consume_info_1.end_date))
    plt.plot(x, consume_info_2.consume_res_list, color='black', label="[{} ~ {}]".format(consume_info_2.start_date, consume_info_2.end_date))

    draw_graph(plt, "[{} ~ {}] {} won".format(consume_info_1.start_date, consume_info_1.end_date, consume_info_1.totals_cost), 'Date', 'Consume Cost', './data/img/plot.png')


# Function that plots a graph of a consumption trend
def draw_graph_single(consume_info):
    
    consume_info_len = len(consume_info.consume_res_list)
    
    x = [i+1 for i in range(consume_info_len)]
    
    # Create Graphs
    plt.figure(figsize=(10,7))
    plt.plot(x, consume_info.consume_res_list, color='red', label="[{} ~ {}]".format(consume_info.start_date, consume_info.end_date))

    draw_graph(plt, "[{} ~ {}] {} won".format(consume_info.start_date, consume_info.end_date, consume_info.totals_cost), 'Date', 'Consume Cost', './data/img/plot.png')