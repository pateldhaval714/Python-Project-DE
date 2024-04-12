import pandas as pd 
import numpy as np 
import requests
import sqlite3
from bs4 import BeautifulSoup
from datetime import datetime

def log_progress(msg):
    timeformat = '%Y-%h-%d-%H:%M:%S'
    now = datetime.now()
    timestamp = now.strftime(timeformat)

    with open(logfile, 'a') as f:
        f.write(timestamp + ' : ' + msg + '\n')

def extract(url, get_market_capitalization_table):
    df = pd.DataFrame(columns = get_market_capitalization_table)

    page = requests.get(url).text
    data = BeautifulSoup(page, 'html.parser')

    tables = data.find_all('tbody')[0]
    rows = tables.find_all('tr')

    for row in rows:
        col = row.find_all('td')
        if len(col) != 0:
            parse_data = col[1].find_all('a')[1]
            if parse_data is not None:
                data_dict = {
                    'Name': parse_data.contents[0],
                    'MC_USD_Billion': col[2].contents[0]
                }
                df1 = pd.DataFrame(data_dict, index = [0])
                df = pd.concat([df, df1], ignore_index = True)
    USD_lst = list(df['MC_USD_Billion'])
    USD_lst = [float(''.join(x.split('\n'))) for x in USD_lst]
    df['MC_USD_Billion'] = USD_lst
    return df

def transform(df, exchange_rate_path):
    cf = pd.read_csv(exchange_rate_path)

    dict = cf.set_index('Currency').to_dict()['Rate']

    df['MC_GBP_Billion'] = [np.round(x * dict['GBP'],2) for x in df['MC_USD_Billion']]
    df['MC_INR_Billion'] = [np.round(x * dict['INR'],2) for x in df['MC_USD_Billion']]
    df['MC_EUR_Billion'] = [np.round(x * dict['EUR'],2) for x in df['MC_USD_Billion']]
    
    return df

def load_to_csv(df, output_path):
    df.to_csv(output_path)

def load_to_db(df, sql_connection, table_name):
    df.to_sql(table_name, sql_connection, if_exists = 'replace', index = False)

def run_query(query_statements, sql_connection):
    for query in query_statements:
        print(query)
        print(pd.read_sql(query, sql_connection), '\n')


url = 'https://web.archive.org/web/20230908091635/https://en.wikipedia.org/wiki/List_of_largest_banks'
exchange_rate_path = 'exchange_rate.csv'

get_market_capitalization_table = ['Name', 'MC_USD_Billion']
db_name = 'Banks.db'
table_name = 'Largest_banks'
conn = sqlite3.connect(db_name)
query_statements = [
        'SELECT * FROM Largest_banks',
        'SELECT AVG(MC_GBP_Billion) FROM Largest_banks',
        'SELECT Name from Largest_banks LIMIT 5'
    ]

logfile = 'code_log.txt'
output_csv_path = 'Largest_banks_data.csv'

log_progress('Preliminaries complete. Initiating ETL process.')

df = extract(url, get_market_capitalization_table)
log_progress('Data extraction complete. Initiating Transformation process.')


df = transform(df, exchange_rate_path)
log_progress('Data transformation complete. Initiating loading process.')

load_to_csv(df, output_csv_path)
log_progress('Data saved to CSV file.')

log_progress('SQL Connection initiated.')


load_to_db(df, conn, table_name)
log_progress('Data loaded to Database as table. Running the query.')

run_query(query_statements, conn)
conn.close()
log_progress('Process Complete.')
