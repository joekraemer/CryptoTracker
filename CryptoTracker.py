import requests
import time
import datetime
import hmac
import hashlib
import krakenex
import csv
from gemini.client import Client
from poloniex import Poloniex
try:
    from urllib import urlencode
    from urlparse import urljoin
except ImportError:
    from urllib.parse import urlencode
    from urllib.parse import urljoin

#API Keys
#PLEASE ADD YOU KEYS HERE
bittrex_api_key = {"key": "0000000000", "secret": "f0000000000000"}
gemini = Client('00000000000','0000000000000')

#Mining Deposit Address
#CHANGE TO YOUR ADDRESS
eth_mining_address = '0x2e699bb880bd665bf2339336c921d0c6fa369b15'

#cold storage addresses
#PLEASE CHANGE TO YOUR ADDRESSES
btc_wallet = ['1DccyaqJHKbq4PQJEqbT8xDXkoy2dnuzhq', '12beH3MQjGNVXKPe6skmsizVh3Me1tYgd4', '1L5VcgP8oH7EanhpD5Uwbx9u5qrFwuhfsp', '1JwQW9eNGbkSNAb74wTBaSWjZJvpubQ1L', '1KWi83jGbu5FKDfVY2UmDiGv6ZTwUFkQHY', '1GZChf7gRyDdUnYP72bKVfvTQ4NgY2sNdS','19KMNsxzULirWAUBYE6JCSQoKhQK3difD1','1MHryQ1z1L6Gorjr4Nqw8kTFw5CZKAKG7S', '1G6uYSKNCgRkrhixmBQuCch4pXuLnL4UyM','14wDNjMRAiVaWqQyCCQDbaVYF1KWMK6Ujg', '1B4vf77HEGH8zVCFBtdk4UAfC2SCDX63yE', '13jvXFBFMjYRfp69azuvNYyAu4aZsM9APU', '1MtA3DgenJX22SgpfXf6MhyBLFRudBpLt7']
cols_eth_stor = ['0xa4C2F38ab69cCB5Ac14e27a65D64e18ddfd73C6A']
depo_chase = 250+249.5


#global tracking variables
tracker = {}
balances = {}
market_values = {}

#****Taken from https://github.com/ericsomdahl/python-bittrex
class bittrex(object):
    BASE_URL = 'https://bittrex.com/api/v1.1/%s/'
    MARKET_SET = {'getopenorders', 'cancel', 'sellmarket', 'selllimit', 'buymarket', 'buylimit'}
    ACCOUNT_SET = {'getbalances', 'getbalance', 'getdepositaddress', 'withdraw', 'getorderhistory'}

    def __init__(self,key,secret):
        self.api_key = key
        self.api_secret = secret
    def api_query(self, method, options=None):
        """
        Queries Bittrex with given method and options
        :param method: Query method for getting info
        :type method: str
        :param options: Extra options for query
        :type options: dict
        :return: JSON response from Bittrex
        :rtype : dict
        """
        if not options:
            options = {}
        nonce = str(int(time.time() * 1000))
        method_set = 'public'

        if method in bittrex.MARKET_SET:
            method_set = 'market'
        elif method in bittrex.ACCOUNT_SET:
            method_set = 'account'

        request_url = (bittrex.BASE_URL % method_set) + method + '?'

        if method_set != 'public':
            request_url += 'apikey=' + self.api_key + "&nonce=" + nonce + '&'

        request_url += urlencode(options)

        return requests.get(
            request_url,
            headers={"apisign": hmac.new(self.api_secret.encode(), request_url.encode(), hashlib.sha512).hexdigest()}
        ).json()
    def get_markets(self):
        """
        Used to get the open and available trading markets
        at Bittrex along with other meta data.
        :return: Available market info in JSON
        :rtype : dict
        """
        return self.api_query('getmarkets')
    def get_currencies(self):
        """
        Used to get all supported currencies at Bittrex
        along with other meta data.
        :return: Supported currencies info in JSON
        :rtype : dict
        """
        return self.api_query('getcurrencies')
    def get_ticker(self, market):
        """
        Used to get the current tick values for a market.
        :param market: String literal for the market (ex: BTC-LTC)
        :type market: str
        :return: Current values for given market in JSON
        :rtype : dict
        """
        return self.api_query('getticker', {'market': market})
    def get_market_summaries(self):
        """
        Used to get the last 24 hour summary of all active exchanges
        :return: Summaries of active exchanges in JSON
        :rtype : dict
        """
        return self.api_query('getmarketsummaries')
    def get_orderbook(self, market, depth_type, depth=20):
        """
        Used to get retrieve the orderbook for a given market
        :param market: String literal for the market (ex: BTC-LTC)
        :type market: str
        :param depth_type: buy, sell or both to identify the type of orderbook to return.
            Use constants BUY_ORDERBOOK, SELL_ORDERBOOK, BOTH_ORDERBOOK
        :type depth_type: str
        :param depth: how deep of an order book to retrieve. Max is 100, default is 20
        :type depth: int
        :return: Orderbook of market in JSON
        :rtype : dict
        """
        return self.api_query('getorderbook', {'market': market, 'type': depth_type, 'depth': depth})
    def get_market_summary(self, market):
        """
        Used to get a market summary for a given market
        :param market:
        :return: dic
        """
        return self.api_query('getmarketsummary', {'market': market})
    def get_market_history(self, market, count):
        """
        Used to retrieve the latest trades that have occurred for a
        specific market.
        /market/getmarkethistory
        :param market: String literal for the market (ex: BTC-LTC)
        :type market: str
        :param count: Number between 1-100 for the number of entries to return (default = 20)
        :type count: int
        :return: Market history in JSON
        :rtype : dict
        """
        return self.api_query('getmarkethistory', {'market': market, 'count': count})
    def buy_market(self, market, quantity):
        """
        Used to place a buy order in a specific market. Use buymarket to
        place market orders. Make sure you have the proper permissions
        set on your API keys for this call to work
        /market/buymarket
        :param market: String literal for the market (ex: BTC-LTC)
        :type market: str
        :param quantity: The amount to purchase
        :type quantity: float
        :param rate: The rate at which to place the order.
            This is not needed for market orders
        :type rate: float
        :return:
        :rtype : dict
        """
        return self.api_query('buymarket', {'market': market, 'quantity': quantity})
    def buy_limit(self, market, quantity, rate):
        """
        Used to place a buy order in a specific market. Use buylimit to place
        limit orders Make sure you have the proper permissions set on your
        API keys for this call to work
        /market/buylimit
        :param market: String literal for the market (ex: BTC-LTC)
        :type market: str
        :param quantity: The amount to purchase
        :type quantity: float
        :param rate: The rate at which to place the order.
            This is not needed for market orders
        :type rate: float
        :return:
        :rtype : dict
        """
        return self.api_query('buylimit', {'market': market, 'quantity': quantity, 'rate': rate})
    def sell_market(self, market, quantity):
        """
        Used to place a sell order in a specific market. Use sellmarket to place
        market orders. Make sure you have the proper permissions set on your
        API keys for this call to work
        /market/sellmarket
        :param market: String literal for the market (ex: BTC-LTC)
        :type market: str
        :param quantity: The amount to purchase
        :type quantity: float
        :param rate: The rate at which to place the order.
            This is not needed for market orders
        :type rate: float
        :return:
        :rtype : dict
        """
        return self.api_query('sellmarket', {'market': market, 'quantity': quantity})
    def sell_limit(self, market, quantity, rate):
        """
        Used to place a sell order in a specific market. Use selllimit to place
        limit orders Make sure you have the proper permissions set on your
        API keys for this call to work
        /market/selllimit
        :param market: String literal for the market (ex: BTC-LTC)
        :type market: str
        :param quantity: The amount to purchase
        :type quantity: float
        :param rate: The rate at which to place the order.
            This is not needed for market orders
        :type rate: float
        :return:
        :rtype : dict
        """
        return self.api_query('selllimit', {'market': market, 'quantity': quantity, 'rate': rate})
    def cancel(self, uuid):
        """
        Used to cancel a buy or sell order
        /market/cancel
        :param uuid: uuid of buy or sell order
        :type uuid: str
        :return:
        :rtype : dict
        """
        return self.api_query('cancel', {'uuid': uuid})
    def get_open_orders(self, market):
        """
        Get all orders that you currently have opened. A specific market can be requested
        /market/getopenorders
        :param market: String literal for the market (ie. BTC-LTC)
        :type market: str
        :return: Open orders info in JSON
        :rtype : dict
        """
        return self.api_query('getopenorders', {'market': market})
    def get_balances(self):
        """
        Used to retrieve all balances from your account
        /account/getbalances
        :return: Balances info in JSON
        :rtype : dict
        """
        return self.api_query('getbalances', {})
    def get_balance(self, currency):
        """
        Used to retrieve the balance from your account for a specific currency
        /account/getbalance
        :param currency: String literal for the currency (ex: LTC)
        :type currency: str
        :return: Balance info in JSON
        :rtype : dict
        """
        return self.api_query('getbalance', {'currency': currency})
    def get_deposit_address(self, currency):
        """
        Used to generate or retrieve an address for a specific currency
        /account/getdepositaddress
        :param currency: String literal for the currency (ie. BTC)
        :type currency: str
        :return: Address info in JSON
        :rtype : dict
        """
        return self.api_query('getdepositaddress', {'currency': currency})
    def withdraw(self, currency, quantity, address):
        """
        Used to withdraw funds from your account
        /account/withdraw
        :param currency: String literal for the currency (ie. BTC)
        :type currency: str
        :param quantity: The quantity of coins to withdraw
        :type quantity: float
        :param address: The address where to send the funds.
        :type address: str
        :return:
        :rtype : dict
        """
        return self.api_query('withdraw', {'currency': currency, 'quantity': quantity, 'address': address})
    def get_order_history(self, market, count):
        """
        Used to reterieve order trade history of account
        /account/getorderhistory
        :param market: optional a string literal for the market (ie. BTC-LTC). If ommited, will return for all markets
        :type market: str
        :param count: optional 	the number of records to return
        :type count: int
        :return: order history in JSON
        :rtype : dict
        """
        return self.api_query('getorderhistory', {'market':market, 'count': count})
#Take from https://github.com/ericsomdahl/python-bittrex****

class nano(object):
    def __init__(self, eth_address):
        self.eth_address = eth_address
    def url_creator(self, type):

        """
        creates the unique url for each API function
        :param type: the type of API request
        :type type: str
        :return: completed url with mining address and API function
        :rtype : str
        """

        url = 'https://api.nanopool.org/v1/eth/' + type + '/' + nano.eth_address
        return (url)
    def balance(self):

        """
        sends a request to Nanopool for ETH balance of the miner
        :return: ETH balance
        :rtype : str
        """

        url = self.url_creator('balance')
        resp = requests.get(url)

        if resp.status_code != 200:
            print('Oops, something went wrong')

        data = resp.json()

        if data['status'] == True:
            return (data['data'])

        elif data['status'] == False:
            print('Oops, something went wrong' + "\n" + data["error"])

        else:
            print("Something went terribly wrong, please run and hide")
    def avghashrate(self):

        """
        sends request to Nanopool to get the average hash rates for a variety of time frames
        :param type: the type of API request
        :type type: str
        :return: dictionary with average hash rates for different time frames
        :rtype : dict
        """

        url = self.url_creator('avghashrate')
        resp = requests.get(url)

        if resp.status_code != 200:
            print('Oops, something went wrong')

        data = resp.json()

        if data['status'] == True:
            return (data['data'])

        elif data['status'] == False:
            print('Oops, something went wrong' + "\n" + data["error"])

        else:
            print("Something went terribly wrong, please run and hide")
    def currenthashrate(self):

        """
        Queries Nanopool and returns current hashrate
        :return: JSON data from Nanopool
        :rtype : str
        """

        url = self.url_creator('hashrate')
        resp = requests.get(url)

        if resp.status_code != 200:
            print('Oops, something went wrong')

        data = resp.json()

        if data['status'] == True:
            return (data['data'])

        elif data['status'] == False:
            print('Oops, something went wrong' + "\n" + data["error"])

        else:
            print("Something went terribly wrong, please run and hide")
    def info(self):

        """
        Queries Nanopool and returns info
        :return: JSON data from Nanopool
        :rtype : dict
        """


        url = self.url_creator('user')
        resp = requests.get(url)

        if resp.status_code != 200:
            print('Oops, something went wrong')

        data = resp.json()

        if data['status'] == True:
            return (data['data'])
        elif data['status'] == False:
            print('Oops, something went wrong' + "\n" + data["error"])

        else:
            print("Something went terribly wrong, please run and hide")
    def profitability(self):

        """
        Queries Nanopool and returns current profitability
        :return: JSON data from Nanopool
        :rtype : str
        """


        hash_24hr = self.avghashrate()['h24']
        url = 'https://api.nanopool.org/v1/eth/approximated_earnings/' + str(hash_24hr)
        resp = requests.get(url)

        if resp.status_code != 200:
            print('Oops, something went wrong')

        data = resp.json()

        if data['status'] == True:
            return (data['data']['month']['dollars'])

        elif data['status'] == False:
            print('Oops, something went wrong' + "\n" + data["error"])

        else:
            print("Something went terribly wrong, please run and hide")
class bitchain(object):
    def balance(self, btc_address):

        """
        Queries Bitchain and returns balance at a given bitcoin address
        :return: JSON data from Bitchain
        :rtype : str
        """

        url = 'https://blockchain.info/rawaddr/' + btc_address
        resp = requests.get(url)

        if resp.status_code != 200:
            print('Oops, something went wrong')

        data = resp.json()

        return (data['final_balance'])
class ethchain(object):

    def balance(self, eth_address):

        """
        Queries Ethchain and returns balance at a given ethereum address
        :return: JSON data from Ethchain
        :rtype : str
        """

        url = 'https://api.blockcypher.com/v1/eth/main/addrs/' + eth_address + '/balance'
        resp = requests.get(url)

        if resp.status_code != 200:
            print('Oops, something went wrong')

        data = resp.json()

        return (data['final_balance'])

#initializing the classes
nano = nano(eth_mining_address)
bittrex = bittrex(bittrex_api_key["key"], bittrex_api_key["secret"])
polo = Poloniex()
krak = krakenex.API()
bc = bitchain()
ec = ethchain()

def calc_ETH_yields(hashrateMH):
    netHash = 6807  # network hash rate in GH/s
    blocktime = 12  # in seconds
    BlockReward = 5  # ETH

    userRatio = (hashrateMH * 1e6) / (netHash * 1e9)
    blocksPerMin = 60 / blocktime
    ETHPerMin = blocksPerMin * BlockReward  # input or pulled off a website

    ETHPerMin = ETHPerMin * userRatio
    ETHPerHour = ETHPerMin * 60
    ETHPerDay = ETHPerHour * 24
    ETHPerWeek = ETHPerDay * 7
    ETHPerMonth = ETHPerDay * 30
    ETHPerYear = ETHPerDay * 365

    ETH_yield = [ETHPerMin, ETHPerHour, ETHPerDay, ETHPerWeek, ETHPerMonth,
                 ETHPerYear]  # min, hour, day, week, month, year

    return (ETH_yield)
def calc_USD_yields(hashrateMH):
    ETHtoBTC = .005  # in BTC  #API reference grab multiple?
    BTCtoUSD = 1700  # in USD #API reference grab multiple?

    ETH_yield = calc_ETH_yields(hashrateMH)

    USD_yield = ETH_yield * ETHtoBTC * BTCtoUSD

    return (USD_yield)
def calc_BTC_yields(hashrateMH):
    ETHtoBTC = .005  # in BTC  #API reference grab multiple?

    ETH_yield = calc_ETH_yields(hashrateMH)

    BTC_yield = ETH_yield * ETHtoBTC

    return BTC_yield
def current_market_values():
    bitBTC_ETH = bittrex.get_market_summary("BTC-ETH")["result"][0]['Last']
    bitBTC_CURE = bittrex.get_market_summary('BTC-CURE')["result"][0]['Last']
    poloBTC_ETH = polo.returnTicker()["BTC_ETH"]['last']
    gemBTC_ETH = gemini.get_ticker("ethbtc")["last"]
    gemBTC_USD = gemini.get_ticker("btcusd")["last"]
    gemETH_USD = gemini.get_ticker("ethusd")["last"]
    temp_dict = {"bitBTC_ETH": bitBTC_ETH, "bitBTC_CURE": bitBTC_CURE, "poloBTC_ETH": poloBTC_ETH, "gemBTC_ETH": gemBTC_ETH, "gemBTC_USD": gemBTC_USD, "gemETH_USD": gemETH_USD}
    return(temp_dict)
def current_balances():

    total_USD = float(gemini.get_balance()[1]['available']) + depo_chase
    total_BTC = float(gemini.get_balance()[0]["available"]) + bittrex.get_balance('BTC')['result']["Available"] + float(btc_cold_stor_bal(btc_wallet))
    total_ETH = float(gemini.get_balance()[2]["available"]) + nano.balance() + eth_cold_stor_bal(cols_eth_stor)
    total_CURE = bittrex.get_balance('CURE')['result']['Available']
    total_ZEC = bittrex.get_balance('ZEC')['result']['Available']

    temp_dict = {"USD": total_USD, "BTC": total_BTC, "ETH": total_ETH, "CURE": total_CURE, "ZEC": total_ZEC}
    return(temp_dict)
def merge_two_dicts(x, y):
    """Given two dicts, merge them into a new dict as a shallow copy."""
    z = x.copy()
    z.update(y)
    return z
def btc_cold_stor_bal(wallet):
    #takes a list of addresses and sums the values of all addresses and returns the total

    running = 0
    for n in wallet:
        temp = bc.balance(n)
        running = running + temp

    return(running/(1e8))
def eth_cold_stor_bal(wallet):
    #takes a list of addresses and sums the values of all addresses and returns the total

    running = 0
    for n in wallet:
        temp = ec.balance(n)
        running = running + temp

    return(running/(1e18))

#MAIN CODE

for x in range(1, 1000):
    TimeAndDate = datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')
    mrk_vals = current_market_values()
    bals = current_balances()
    month_profit = nano.profitability()
    time_cur = {"time": TimeAndDate, "monthly_profit": month_profit}
    combo = merge_two_dicts(mrk_vals, bals)
    full_track = [merge_two_dicts(combo, time_cur)]

    #adding to CSV
    field_names = ['time', 'USD', 'ZEC', 'CURE', 'ETH', 'BTC', 'gemBTC_USD', 'gemBTC_ETH','gemETH_USD', 'bitBTC_ETH', 'bitBTC_CURE', 'poloBTC_ETH', 'monthly_profit']

    with open('history.csv', 'a') as file:
        dict_writer = csv.DictWriter(file, fieldnames = field_names, extrasaction='ignore', delimiter = ",")
        #dict_writer.writeheader()
        dict_writer.writerows(full_track)

    print('Data Saved at ' + full_track[0]['time'])
    print('   Projected Profit: $' + str(full_track[0]['monthly_profit']))
    current_valuation = float(full_track[0]['USD']) + float(full_track[0]['ETH'])*float(full_track[0]['gemETH_USD']) + float(full_track[0]['BTC'])*float(full_track[0]['gemBTC_USD'])
    print('   Current Valuation: $' + str(current_valuation))
    time.sleep(3600)

