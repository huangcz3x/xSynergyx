"""
    stock.py

    Stock class file.
"""
from random import randint
import os
from dotenv import load_dotenv, find_dotenv
#import time
import requests
import pandas as pd #Add to requirements pandas and numpy
#from stock_utils import parse_api_data

load_dotenv(find_dotenv())

def symbols(csv_file):
    """Gathers symbols into list from csv file"""
    stock_lst = []
    try:
        file = pd.read_csv(csv_file)
        symbol = file['Symbol']
        num_list = []
        while len(stock_lst) < 4:
            num = randint(0, len(symbol)-1)
            if num not in num_list:
                stock_lst.append(symbol[num])
                num_list.append(num)
    except FileNotFoundError:
        stock_lst = ['File Not Found']
    except KeyError:
        stock_lst = ['Wrong Format']
    return stock_lst

def crypto_symbols(crypto_big_lst):
    """ Gathers four random crypto currencies from list """
    num_lst = []
    lst = []
    while len(lst) < 4:#Put into separate function
        num = randint(0, len(crypto_big_lst)-1)
        if num not in num_lst:
            lst.append(crypto_big_lst[num])
            num_lst.append(num)
    #print(lst)
    return lst

class Stock:
    """Class object gathers stock information and news for selected companies"""
    IEX_SANDBOX_URL = "https://sandbox.iexapis.com/stable/stock/market/batch?"
    IEX_SANDBOX_NEWS_URL = "https://sandbox.iexapis.com/stable/stock/market/batch?"
    IEX_SANDBOX_CRYPTO_URL = "https://sandbox.iexapis.com/stable/crypto/{}/price"

    IEX_CRYPTO_SYMBOL_URL = "https://sandbox.iexapis.com/stable/ref-data/crypto/symbols"
    IEX_CLOUD_REAL_STOCK_URL = "https://cloud.iexapis.com/stable/stock/market/batch?"
    IEX_CLOUD_REAL_CRYPTO_URL = "https://cloud.iexapis.com/stable/crypto/{}/price"

    NYT_URL = "https://api.nytimes.com/svc/search/v2/articlesearch.json"

    def default(self):
        """Default homescreen with stock information"""
        home_lst = []
        mega_stock = symbols('stock_categories/mega.csv')
        tech_stock = symbols('stock_categories/tech.csv')
        energy_stock = symbols('stock_categories/energy.csv')
        finance_stock = symbols('stock_categories/finance.csv')
        utilities_stock = symbols('stock_categories/pub_utilities.csv')
        home_lst.append({'Mega': self.search(mega_stock, 'Mega')})
        home_lst.append({'Tech': self.search(tech_stock, 'Tech')})
        home_lst.append({'Energy': self.search(energy_stock, 'Energy')})
        home_lst.append({'Utilities': self.search(utilities_stock, 'Utilities')})
        home_lst.append({'Finance': self.search(finance_stock, 'Finance')})
        home_lst.append({'Cryptocurrency' : self.crypto("")})
        return home_lst

    #query is a list and category should be None when searching for indiviudal stock
    def search(self, query, category):
        """Takes list of symbols, and gathers stock information"""
        data = {}
        stock_symbols = None
        if len(query) == 1:
            stock_symbols = query[0]
        else:
            stock_symbols = query[0]
            for i in range(1, len(query)):
                stock_symbols += ',{}'.format(query[i])
        #'token': os.getenv('IEX_CLOUD_SANDBOX_KEY')
        params = {
            'symbols': stock_symbols,
            'types': 'company,quote',
            #'token': os.getenv('IEX_CLOUD_SANDBOX_KEY')
            'token' : os.getenv('IEX_CLOUD_REAL_KEY')
        }
        stocks = [x.upper() for x in query] #capatalize symbols for json file
        #response = requests.get(self.IEX_SANDBOX_URL, params=params)
        response = requests.get(self.IEX_CLOUD_REAL_STOCK_URL, params=params)
        if response.status_code == 404: #Resource not found
            crypto_search = self.crypto(query[0])
            data[query[0]] = 'Not Found'
            return crypto_search
        if response.status_code > 500: #Server error
            data['Error'] = 'Server Error'
            return data
        #print(response)
        response_json = response.json()
        if response_json[query[0]]['quote'] is None: #200 status but still not valid stock symbol
            data[query[0]] = 'Not Found'
            return data
        # print(response_json)
        for stock in stocks:
            stock_dict = {}
            stock_quote = response_json[stock]['quote']
            stock_dict['Symbol'] = stock
            stock_dict['Company'] = stock_quote['companyName']
            stock_dict['High'] = stock_quote['high']
            stock_dict['Low'] = stock_quote['low']
            stock_dict['Price'] = stock_quote['latestPrice']
            stock_dict['Category'] = category
            stock_dict['Overview'] = response_json[stock]['company']['description']
            data[stock] = stock_dict
        return data

    def news(self, stock):
        """ Gathers five articles related to company after click with NYT API
            Use IEX API in case of KeyError from NYT reaching minute request limit.
        """
        news = []
        try:
            params = {
                'q' : stock + ' ',
                'news_desk' : 'Business',
                'api-key': os.getenv('NYT_KEY'),
                'sort': 'relevance'
            }
            response = requests.get(self.NYT_URL, params=params)
            if response.status_code == 429: #Too many requests
                raise KeyError("Response 429")
            if response.status_code == 404:
                raise KeyError("Response 404")
            data = response.json()
            for i in range(5):
                # print(data['response']['docs'][i]['headline']['main'])
                # print(data['response']['docs'][i])
                news.append({
                    'headline': data['response']['docs'][i]['headline']['main'],
                    'snippet': data['response']['docs'][i]['snippet']
                })
        except KeyError:
            params = {
                'symbols': stock,
                'token': os.getenv('IEX_CLOUD_REAL_KEY'),
                'types': 'news',
                'last': 5
            }
            response = requests.get(self.IEX_CLOUD_REAL_STOCK_URL, params=params)
            # print(response)
            print("IEX " + str(response))
            data = response.json()
            stock_news = data[stock]['news']
            for headline in stock_news:
                #print(str(headline['headline']))
                news.append({
                    'headline': headline['headline'],
                    'snippet': headline['summary']
                })
        except ValueError: #simplejson.errors.JSONDecodeError
            print("Decode JSON failed")
            news.append({'Error': 'Refresh page'})
        except IndexError:
            print("Index Error")
            news.append({'Error': 'News error'})
        # print(news)
        return news

    def crypto(self, query):
        """ Takes empty string to randomly search for 4 currencies, and search if stock entered
         with length greater than 0. Returns list with dictionaires symbol and price"""
        symbol_lst = []
        homescreen_lst = None
        data = {}
        crypto_lst = {}
        params = {
            'token': os.getenv('IEX_CLOUD_SANDBOX_KEY')
        }
        response = requests.get(self.IEX_CRYPTO_SYMBOL_URL, params=params)
        symbol_json = response.json()
        for symbol in symbol_json: #Gathers accepted list of currencies
            symbol_lst.append(symbol["symbol"])
        params = {
            'token': os.getenv('IEX_CLOUD_REAL_KEY')
        }
        if len(query) > 0:
            response = requests.get(self.IEX_CLOUD_REAL_CRYPTO_URL.format(query), params=params)
            if response.status_code == 404: #Not found
                return {query : 'Not Found'}
            if response.status_code > 500: #Server error
                return {'Error' : 'Server Error'}
            data = response.json()
            crypto_lst = {'Symbol' : query, 'Price' : data['price'], 'Category': 'Cryptocurrency'}
        else:
            homescreen_lst = crypto_symbols(symbol_lst)
            #print(homescreen_lst)
            for i in homescreen_lst:
                crypto_dict = {}
                response = requests.get(self.IEX_CLOUD_REAL_CRYPTO_URL.format(i), params=params)
                if response.status_code > 500: #Server error
                    return {'Error' : 'Server Error'}
                data = response.json()
                crypto_dict['Symbol'] = i
                crypto_dict['Price'] = data['price']
                crypto_dict['Category'] = 'Cryptocurrency'
                crypto_lst[i] = crypto_dict
        return crypto_lst
#TEST = Stock()
#print(TEST.default())
#print(TEST.crypto("wer2sdvv"))
# for count in range(20):
#     TEST.news('AAPL')
#print(TEST.crypto('ATOWS'))
#print(TEST.search(['ATOWS'], None))
#stock_data = TEST.default()
#print(stock_data)
#print(parse_api_data(stock_data))
