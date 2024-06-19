from telegram.ext import *
import json
from bs4 import BeautifulSoup
import requests
from elasticsearch import Elasticsearch
import logging
import logging.handlers
from datetime import datetime, timedelta
import cv2
from elasticsearch_dsl import Search, Q, A
import calendar
import pytz
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import time
from dateutil import parser
from dateutil.relativedelta import relativedelta
import os
from dotenv import load_dotenv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from collections import OrderedDict

