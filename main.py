import cbpro, time, ssl, csv
import tkinter as tk
import socket, sys

class MyWebsocketClient(cbpro.WebsocketClient):
    def on_open(self):
        self.products = ["ETH-USD", "BTC-USD"]
        self.url = "wss://ws-feed.pro.coinbase.com"

    def on_message(self, msg):
        time.sleep(4)

    def on_close(self):
        print("-- Goodbye! --")


# ------- Define Global Variables -------- #
LARGE_FONT = ("Verdana", 12)
SMALL_FONT = ("Verdana", 8)
MID_FONT = ("Verdana", 10)

WS_URL = "wss://ws-feed-public.sandbox.pro.coinbase.com"        # SANDBOX
# WS_URL = "wss://ws-feed.pro.coinbase.com"
API_URL = "https://api-public.sandbox.pro.coinbase.com"  # SANDBOX
# API_URL = "https://api.pro.coinbase.com"
API_KEY = ""  # SANDBOX
# API_KEY = ""
API_SECRET = ""  # SANDBOX
# API_SECRET = ""
API_PASS = ""
auth_client = cbpro.AuthenticatedClient(API_KEY, API_SECRET, API_PASS, api_url=API_URL)
ws_client = MyWebsocketClient()
public_client = cbpro.PublicClient()
client = [auth_client, public_client]
mode = 1           # set to 0 for real run, -1 or 1 for test run
with open("log.txt", "w+") as log:
    log_orders = open("order_log.txt", "a+")
    log_prices = open("price_log.txt", "a+")
    log_learning = open("learning_variables.txt", "r")
    quote_track = {'ETH-USD': [], 'BTC-USD': [], 'LTC-USD': []}
    delay = 0       # used to run select parts every "delay" iterations
    stats = client[mode].get_product_24hr_stats('ETH-USD')
    current_product = 'ETH-USD'
    trigger_walls_on = True
    all_triggers_off = False
    account_ids = {"USD": 0, "BTC": 0, "ETH": 0, "LTC": 0}
    # --------------------------------------- #
    
    # ------- Possibly Future Machine Learning Variables ------- #
    lin = []
    for line in log_learning.readlines():
        lin.append(line)
    
    wall_criteria = float(lin[0][(lin[0].index('=') + 2):])
    master_trigger_sensitivity = float(lin[1][(lin[1].index('=') + 2):])
    trigger_sensitivity_list = lin[2][(lin[2].index('=') + 2):]
    success_wedge = float(lin[3][(lin[3].index('=') + 2):])
    success_possible_breakout = float(lin[4][(lin[4].index('=') + 2):])
    success_breakout = float(lin[5][(lin[5].index('=') + 2):])
    # many to be added
    # ------------------------------------------ #
    
    BTC_limit_entry_box = -1
    ETH_limit_entry_box = -1
    LTC_limit_entry_box = -1
    
    
    def main():
        global account_ids
        if mode == 0:
            accounts = client[mode].get_accounts()  # returns an array of account dictionaries
            account_ids['USD'] = extract_account_id(accounts, "USD")
            account_ids['BTC'] = extract_account_id(accounts, "BTC")
            account_ids['ETH'] = extract_account_id(accounts, "ETH")
            account_ids['LTC'] = extract_account_id(accounts, "LTC")

        # -------------------------- CSV for Testing -------------------------- #
        #with open('data.csv', 'w', newline='\n') as csvfile:
        #    writer = csv.writer(csvfile, delimiter=',', quotechar="'", quoting=csv.QUOTE_MINIMAL)
        #    writer.writerow(['Time', 'Price', 'Bid Wall', 'Bid Wall Scale', 'Ask Wall', 'Ask Wall Scale',
        #                     'Total Bid/Ask Ratio', '5min Volume', '15min Volume', '24h Volume'])
        # --------------------------------------------------------------------- #

        gui_loop()

        # print(accounts, "\n")
        # account_id = extract_account_id(accounts)
        # print(auth_client.get_account(account_id))
        # order_book = auth_client.get_product_order_book('BTC-USD', level=2)
        # print(order_book)
    
    #   ws_client.start()
    #   ws_client.close()
    #   ws_order_book.close()
    
    
    def gui_loop():
        global BTC_limit_entry_box, ETH_limit_entry_box, LTC_limit_entry_box
        root = tk.Tk()
        root.geometry('1150x900')
        root.title('Crypto-Trader by Kendall Ayers')

        container = tk.Frame(root)
        container.configure(background='black')
        container.pack(side="top", fill="both", expand=True)
        rows = cols = 0
        while rows < 30:
            container.rowconfigure(rows, weight=1)
            rows += 1
        while cols < 16:
            container.columnconfigure(cols, weight=1)
            cols += 1

        label = tk.Label(container, text="Crypto-Trader", font=LARGE_FONT, background="white")
        label.grid(row=1, column=5, sticky="n")

        BTC_buy_label = tk.Label(container, text="Buy BTC", font=MID_FONT, bg="black", fg="white")
        BTC_buy_label.grid(row=3, column=2)
        BTC_buy_label.bind('<Button-1>', place_BTC_buy)

        ETH_buy_label = tk.Label(container, text="Buy ETH", font=MID_FONT, bg="black", fg="white")
        ETH_buy_label.grid(row=5, column=2)
        ETH_buy_label.bind('<Button-1>', place_ETH_buy)

        LTC_buy_label = tk.Label(container, text="Buy LTC", font=MID_FONT, bg="black", fg="white")
        LTC_buy_label.grid(row=7, column=2)
        LTC_buy_label.bind('<Button-1>', place_LTC_buy)

        BTC_buy_fees_label = tk.Label(container, text="Fees Buy BTC", font=MID_FONT, bg="black", fg="white")
        BTC_buy_fees_label.grid(row=3, column=5)
        BTC_buy_fees_label.bind('<Button-1>', place_BTC_fees_buy)

        ETH_buy_fees_label = tk.Label(container, text="Fees Buy ETH", font=MID_FONT, bg="black", fg="white")
        ETH_buy_fees_label.grid(row=5, column=5)
        ETH_buy_fees_label.bind('<Button-1>', place_ETH_fees_buy)

        LTC_buy_fees_label = tk.Label(container, text="Fees Buy LTC", font=MID_FONT, bg="black", fg="white")
        LTC_buy_fees_label.grid(row=7, column=5)
        LTC_buy_fees_label.bind('<Button-1>', place_LTC_fees_buy)

        BTC_sell_label = tk.Label(container, text="Sell BTC", font=MID_FONT, bg="black", fg="white")
        BTC_sell_label.grid(row=3, column=3)
        BTC_sell_label.bind('<Button-1>', place_BTC_sell)

        ETH_sell_label = tk.Label(container, text="Sell ETH", font=MID_FONT, bg="black", fg="white")
        ETH_sell_label.grid(row=5, column=3)
        ETH_sell_label.bind('<Button-1>', place_ETH_sell)

        LTC_sell_label = tk.Label(container, text="Sell LTC", font=MID_FONT, bg="black", fg="white")
        LTC_sell_label.grid(row=7, column=3)
        LTC_sell_label.bind('<Button-1>', place_LTC_sell)

        BTC_sell_fees_label = tk.Label(container, text="Fees Sell BTC", font=MID_FONT, bg="black", fg="white")
        BTC_sell_fees_label.grid(row=3, column=6)
        BTC_sell_fees_label.bind('<Button-1>', place_BTC_fees_sell)

        ETH_sell_fees_label = tk.Label(container, text="Fees Sell ETH", font=MID_FONT, bg="black", fg="white")
        ETH_sell_fees_label.grid(row=5, column=6)
        ETH_sell_fees_label.bind('<Button-1>', place_ETH_fees_sell)

        LTC_sell_fees_label = tk.Label(container, text="Fees Sell LTC", font=MID_FONT, bg="black", fg="white")
        LTC_sell_fees_label.grid(row=7, column=6)
        LTC_sell_fees_label.bind('<Button-1>', place_LTC_fees_sell)

        BTC_limit_entry_box = tk.Entry(container)
        BTC_limit_entry_box.grid(row=3, column=4)

        ETH_limit_entry_box = tk.Entry(container)
        ETH_limit_entry_box.grid(row=5, column=4)

        LTC_limit_entry_box = tk.Entry(container)
        LTC_limit_entry_box.grid(row=7, column=4)

        BTC_24 = tk.StringVar()
        ETH_24 = tk.StringVar()
        LTC_24 = tk.StringVar()
        BTC_6 = tk.StringVar()
        ETH_6 = tk.StringVar()
        LTC_6 = tk.StringVar()
        BTC_1 = tk.StringVar()
        ETH_1 = tk.StringVar()
        LTC_1 = tk.StringVar()
        BTC_15 = tk.StringVar()
        ETH_15 = tk.StringVar()
        LTC_15 = tk.StringVar()

        label = tk.Label(container, text="24hr", font=MID_FONT, background="white")
        label.grid(row=2, column=8, sticky="n")
        label = tk.Label(container, text="6hr", font=MID_FONT, background="white")
        label.grid(row=2, column=10, sticky="n")
        label = tk.Label(container, text="1hr", font=MID_FONT, background="white")
        label.grid(row=2, column=12, sticky="n")
        label = tk.Label(container, text="15min", font=MID_FONT, background="white")
        label.grid(row=2, column=14, sticky="n")

        BTC_24_label = tk.Label(container, textvariable=BTC_24, font=MID_FONT, background="white")
        BTC_24_label.grid(row=3, column=8, sticky="n")
        BTC_6_label = tk.Label(container, textvariable=BTC_6, font=MID_FONT, background="white")
        BTC_6_label.grid(row=3, column=10, sticky="n")
        BTC_1_label = tk.Label(container, textvariable=BTC_1, font=MID_FONT, background="white")
        BTC_1_label.grid(row=3, column=12, sticky="n")
        BTC_15_label = tk.Label(container, textvariable=BTC_15, font=MID_FONT, background="white")
        BTC_15_label.grid(row=3, column=14, sticky="n")

        ETH_24_label = tk.Label(container, textvariable=ETH_24, font=MID_FONT, background="white")
        ETH_24_label.grid(row=5, column=8, sticky="n")
        ETH_6_label = tk.Label(container, textvariable=ETH_6, font=MID_FONT, background="white")
        ETH_6_label.grid(row=5, column=10, sticky="n")
        ETH_1_label = tk.Label(container, textvariable=ETH_1, font=MID_FONT, background="white")
        ETH_1_label.grid(row=5, column=12, sticky="n")
        ETH_15_label = tk.Label(container, textvariable=ETH_15, font=MID_FONT, background="white")
        ETH_15_label.grid(row=5, column=14, sticky="n")

        LTC_24_label = tk.Label(container, textvariable=LTC_24, font=MID_FONT, background="white")
        LTC_24_label.grid(row=7, column=8, sticky="n")
        LTC_6_label = tk.Label(container, textvariable=LTC_6, font=MID_FONT, background="white")
        LTC_6_label.grid(row=7, column=10, sticky="n")
        LTC_1_label = tk.Label(container, textvariable=LTC_1, font=MID_FONT, background="white")
        LTC_1_label.grid(row=7, column=12, sticky="n")
        LTC_15_label = tk.Label(container, textvariable=LTC_15, font=MID_FONT, background="white")
        LTC_15_label.grid(row=7, column=14, sticky="n")

        try:
            while True:
                root.update_idletasks()
                root.update()
                order_book = client[mode].get_product_order_book('ETH-USD', level=2)
                process_order_book(order_book, 'ETH-USD')
                order_book = client[mode].get_product_order_book('BTC-USD', level=2)
                process_order_book(order_book, 'BTC-USD')
                order_book = client[mode].get_product_order_book('LTC-USD', level=2)
                process_order_book(order_book, 'LTC-USD')

                BTC_24.set(round(((quote_track['BTC-USD'][-1]['price'] - float(
                    client[mode].get_product_24hr_stats('BTC-USD')['open']))
                                        * 100) / float(client[mode].get_product_24hr_stats('BTC-USD')['open']), 3))
                if (BTC_24.get() != 'None') and float(BTC_24.get()) > 0:
                    BTC_24_label.config(bg='green')
                else:
                    BTC_24_label.config(bg='red')

                BTC_15.set(round(get_change(15, 'BTC-USD'), 3))
                if (BTC_15.get() != 'None') and float(BTC_15.get()) > 0:
                    BTC_15_label.config(bg='green')
                else:
                    BTC_15_label.config(bg='red')

                BTC_1.set(round(get_change(60, 'BTC-USD'), 3))
                if (BTC_1.get() != 'None') and float(BTC_1.get()) > 0:
                    BTC_1_label.config(bg='green')
                else:
                    BTC_1_label.config(bg='red')

                BTC_6.set(round(get_change(360, 'BTC-USD'), 3))
                if (BTC_6.get() != 'None') and float(BTC_6.get()) > 0:
                    BTC_6_label.config(bg='green')
                else:
                    BTC_6_label.config(bg='red')

                ETH_24.set(round((((quote_track['ETH-USD'][-1]['price'] - float(
                    client[mode].get_product_24hr_stats('ETH-USD')['open']))
                             * 100) / float(client[mode].get_product_24hr_stats('ETH-USD')['open'])), 3))
                if (ETH_24.get() != 'None') and float(ETH_24.get()) > 0:
                    ETH_24_label.config(bg='green')
                else:
                    ETH_24_label.config(bg='red')

                ETH_15.set(round(get_change(15, 'ETH-USD'), 3))
                if (ETH_15.get() != 'None') and float(ETH_15.get()) > 0:
                    ETH_15_label.config(bg='green')
                else:
                    ETH_15_label.config(bg='red')

                ETH_1.set(round(get_change(60, 'ETH-USD'), 3))
                if (ETH_1.get() != 'None') and float(ETH_1.get()) > 0:
                    ETH_1_label.config(bg='green')
                else:
                    ETH_1_label.config(bg='red')

                ETH_6.set(round(get_change(360, 'ETH-USD'), 3))
                if (ETH_6.get() != 'None') and float(ETH_6.get()) > 0:
                    ETH_6_label.config(bg='green')
                else:
                    ETH_6_label.config(bg='red')

                LTC_24.set(round((((quote_track['LTC-USD'][-1]['price'] - float(
                    client[mode].get_product_24hr_stats('LTC-USD')['open']))
                             * 100) / float(client[mode].get_product_24hr_stats('LTC-USD')['open'])), 3))
                if (LTC_24.get() != 'None') and float(LTC_24.get()) > 0:
                    LTC_24_label.config(bg='green')
                else:
                    LTC_24_label.config(bg='red')

                LTC_15.set(round(get_change(15, 'LTC-USD'), 3))
                if (LTC_15.get() != 'None') and float(LTC_15.get()) > 0:
                    LTC_15_label.config(bg='green')
                else:
                    LTC_15_label.config(bg='red')

                LTC_1.set(round(get_change(60, 'LTC-USD'), 3))
                if (LTC_1.get() != 'None') and float(LTC_1.get()) > 0:
                    LTC_1_label.config(bg='green')
                else:
                    LTC_1_label.config(bg='red')

                LTC_6.set(round(get_change(360, 'LTC-USD'), 3))
                if (LTC_6.get() != 'None') and float(LTC_6.get()) > 0:
                    LTC_6_label.config(bg='green')
                else:
                    LTC_6_label.config(bg='red')

        except Exception as e:
            print(e)
            root.destroy()
    
    
    def process_order_book(book, product):
        global quote_track
        current_bid = float(book.get('bids')[0][0])
        current_ask = float(book.get('asks')[0][0])
        current_price = current_bid
        current_bid_wall = find_bid_wall(book)  # walls are an array with [price, scale, total_book_quantity]
        current_ask_wall = find_ask_wall(book)  # where scale is amount / wall_criteria
        current_bid_to_ask_ratio = current_bid_wall[2] / current_ask_wall[2]
        current_time = time_machine()

        try:
            quote_dic = {'time': str(current_time), 'price': float(current_price), 'bid_wall': float(current_bid_wall[0]),
                         'bid_wall_scale': float(current_bid_wall[1]), 'ask_wall': float(current_ask_wall[0]),
                         'ask_wall_scale': float(current_ask_wall[1]), 'bid_ask_ratio': float(current_bid_to_ask_ratio),
                         }
        except ValueError as e:
            print("quote_dic could not be initialized: ", e)
        if len(quote_track['ETH-USD']) >= 1209600/3:         # one week of data at 2 requests/sec
            quote_track.pop(0)

        quote_track[product].append(quote_dic)

        # --------------------------- To CSV for sampling ---------------------------- #
        # with open('data.csv', 'a', newline='\n') as csvfile:
        #    writer = csv.writer(csvfile, delimiter=',', quotechar="'", quoting=csv.QUOTE_MINIMAL)
        #    writer.writerow([current_time, current_price, current_bid_wall[0], current_bid_wall[1], current_ask_wall[0],
        #                     current_ask_wall[1], current_bid_to_ask_ratio,
        #                     current_volume_5min, current_volume_15min, current_volume_24hr])
        # --------------------------------------------------------------------------- #
    
    
    def place_BTC_buy(event=None):
        client[mode].cancel_all(product='BTC-USD')
        if len(str(BTC_limit_entry_box.get())) > 1:
            price = float(BTC_limit_entry_box.get())
        else:
            price = quote_track['BTC-USD'][-1]['price']
        account = client[mode].get_account(account_ids['USD'])
        size = (account['balance'] - .1) / price
        client[mode].buy(price=price, size=size, product_id='BTC-USD', post_only=True)  # limit order to buy size ETH at $price
    
    
    def place_BTC_fees_buy(event=None):
        client[mode].cancel_all(product='BTC-USD')
        account = client[mode].get_account(account_ids['USD'])
        size = (account['balance'] - .1) / quote_track['BTC-USD'][-1]['price']
        client[mode].buy(type='market', size=size, product_id='BTC-USD', post_only=False)
    
    
    def place_ETH_buy(event=None):
        client[mode].cancel_all(product='ETH-USD')
        if len(str(ETH_limit_entry_box.get())) > 1:
            price = float(ETH_limit_entry_box.get())
        else:
            price = quote_track['ETH-USD'][-1]['price']
        account = client[mode].get_account(account_ids['USD'])
        size = (account['balance'] - .1) / price
        client[mode].buy(price=price, size=size, product_id='ETH-USD', post_only=True)
    
    
    def place_ETH_fees_buy(event=None):
        client[mode].cancel_all(product='ETH-USD')
        account = client[mode].get_account(account_ids['USD'])
        size = (account['balance'] - .1) / quote_track['ETH-USD'][-1]['price']
        client[mode].buy(type='market', size=size, product_id='ETH-USD', post_only=False)
    
    
    def place_LTC_buy(event=None):
        client[mode].cancel_all(product='LTC-USD')
        if len(str(LTC_limit_entry_box.get())) > 1:
            price = float(LTC_limit_entry_box.get())
        else:
            price = quote_track['LTC-USD'][-1]['price']
        account = client[mode].get_account(account_ids['USD'])
        size = (account['balance'] - .1) / price
        client[mode].buy(price=price, size=size, product_id='LTC-USD', post_only=True)
    
    
    def place_LTC_fees_buy(event=None):
        client[mode].cancel_all(product='LTC-USD')
        account = client[mode].get_account(account_ids['USD'])
        size = (account['balance'] - .1) / quote_track['LTC-USD'][-1]['price']
        client[mode].buy(type='market', size=size, product_id='LTC-USD', post_only=False)
    
    
    def place_BTC_sell(event=None):
        client[mode].cancel_all(product='BTC-USD')
        if len(str(BTC_limit_entry_box.get())) > 1:
            price = float(BTC_limit_entry_box.get())
        else:
            price = quote_track['BTC-USD'][-1]['price'] + .01
        account = client[mode].get_account(account_ids['BTC'])
        size = account['balance']
        client[mode].sell(price=price, size=size, product_id='BTC-USD', post_only=True)
    
    
    def place_BTC_fees_sell(event=None):
        client[mode].cancel_all(product='BTC-USD')
        account = client[mode].get_account(account_ids['BTC'])
        size = account['balance']
        client[mode].sell(type='market', size=size, product_id='BTC-USD', post_only=False)
    
    
    def place_ETH_sell(event=None):
        client[mode].cancel_all(product='ETH-USD')
        if len(str(ETH_limit_entry_box.get())) > 1:
            price = float(ETH_limit_entry_box.get())
        else:
            price = quote_track['ETH-USD'][-1]['price'] + .01
        account = client[mode].get_account(account_ids['ETH'])
        size = account['balance']
        client[mode].sell(price=price, size=size, product_id='ETH-USD', post_only=True)
    
    
    def place_ETH_fees_sell(event=None):
        client[mode].cancel_all(product='ETH-USD')
        account = client[mode].get_account(account_ids['ETH'])
        size = account['balance']
        client[mode].sell(type='market', size=size, product_id='ETH-USD', post_only=False)
    
    
    def place_LTC_sell(event=None):
        client[mode].cancel_all(product='LTC-USD')
        if len(str(LTC_limit_entry_box.get())) > 1:
            price = float(LTC_limit_entry_box.get())
        else:
            price = quote_track['LTC-USD'][-1]['price'] + .01
        account = client[mode].get_account(account_ids['LTC'])
        size = account['balance']
        client[mode].sell(price=price, size=size, product_id='LTC-USD', post_only=True)
    
    
    def place_LTC_fees_sell(event=None):
        client[mode].cancel_all(product='LTC-USD')
        account = client[mode].get_account(account_ids['LTC'])
        size = account['balance']
        client[mode].sell(type='market', size=size, product_id='LTC-USD', post_only=False)
    
    
    def extract_account_id(accounts, product):
        for account in accounts:
            if account.get('currency') == product:
                return account.get('id')
    
    
    def sell_all():
        pass
    
    
    def fail_safe(product):
        client[mode].cancel_all(product=product)
    
    
    def find_bid_wall(book):
        scale = 0
        total_book_quantity = 0
        highest_quantity_index = 0
        previous_highest_quantity = 0
        bids = book.get('bids')
        for index, bid in enumerate(bids):
            if float(bid[1]) > previous_highest_quantity:
                highest_quantity_index = index
                previous_highest_quantity = float(bid[1])
            total_book_quantity += float(bid[1])
        scale += float(bids[highest_quantity_index][1]) / wall_criteria
        if highest_quantity_index != 0:
            scale += float(bids[highest_quantity_index-1][1]) / wall_criteria
        if highest_quantity_index != len(book.get('bids')) - 1:
            scale += float(bids[highest_quantity_index+1][1]) / wall_criteria
        return [float(bids[highest_quantity_index][0]), scale, total_book_quantity]
    
    
    def find_ask_wall(book):
        scale = 0
        total_book_quantity = 0
        highest_quantity_index = 0
        previous_highest_quantity = 0
        asks = book.get('asks')
        for index, ask in enumerate(asks):
            if float(ask[1]) > previous_highest_quantity:
                highest_quantity_index = index
                previous_highest_quantity = float(ask[1])
            total_book_quantity += float(ask[1])
        scale += float(asks[highest_quantity_index][1]) / wall_criteria
        if highest_quantity_index != 0:
            scale += float(asks[highest_quantity_index - 1][1]) / wall_criteria
        if highest_quantity_index != len(book.get('bids')) - 1:
            scale += float(asks[highest_quantity_index + 1][1]) / wall_criteria
        return [float(asks[highest_quantity_index][0]), scale, total_book_quantity]
    
    
    
    # Triggers to detect a pattern and make an automated trade TODO
    def trigger_wedge():
        return
    
    
    def trigger_possible_breakout():
        return
    
    
    def trigger_breakout():
        return
    
    
    def trigger_something():
        return
    
    
    # Returns a correctly formatted date at a given amount of time in the past
    def time_machine(years=0, months=0, days=0, hours=0, minutes=0, seconds=0, direction='backwards'):
        current_time = client[mode].get_time().get('iso')
        i = 0
        if direction == 'backwards':
            # ------------ Seconds ---------- #
            index = current_time.index('.')
            num = current_time[index-2:index]
            if int(num) - seconds <= 0:
                minutes += 1
                seconds = 60 + (int(num) - seconds)
            else:
                seconds = (int(num) - seconds)
            current_time = current_time[0:index-2] + current_time[index:]
            if seconds < 10:
                current_time = current_time[0:index - 2] + '0' + str(seconds) + current_time[index-2:]
            else:
                current_time = current_time[0:index - 2] + str(seconds) + current_time[index-2:]

            # ------------ Minutes ------------ #
            index = current_time.index(':')
            num = current_time[index+1:index+3]
            if int(num) - minutes <= 0:
                hours += 1
                minutes = 60 + (int(num) - minutes)
            else:
                minutes = (int(num) - minutes)
            current_time = current_time[0:index+1] + current_time[index+3:]
            if minutes < 10:
                current_time = current_time[0:index + 1] + '0' + str(minutes) + current_time[index+1:]
            else:
                current_time = current_time[0:index + 1] + str(minutes) + current_time[index+1:]

            # ------------ Hours ------------- #
            index = current_time.index(':')
            num = current_time[index - 2:index]
            if int(num) - hours < 0:
                days += 1
                hours = 24 + (int(num) - hours)
            else:
                hours = (int(num) - hours)
            current_time = current_time[0:index - 2] + current_time[index:]
            if hours < 10:
                current_time = current_time[0:index - 2] + '0' + str(hours) + current_time[index-2:]
            else:
                current_time = current_time[0:index - 2] + str(hours) + current_time[index-2:]

            # ------------- Days ------------- #
            index = current_time.index('T')
            num = current_time[index - 2:index]
            if int(num) - days <= 0:
                months += 1
                days = 30 + (int(num) - days)
            else:
                days = (int(num) - days)
            current_time = current_time[0:index - 2] + current_time[index:]
            if days < 10:
                current_time = current_time[0:index - 2] + '0' + str(days) + current_time[index-2:]
            else:
                current_time = current_time[0:index - 2] + str(days) + current_time[index-2:]

            # ------------ Months ------------ #
            index = current_time.index('-')
            num = current_time[index+1:index+3]
            if int(num) - months <= 0:
                years += 1
                months = 12 + (int(num) - months)
            else:
                months = (int(num) - months)
            current_time = current_time[0:index + 1] + current_time[index + 3:]
            if months < 10:
                current_time = current_time[0:index+1] + '0' + str(months) + current_time[index+1:]
            else:
                current_time = current_time[0:index+1] + str(months) + current_time[index+1:]

            # ----------- Years ------------- #
            index = current_time.index('-')
            num = current_time[index - 4:index]
            if int(num) - years <= 0:
                raise Exception
            else:
                years = (int(num) - years)
                current_time = current_time[0:index - 4] + current_time[index:]
            if years < 1000:
                current_time = current_time[0:index - 4] + '0' + str(years) + current_time[index-4:]
            elif years < 100:
                current_time = current_time[0:index - 4] + '00' + str(years) + current_time[index-4:]
            elif years < 10:
                current_time = current_time[0:index - 4] + '000' + str(years) + current_time[index-4:]
            else:
                current_time = current_time[0:index - 4] + str(years) + current_time[index-4:]
        else:
            print("Time travel to the future is unavailable at this time!")
        return current_time
    
    
    def get_change(mins, product):
        try:
            return (((quote_track[product][-1]['price'] - float(client[mode].get_product_historic_rates(product,
                                        time_machine(minutes=mins),time_machine(), (mins*60) - 1)[1][3])) * 100) /
                                        float(client[mode].get_product_historic_rates(product,
                                        time_machine(minutes=mins),time_machine(), (mins*60) - 1)[1][3]))
        except:
            return -1.000
    
    
    if __name__ == "__main__":
        main()
