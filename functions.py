import pandas as pd
import re
import requests
import sqlite3
from bs4 import BeautifulSoup
from sqlalchemy import create_engine

#############
# Constants
#############

# Shared column name
JP_NAME = 'japanese_name'

# Uma Musume data columns
UMA_ID = 'umamusume_id'
HEIGHT = 'height'
SPEED = 'speed_growth'
POWER = 'power_growth'
HAS_SPE_POW = 'has_speed_and_power'

# netkeiba data columns
NET_ID = 'netkeiba_id'
EN_NAME = 'english_name'
FOALED = 'foaled_date'
TRAINED = 'trained_at'
WEIGHT = 'average_race_weight'
WINS = 'wins'
STARTS = 'starts'
WIN_PCT = 'win_percent'

#############
# Uma Musume: Pretty Derby data preparation functions
#############

def get_uma(conn: str) -> pd.DataFrame:
    """Return a df containing character ID, name, height, speed growth 
    and power growth of characters contained in the file with SQLite URL conn.
    """

    url = create_engine(conn)
    query = '''SELECT chara_id, text, scale, talent_speed, talent_pow
    FROM card_data
    LEFT JOIN text_data
    ON chara_id = [index]
    AND category = 6
    JOIN chara_data
    ON chara_data.id = chara_id;
    '''
    return pd.read_sql_query(query, url)


def clean_uma(df: pd.DataFrame) -> None:
    """Return a cleaned version of df by perfoming the following tasks:
    - Rename columns of df to their respective English names.
    - Remove rows with duplicates in UMA_ID, 
    which refer to alternate versions of characters.
    - Add boolean columns HAS_SPE and HAS_POW indicating if the character has 
    positive speed or power growth, respectively.
    """

    df.rename(columns={'chara_id': UMA_ID, 'text': JP_NAME, 
                       'scale': HEIGHT, 'talent_speed': SPEED, 
                       'talent_pow': POWER}, inplace=True)
    df[HAS_SPE_POW] = (df[SPEED] > 0) & (df[POWER] > 0)
    df.drop_duplicates(subset=[UMA_ID], inplace=True)

#############
# netkeiba.com web scraping and preparation functions
#############

def fetch_soup(url: str) -> BeautifulSoup | None:
    """Return a BeautifulSoup object if url is successfully fetched,
    and None otherwise.
    """
    
    response = requests.get(url)
    if response.status_code == 200:
        return BeautifulSoup(response.text, 'html.parser')
    return None


def find_url(name: str) -> str:
    """Find the webpage that corresponds to the racehorse with name.
    """

    search_url = f'https://en.netkeiba.com/db/horse/horse_list.html?word=+{name}'
    soup = fetch_soup(search_url)
    if soup and soup.find('li', attrs={'class': 'fc'}):
        return soup.find('li', attrs={'class': 'fc'}).find_next().get('href')


def get_netikeiba(url: str) -> dict:
    """Return a dict containing the ID, Japanese name, English name, 
    Foaled date, Training facility, Wins, and Starts from url. 
    """ 

    soup = fetch_soup(url)
    if soup:
       horse_dict = {}
       horse_dict[NET_ID] = re.search(r'\d+\w*', url).group()
       horse_dict[JP_NAME] = soup.find(
           attrs={'class': 'Name'}).a.get_text().strip()
       horse_dict[EN_NAME] = soup.find(
           attrs={'class': 'Name'}).h1.get_text().strip()
       horse_dict[FOALED] = soup.find(
           string='Foaled').find_next().get_text().strip()
       if soup.find(string='Trainer').find_next().span:
            horse_dict[TRAINED] = soup.find(
                string='Trainer').find_next().span.get_text().strip()
       record = soup.find(string='Race Record').find_next().get_text().strip()
       horse_dict[WINS] = int(re.findall(r'\d+', record)[0])
       horse_dict[STARTS] = int(re.findall(r'\d+', record)[1])
       return horse_dict


def get_weight(horse: dict) -> None: 
    """Calculate the average race weight of horse based on 
    the corresponding race records page on netkeiba.com, then store it in horse
    under the key WEIGHT.
    """
    
    record_url = 'https://en.netkeiba.com/db/horse/result/' + str(horse[NET_ID])
    soup = fetch_soup(record_url)
    if soup and not soup.find(attrs={'class': 'label Classic'}):
        weights = []
        for row in soup.find(
            attrs={'class': 'table_slide_body'}).tbody.find_all('tr'):
            weight = re.search(
                r'\d+', row.find_all('td')[18].get_text().strip())
            if weight:
                weights.append(int(weight.group()))
        avg_weight = sum(weights) / len(weights)
        horse[WEIGHT] = avg_weight     


def build_netkeiba(names: pd.Series) -> pd.DataFrame:
    """Return a DataFrame containing data from netkeiba corresponding to names.
    """

    horses = []
    for name in names:
        url = find_url(name)
        horse = get_netikeiba(url)
        get_weight(horse)
        horses.append(horse)
    return pd.DataFrame(horses)


def clean_netkeiba(df: pd.DataFrame) -> None:
    """Clean df by peforming the following tasks:
    - Add a column named WIN_PCT to df consisting of 
    Wins divided by Starts, multiplied by 100.
    - Change the type of FOALED to datetime.
    """
    
    df[WIN_PCT] = df[WINS] / df[STARTS] * 100
    df[FOALED] = pd.to_datetime(df[FOALED], format='%d %b %Y')

if __name__ == "__main__":
    pass
    