# from secrets import *
from secrets import *
import requests
import json
from bs4 import BeautifulSoup
from operator import itemgetter
from selenium import webdriver
import sqlite3
import csv

CACHE_FNAME = 'cache.json'
try:
    cache_file = open(CACHE_FNAME, 'r')
    cache_contents = cache_file.read()
    CACHE_DICTION = json.loads(cache_contents)
    cache_file.close()

# if there was no file, no worries. There will be soon!
except:
    CACHE_DICTION = {}

def get_unique_key(url):
  return url

def make_request_using_cache(url):
    unique_ident = get_unique_key(url)

    ## first, look in the cache to see if we already have this data
    if unique_ident in CACHE_DICTION:
        return CACHE_DICTION[unique_ident]
    ## if not, fetch the data afresh, add it to the cache,
    ## then write the cache to file
    else:
        print("Making a request for new data...")
        # Make the request and cache the new data
        wd = webdriver.Firefox()
        wd.get(url)
        CACHE_DICTION[unique_ident] = wd.page_source
        dumped_json_cache = json.dumps(CACHE_DICTION)
        fw = open(CACHE_FNAME,"w")
        fw.write(dumped_json_cache)
        fw.close() # Close the open file
        return CACHE_DICTION[unique_ident]


# users: pick a location
# program:
    # hotel name, rates, prices
class Hotel():
    # needs to be changed, obvi.
    def __init__(self, name, rate=0, price=0):
        self.name = name
        self.rate = rate
        self.price = price

    def __str__(self):
        statement = "The rate of "+ self.name + " is "+ self.rate + ". The price is " + self.priced
        return statement

def get_hotels(city):
    hotel_list = []
    url='http://compare.hotels-fairy.com/Hotels/Search?destination=place:'
    url = url + city +'&radius=0mi&checkin=2018-08-04&checkout=2018-08-05&Rooms=1&adults_1=2&pageSize=25&pageIndex=0&sort=Popularity-desc&showSoldOut=false&HotelID=&mapState=expanded%3D0'
    page_text = make_request_using_cache(url)
    page_soup = BeautifulSoup(page_text, 'html.parser')
    hotel_div = page_soup.find_all(class_='hc_hotel hc_sri_result')
    for i in range(len(hotel_div)):
        hotel_name_title = hotel_div[i].find('h3')
        hotel_name = hotel_name_title.find('a').string

        hotel_rate_desc = hotel_div[i].find('p',class_='hc_hotel_userRating')
        hotel_rate = hotel_rate_desc.find('a').string

        hotel_price = hotel_div[i].find('p',class_='hc_hotel_price').text.strip()
        hotel_price = hotel_price.split('$', 1 )
        hotel_price = int(hotel_price[-1])
        hotel = Hotel(name=hotel_name,rate=hotel_rate,price=hotel_price)
        hotel_list.append(hotel)

    return hotel_list

class Crime():
    # needs to be changed, obvi.
    def __init__(self, type, address='', date=''):
        self.type = type
        self.address = address
        self.date = date

def get_crime_info(hotel_name):
    # crime category, location,time
    crime_list = []
    name_list = []
    name_list =str(hotel_name).split()
    a = len(name_list)-1
    for i in name_list[0:a]:
        crime_url='https://spotcrime.com/mobile/index.html#'
        crime_url = crime_url + i + '%20'
    crime_url = crime_url + name_list[-1]
    page_text = make_request_using_cache(crime_url)
    soup = BeautifulSoup(page_text,'html.parser')
    data_table = soup.find('div', {'id': 'table_container'})
    for div in data_table.find_all('a', class_='list-group-item clearfix'):
        type = div.find('h4',class_='list-group-item-heading').text.strip()
        date = div.find('p',class_='list-group-item-text crime-date').string
        adress = div.find('p',class_='list-group-item-text crime-address').string
        crime = Crime(type=type,address=adress,date=date)
        crime_list.append(crime)
    return crime_list

# scrape data and write into csv
city_list = [
    'New_York_City','San_Francisco',"Boston",'Washington_DC','Austin','Seattle','Los_Angeles',
    'San_Diego',"New_Orleans",'Atlanta','Las_Vegas','Miami',
    'Phoenix','Columbus','Detroit','Orlando','Pittsburgh','Oakland'
    ]

with open('Hotels.csv', 'w', newline='') as csvfile:
    fieldnames = ['Name', 'Rate', 'Price','City']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for i in city_list:
        city = i
        hotels=get_hotels(i)
        for i in hotels:
            writer.writerow({'Name': i.name, 'Rate': i.rate, 'Price': i.price, 'City': city })

with open('Crime.csv', 'w', newline='') as csvfile:
    fieldnames = ['Type', 'Date', 'Address','Hotel']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for i in city_list:
        city = i
        hotels=get_hotels(i)
        for i in hotels:
            hotel_name = i.name
            try:
                crimes=get_crime_info(hotel_name)
                for i in crimes:
                    writer.writerow({'Type': i.type, 'Date': i.date, 'Address': i.address, 'Hotel': hotel_name })
            except:
                writer.writerow({'Type': 'none', 'Date': 'none', 'Address': 'none', 'Hotel': hotel_name })

# Store them into a database
conn = sqlite3.connect('hotel.db')
cur = conn.cursor()
statement = '''
    DROP TABLE IF EXISTS 'Hotel';
'''
cur.execute(statement)
conn.commit()
statement = '''
    DROP TABLE IF EXISTS 'City';
'''
cur.execute(statement)
conn.commit()
statement = '''
    DROP TABLE IF EXISTS 'Crime';
'''
cur.execute(statement)
conn.commit()
# create new table bars
statement = '''
    CREATE TABLE 'City' (
        'Id' INTEGER PRIMARY KEY AUTOINCREMENT,
        'Name' TEXT NOT NULL
    );
'''
cur.execute(statement)
conn.commit()

statement = '''
    CREATE TABLE 'Hotel' (
        'Id' INTEGER PRIMARY KEY AUTOINCREMENT,
        'Name' TEXT NOT NULL,
        'Rate' REAL,
        'Price' INTEGER,
        'City' TEXT NOT NULL
    );
'''
cur.execute(statement)
conn.commit()

statement = '''
    CREATE TABLE 'Crime' (
        'Id' INTEGER PRIMARY KEY AUTOINCREMENT,
        'Type' TEXT NOT NULL,
        'Date' TEXT NOT NULL,
        'Address' TEXT NOT NULL,
        'Hotel'TEXT NOT NULL,
        'HotelId' INTEGER
    );
'''
cur.execute(statement)
conn.commit()

# import cvs
ignore_header = False
with open('Hotels.csv', newline='') as csvfile:
    bar = csv.reader(csvfile, delimiter=',', quotechar='"')
    i= 0
    for params in bar:
        if ignore_header:
            i+=1
            insertion = (i,params[0],params[1],params[2],params[3])
            statement = 'INSERT INTO "Hotel" '
            statement += 'VALUES (?, ?, ?, ?, ?)'
            cur.execute(statement, insertion)
            conn.commit()
        ignore_header = True

ignore_header = False
with open('Crime.csv', newline='') as csvfile:
    bar = csv.reader(csvfile, delimiter=',')
    i= 0
    for params in bar:
        if ignore_header:
            i+=1
            insertion = (i,params[0],params[1],params[2],params[3],i)
            statement = 'INSERT INTO "Crime" '
            statement += 'VALUES (?, ?, ?, ?, ?, ?)'
            cur.execute(statement, insertion)
            conn.commit()
        ignore_header = True
i= 0
for city in city_list:
    i+=1
    insertion = (i,city)
    statement = 'INSERT INTO "City" '
    statement += 'VALUES (?, ?)'
    cur.execute(statement, insertion)
    conn.commit()

query = '''
        SELECT Hotel
        FROM Crime
'''
cur.execute(query)
hotel_list= cur.fetchall()
for hotel in hotel_list:
    query = '''
            SELECT Hotel.Id
            FROM Crime
                JOIN Hotel
                ON Crime.Hotel = Hotel.Name
            WHERE Crime.Hotel = ?
    '''
    params = (hotel[0],)
    cur.execute(query, params)
    id= cur.fetchone()

    params = (id[0],hotel[0])
    statement = '''
        UPDATE Crime
        SET HotelID = ?
        WHERE Crime.Hotel = ?
    '''
    cur.execute(statement, params)
    conn.commit()
