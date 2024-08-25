import os
import MetaTrader5 as mt
import pandas as pd
import plotly.express as px
from datetime import datetime
from datetime import timedelta
from openai import OpenAI
import openai
from dotenv import load_dotenv

load_dotenv()
client = OpenAI()
login = os.getenv("LOGIN")
password = os.getenv("PASSWORD")
server = os.getenv("SERVER")
system_prompt =  """
           # Role
            Act as a Trading Advisor, an expert in analyzing financial market data to provide precise trading recommendations including entry points, stop loss, and take profit levels based on advanced trading strategies and risk management principles.

            # Task
            Analyze the OHLC (Open, High, Low, Close) data and tick data from MetaTrader5 charts to determine the optimal trading strategy for the given scenario. Provide clear, actionable trading signals that include whether to BUY or SELL, along with specific ENTRY, SL (Stop Loss), and TP (Take Profit) values. Utilize the provided PDF document with trading strategies to inform your analysis and recommendations.

            ## Specifics
            - The first user prompt that the user gives you is actually the ohlc data formatted as json data. You know what to do with it. Respect the example format of responding
            - Don;t include anything else besides Entry, SL, TP
            - Focus solely on the analysis of provided chart data to offer trading advice.
            - Use the trading strategies outlined in the provided PDF document as the basis for your analysis.
            - Be precise and concise in your recommendations, offering only the essential information needed for trading decisions: BUY or SELL, ENTRY, SL, and TP.
            - Request follow-up screenshots if necessary for a more detailed analysis.

            ##Strategy
###Analysis Approach:
-Trend Identification: Use D1 to determine the overall trend (bullish, bearish, or sideways).
-Intermediate Trends: Use H1 to see how the current price is moving within the daily trend.
-Precise Entry Point: Use M15 to fine-tune your entry, looking for price action signals like breakouts, pullbacks, or reversals.
### Position Identification:
-Confluence: Ensure that the entry on the M15 aligns with the trend observed on H1 and D1.
-Risk Management: Set stop losses based on the recent low/high on M15 or H1, ensuring a favorable risk-to-reward ratio.
-Best Position Example:If the D1 chart shows an overall uptrend, and the H1 chart indicates a recent pullback to a strong support level, you would look for a bullish candlestick pattern on the M15 chart to enter a long position.

            # Tools
            1. *Knowledge Base*: A PDF document titled "My Learnings - Profitable Trading Strategies" available at https://acledasecurities.com.kh/as/assets/pdf_zip/My%20Learnings%20-%20Profitable%20Trading%20Strategies.pdf, which outlines various trading strategies. This should be consulted to inform your trading advice.
            2. *MetaTrader5*: A platform for trading that provides the OHLC you will analyze. While you won't interact with MetaTrader5 directly in this context, your advice will be based on data that could be derived from this tool.
            3. **Number and probability theory"": You will also use every maths aspect you can apply to maximize profits and minimize losses.
            # Examples
            Input: Data

            Output:
            BUY
            Entry: 161.818
            SL: 161.600
            TP: 161.850

            Input: Data

            Output:
            SELL
            Entry: 161.720
            SL: 161.900
            TP: 161.550

            # Notes
            - Your responses should be straightforward and to the point, mirroring the precision required in trading decisions.
            - Avoid any form of conversational or unnecessary commentary outside of the trading signals and required values (BUY/SELL, ENTRY, SL, TP).
            - Act with the efficiency and accuracy of a well-calibrated trading robot, focusing solely on delivering high-quality trading advice based on the provided data and strategies.
            - When in need of more detailed data for analysis, do not hesitate to request follow-up data, but ensure that your primary output remains focused on trading signals and related values.
            - Best Position Example:If the D1 chart shows an overall uptrend, and the H1 chart indicates a recent pullback to a strong support level, you would look for a bullish candlestick pattern on the M15 chart to enter a long position.            """

def create_order(order_type, entry, sl, tp, symb):
  if order_type == "BUY":
    request = {"action": mt.TRADE_ACTION_DEAL,
                "symbol": symb,
                "volume": 1.0, # FLOAT
                "type": mt.ORDER_TYPE_BUY,
                "price": entry, # mt.symbol_info_tick(symb).ask
                "sl": sl, # FLOAT
                "tp": tp, # FLOAT
                "magic": 234000, # INTERGER
                "comment": "python script open",
                "type_time": mt.ORDER_TIME_GTC,
                "type_filling": mt.ORDER_FILLING_IOC}
  elif order_type == "SELL":
    request = {"action": mt.TRADE_ACTION_DEAL,
                "symbol": symb,
                "volume": 1.0, # FLOAT
                "type": mt.ORDER_TYPE_SELL,
                "price": entry, # mt.symbol_info_tick(symb).ask
                "sl": sl, # FLOAT
                "tp": tp, # FLOAT
                "magic": 234000, # INTERGER
                "comment": "python script open",
                "type_time": mt.ORDER_TIME_GTC,
                "type_filling": mt.ORDER_FILLING_IOC}      
  return request

def Continue():
   i = input("Do you want to continue? 1 - Yes, 0 - No\n")
   if i == '1':
      return True
   else:
      return False
   
def main():
  # Initialize mt
  mt.initialize()
  mt.login(login, password, server)

  order_type = "none"
  entry = "none"
  sl = "none"
  tp = "none"

  working = True
  while(working == True):
    symb = input("Please provide the symbol you want to trade: ")
    
    raw_data = mt.copy_rates_from(symb, mt.TIMEFRAME_M15, datetime.now() - timedelta(days=1), 25)
    ohlc_data = pd.DataFrame(raw_data)
    #tick_data = pd.DataFrame(mt.copy_ticks_range(symb, datetime(2024, 8, 16), datetime.now(), mt.COPY_TICKS_ALL))

    ohlc_data_json = ohlc_data.to_json(orient='records')
    #tick_data_json = tick_data.to_json(orient='records')

    prompt = ohlc_data_json
    #print(prompt)
  
    

    response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
      {"role": "system", "content": system_prompt},
      {"role": "user", "content": prompt}
    ]
    )
    raspuns = response.choices[0].message.content
    lines = raspuns.splitlines()

    for line in lines:
      if line.startswith("BUY") or line.startswith("SELL"):
        order_type = line.strip()
      else: 
        text = line.split(':')
        if text[0] == "Entry":
            entry = text[1].strip()
        elif text[0] == "SL":
            sl = text[1].strip()
        elif text[0] == "TP":
            tp = text[1].strip()

    if(entry == 'none' or sl == 'none' or tp == 'none'):
      print("Chatgpt is funny, asks for data/ doesn't receive data")


    req = create_order(order_type, float(entry), float(sl), float(tp), symb)
    order = mt.order_send(req)
    
    print(raspuns, "\n")
    print(order, "\n")

    working = Continue()
  
  mt.shutdown()

if __name__ == "__main__":
  main()