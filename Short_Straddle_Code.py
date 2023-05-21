#importing important modules
import logging
from datetime import datetime
import time

from dateutil.relativedelta import relativedelta, TH
from kiteconnect import KiteConnect


variables = {}
with open('Input_File.txt', 'r') as f:
    lines = f.readlines()



for line in lines:
    variable, value = line.strip().split('=')
    variables[variable] = value

key = variables['key']
secret = variables['secret']
req_tkn = variables['req_tkn']
access_token = variables['access_token']

#Initialize the KiteConnect to access methods and endpoints provided by KiteConnect API
kite = KiteConnect(api_key=key)

#specify entry time and exit time in a separate variable
entry_time = "09:30:00"
exit_time = "15:15:00"
time_str = datetime.now()
now = time_str.strftime("%H:%M:%S")


#This function creates a new instance of the KiteConnect API client, sets the access token, and returns the client object.
def get_kite():
    kiteObj = KiteConnect(api_key=key)
    kiteObj.set_access_token(access_token)
    return kiteObj

kite = get_kite()
instrumentsList = None


#function to get current_market_price
def getCMP(tradingSymbol):
    quote = kite.quote(tradingSymbol)
    if quote:
        return quote[tradingSymbol]['last_price']
    else:
        return 0

#function to get symbols of instrument you want to buy/sell
def get_symbols(expiry, name, strike, ins_type):
    global instrumentsList

    if instrumentsList is None:
        instrumentsList = kite.instruments('NFO')

    lst_b = [num for num in instrumentsList if num['expiry'] == expiry and num['strike'] == strike
             and num['instrument_type'] == ins_type and num['name'] == name]
    return lst_b[0]['tradingsymbol']

#function to place order in kite
def place_order(tradingSymbol, price, qty, direction, exchangeType, product, orderType, triggerPrice=None):
    try:
        orderId = kite.place_order(
            variety=kite.VARIETY_REGULAR,
            exchange=exchangeType,
            tradingsymbol=tradingSymbol,
            transaction_type=direction,
            quantity=qty,
            price=price,
            product=product,
            order_type=orderType,
            trigger_price=triggerPrice)

        logging.info('Order placed successfully, orderId = %s', orderId)
        return orderId
    except Exception as e:
        logging.info('Order placement failed: %s', e.message)


if __name__ == '__main__':

    try:
        if (now >= entry_time and now <= exit_time)  and (time_str.weekday() not in [5, 6]):
            while True:
                # Find ATM Strike of Nifty
                # get current price of Nifty
                price = getCMP('NSE:NIFTY 50')
                if (price % 100 < 25):
                    atm_strike = (price // 100) * 100

                if (price % 100 >= 25 and price % 100 <= 75):
                    atm_strike = ((price // 100) * 100) + 50

                if (price % 100 > 75):
                    atm_strike = ((price // 100) + 1) * 100


                next_thursday_expiry = datetime.today() + relativedelta(weekday=TH(1))

                # store atm strikes call and put option in next thursday in a variables
                symbol_ce = get_symbols(next_thursday_expiry.date(), 'NIFTY', atm_strike, 'CE')
                symbol_pe = get_symbols(next_thursday_expiry.date(), 'NIFTY', atm_strike, 'PE')

                order_id_selling_ce = place_order(symbol_ce, 0, 50, kite.TRANSACTION_TYPE_BUY, KiteConnect.EXCHANGE_NFO,
                                                 KiteConnect.PRODUCT_MIS,
                                                 KiteConnect.ORDER_TYPE_MARKET,None)
                order_id_selling_pe = place_order(symbol_pe, 0, 50, kite.TRANSACTION_TYPE_BUY, KiteConnect.EXCHANGE_NFO,
                                                 KiteConnect.PRODUCT_MIS,
                                                 KiteConnect.ORDER_TYPE_MARKET,None)
                # Define tick size
                tick_size = 0.05

                # check orderbook
                orderbook = kite.orders()
                for order in orderbook:
                    if order['order_id'] == order_id_selling_ce:
                        # Calculate selling price of CE option
                        selling_price_ce = (order['average_price'] / 100) * 100
                        # Calculate stop-loss price of CE option
                        pre_stop_loss_ce = buying_price_ce * 1.25
                        stop_loss_ce = round(pre_stop_loss_ce,1)
                    elif order['order_id'] == order_id_selling_pe:
                        # Calculate selling price of PE option
                        selling_price_pe = (order['average_price'] / 100) * 100
                        # Calculate stop-loss price of PE option
                        pre_stop_loss_pe = selling_price_pe * 1.25
                        stop_loss_pe = round(pre_stop_loss_pe, 1)

                stop_loss_order_id_ce = place_order(symbol_ce, stop_loss_ce, 50, kite.TRANSACTION_TYPE_BUY, KiteConnect.EXCHANGE_NFO,
                                                 KiteConnect.PRODUCT_MIS,
                                                 KiteConnect.ORDER_TYPE_SL,stop_loss_ce)
                stop_loss_order_id_pe = place_order(symbol_pe, stop_loss_pe, 50, kite.TRANSACTION_TYPE_BUY, KiteConnect.EXCHANGE_NFO,
                                                 KiteConnect.PRODUCT_MIS,
                                                 KiteConnect.ORDER_TYPE_SL,stop_loss_pe)
                


                while True:
                    orders = kite.orders()
                    stop_loss_order_ce = next((order for order in orders if order['order_id'] == stop_loss_order_id_ce),
                                              None)
                    stop_loss_order_pe = next((order for order in orders if order['order_id'] == stop_loss_order_id_pe),
                                              None)
                    stop_loss_order_modified_pe = False
                    stop_loss_order_modified_ce = False
                    if stop_loss_order_ce and stop_loss_order_ce['status'] == 'COMPLETE':
                        # Modify stop loss order of put option to selling price
                        if not stop_loss_order_modified_pe:
                            modified_order_pe = kite.modify_order(variety=kite.VARIETY_REGULAR,
                                              order_id=stop_loss_order_id_pe,
                                              trigger_price=selling_price_pe,
                                              price=selling_price_pe)
                            time.sleep(2)
                        # Extract the order ID from the modified order dictionary
                            if isinstance(modified_order_pe, dict):
                                modified_order_id_pe = modified_order_pe.get("order_id")
                                stop_loss_order_modified_pe = True
                                while True:
                                    current_price_pe = getCMP(symbol_pe)
                                    orders = kite.orders()
                                    id_new_stop_loss_order_pe = next(
                                        (order for order in orders if order['order_id'] == modified_order_id_pe),
                                        None)
                                    if id_new_stop_loss_order_pe and id_new_stop_loss_order_pe['status'] == 'COMPLETE':
                                        break

                                    if current_price_pe <= selling_price_pe * 0.8 or now == exit_time:
                                        for order in orderbook:
                                            if order['order_id'] == order_id_selling_pe:
                                                place_order(symbol_pe, 0, 50, kite.TRANSACTION_TYPE_BUY,
                                                            KiteConnect.EXCHANGE_NFO,
                                                            KiteConnect.PRODUCT_MIS,
                                                            KiteConnect.ORDER_TYPE_MARKET, None)
                                        break
                    elif stop_loss_order_pe and stop_loss_order_pe['status'] == 'COMPLETE':
                        # Modify stop loss order of call option to selling price
                        if not stop_loss_order_modified_ce:
                            modified_order_ce = kite.modify_order(variety=kite.VARIETY_REGULAR,
                                              order_id=stop_loss_order_id_ce,
                                              trigger_price=selling_price_ce,
                                              price=selling_price_ce)
                            time.sleep(2)
                        # Extract the order ID from the modified order dictionary
                            if isinstance(modified_order_ce, dict):
                                modified_order_id_ce = modified_order_ce.get("order_id")
                                stop_loss_order_modified_ce = True
                                while True:
                                    current_price_ce = getCMP(symbol_ce)
                                    orders = kite.orders()
                                    id_new_stop_loss_order_ce = next(
                                        (order for order in orders if order['order_id'] == modified_order_id_ce),
                                        None)
                                    if id_new_stop_loss_order_ce and id_new_stop_loss_order_ce['status'] == 'COMPLETE':
                                        break
                                    if current_price_ce <= selling_price_ce * 0.08 or now == exit_time:
                                        for order in orderbook:
                                            if order['order_id'] == order_id_selling_ce:
                                                place_order(symbol_ce, 0, 50, kite.TRANSACTION_TYPE_BUY,
                                                            KiteConnect.EXCHANGE_NFO,
                                                            KiteConnect.PRODUCT_MIS,
                                                            KiteConnect.ORDER_TYPE_MARKET, None)
                                        break
        else:
            print("Market is closed right now.")
    except KiteConnect.exceptions.InputException as e:
        error_message = str(e)
        if "There is an error. Try to rerun the program again" in error_message and (now >= exit_time and now <= entry_time):
            print("Markets is closed right now.")
        else:
            logging.info('Order placement failed: %s', error_message)
