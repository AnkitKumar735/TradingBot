#lumibot - easy algo trading framework
#alpaca trade api python - get news and place to trades broker 
#torch - pytorch framework for using AI/Ml
#transformers - load up finance deep learning model

from lumibot.brokers import Alpaca
from lumibot.backtesting import YahooDataBacktesting
from lumibot.strategies.strategy import Strategy
from lumibot.traders import Trader
from datetime import datetime , timedelta
from alpaca_trade_api import REST
from timedelta import Timedelta  #to calculate difference between time and days
from finbert_utils import estimate_sentiment

API_KEY = "PKXI75W7Z1SNYNSA0KKX"
API_SECRET = "ZCJJ1LORs4I8mzqGhkItbNIhm1h71wozK02JGH2e"
BASE_URL = "https://paper-api.alpaca.markets/v2"

#making a dictionary to pass through alpaca broker
ALPACA_CONFIG = {
    "API_KEY" : "PKXI75W7Z1SNYNSA0KKX",
    "API_SECRET" : "ZCJJ1LORs4I8mzqGhkItbNIhm1h71wozK02JGH2e",
    "PAPER": True #for not involving real cash
}


class MLTrader(Strategy):
    def initialize(self,symbol:str="SPY", cash_at_risk:float=.5): #it will run once
        self.symbol = symbol
        self.sleeptime = "24H" #how frequently we gonna trade
        self.last_trade = None 
        self.cash_at_risk = cash_at_risk
        self.api = REST(base_url=BASE_URL,key_id=API_KEY,secret_key=API_SECRET)

    def position_sizing(self):
        cash = self.get_cash() #for dynamic number of stocks
        last_price = self.get_last_price(self.symbol)
        quantity = float(cash * self.cash_at_risk / last_price)
        return cash , last_price,quantity
    
    def get_dates(self):
        today = self.get_datetime()
        three_days_prior = today - Timedelta(days=3) #start day prior to trading day
        return today.strftime('%Y-%m-%d'), three_days_prior.strftime('%Y-%m-%d')

    #calling news to get api
    def get_sentiment(self):
        today, three_days_prior = self.get_dates()  
        news = self.api.get_news(symbol=self.symbol,
                                 start=three_days_prior,
                                 end=today)
        
        news = [event.__dict__["_raw"]["headline"] for event in news] #formatting our jumbled news
        probability, sentiment = estimate_sentiment(news)
        return probability, sentiment

    def on_trading_iteration(self): #every time new data is fetched
        cash , last_price, quantity = self.position_sizing()
        probability, sentiment = self.get_sentiment()
        
        if cash > last_price: #we not buy if we do not have cash
            if sentiment == "positive" and probability > 0.999:   #for using ml taking trade decisions
                if self.last_trade == "sell":
                    self.sell_all()
                order = self.create_order(
                    self.symbol,
                    quantity, #number of stocks u buy
                    "buy",
                    type="bracket",
                    take_profit_price = last_price*1.20,
                    stop_loss_price = last_price*0.95
                )
                self.submit_order(order)
                self.last_trade = "buy"
            elif sentiment == "negative" and probability > 0.999:   #for using ml taking trade decisions
                if self.last_trade == "buy":
                    self.sell_all()
                order = self.create_order(
                    self.symbol,
                    quantity, #number of stocks u buy
                    "sell",
                    type="bracket",
                    take_profit_price = last_price*0.8,
                    stop_loss_price = last_price*1.03
                )
                self.submit_order(order)
                self.last_trade = "sell"


start_date = datetime(2020,1,1)
end_date = datetime(2024,2,1)

broker = Alpaca(ALPACA_CONFIG)

strategy = MLTrader(name = 'mlstrat', broker = broker,
                    parameters={"symbol":"SPY",
                                "cash_at_risk":.5})
strategy.backtest(
    YahooDataBacktesting,
    start_date,
    end_date,
    parameters={"symbol":"SPY", "cash_at_risk":.5} #higher the value riskier the bot
) 