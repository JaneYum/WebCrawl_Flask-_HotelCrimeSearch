import sqlite3
import requests
import json
from secrets import *
import plotly.plotly as py
from plotly.graph_objs import *
from plotly.offline import plot


DB_FILE_NAME = 'hotel.db'
# API cache
CACHE_FNAME = 'cache_location.json'
try:
    cache_file = open(CACHE_FNAME, 'r')
    cache_contents = cache_file.read()
    CACHE_DICTION = json.loads(cache_contents)
    cache_file.close()
# if there was no file, no worries. There will be soon!
except:
    CACHE_DICTION = {}


def params_unique_combination(baseurl, params):
    alphabetized_keys = sorted(params.keys())
    res = []
    for k in alphabetized_keys:
        res.append("{}-{}".format(k, params[k]))
    return baseurl + "_".join(res)


def make_API_request_using_cache(baseurl, params):
    unique_ident = params_unique_combination(baseurl,params)


    if unique_ident in CACHE_DICTION:
        #print("Getting cached data...")
        return CACHE_DICTION[unique_ident]
    else:
        print("Making a request for new data...")
        # Make the request and cache the new data
        resp = requests.get(baseurl, params)
        CACHE_DICTION[unique_ident] = json.loads(resp.text)
        dumped_json_cache = json.dumps(CACHE_DICTION)
        fw = open(CACHE_FNAME,"w")
        fw.write(dumped_json_cache)
        fw.close() # Close the open file
        return CACHE_DICTION[unique_ident]


def init_database(db_name=DB_FILE_NAME):
    conn = sqlite3.connect(db_name)
    cur = conn.cursor()

def get_hotels(cities='San_Francisco', sortby ='200', sortorder='desc'):
    conn = sqlite3.connect(DB_FILE_NAME)
    cur = conn.cursor()
    query = '''
            SELECT Hotel.Name,Rate,Price
            FROM Hotel
                JOIN City
                ON City.Name= Hotel.City
            WHERE Hotel.City = ?
    '''


    if sortby == '100':
        query += " AND Hotel.Price <= 100 "
    elif sortby == '200':
        query += " AND Hotel.Price > 100 AND Hotel.Price <= 200 "
    elif sortby == '300':
        query += " AND Hotel.Price > 200 AND Hotel.Price <= 300 "
    else:
        query += " AND Hotel.Price > 300 "

    if sortorder == 'desc':
        query += 'ORDER BY "Price" DESC'
    elif sortorder == 'asc':
        query += 'ORDER BY "Price"'
    else:
        query += 'ORDER BY "Price" DESC'

    params = (cities,)
    cur.execute(query, params)
    Hotel_info= cur.fetchall()
    return Hotel_info

def plot_hotel_and_crimes(hotelname='Hotel Zephyr'):
    conn = sqlite3.connect(DB_FILE_NAME)
    cur = conn.cursor()
    # # hotel_name - lan lng
    hotel_lat_vals = []
    hotel_lon_vals = []
    hotel_text_vals = []
    baseurl = 'https://maps.googleapis.com/maps/api/place/textsearch/json'
    params = {}
    params['key'] = google_places_key
    params['query'] = hotelname
    nearbyplace = make_API_request_using_cache(baseurl, params)['results']
    if nearbyplace != []:
        lat = nearbyplace[0]['geometry']['location']['lat']
        lng = nearbyplace[0]['geometry']['location']['lng']
        hotel_lat_vals.append(lat)
        hotel_lon_vals.append(lng)
        hotel_text_vals.append(hotelname)

    # hotel_name - crime.address - lan lng
    query = '''
            SELECT Address,Type
            FROM Crime
            WHERE Crime.Hotel = ?
    '''
    params = (hotelname,)
    cur.execute(query, params)
    address_list= cur.fetchall()

    query = '''
            SELECT City
            FROM Hotel
            WHERE Name = ?
    '''
    params = (hotelname,)
    cur.execute(query, params)
    city = cur.fetchone()
    city = city[0].replace('_',' ')
    lat_vals = []
    lon_vals = []
    text_vals = []
    for address in address_list:
        baseurl = 'https://maps.googleapis.com/maps/api/place/textsearch/json'
        # address=1600+Amphitheatre+Parkway,+Mountain+View,+CA
        params = {}
        params['key'] = google_places_key
        params['query'] = address[0]
        nearbyplace = make_API_request_using_cache(baseurl, params)['results']
        # print(nearbyplace)

        if nearbyplace != []:
            location = nearbyplace[0]['formatted_address']
            baseurl = 'https://maps.googleapis.com/maps/api/geocode/json'
            # address=1600+Amphitheatre+Parkway,+Mountain+View,+CA
            params = {}
            params['key'] = google_geo_key
            params['address'] = location
            crime_spot = make_API_request_using_cache(baseurl, params)['results']
            # print(crime_spot)
            if crime_spot != []:
                try:
                    if crime_spot[0]['address_components'][3]['long_name']==city:
                        lat = crime_spot[0]['geometry']['location']['lat']
                        lng = crime_spot[0]['geometry']['location']['lng']
                        location = "( "+address[1] +" ) "+  location
                        lat_vals.append(lat)
                        lon_vals.append(lng)
                        text_vals.append(location)
                except:
                    print('none')

    min_lat = 10000
    max_lat = -10000
    min_lon = 10000
    max_lon = -10000

    lat_vals_range = lat_vals + hotel_lat_vals
    lon_vals_range = lon_vals + hotel_lon_vals

    for str_v in lat_vals_range:
        v = float(str_v)
        if v < min_lat:
            min_lat = v
        if v > max_lat:
            max_lat = v
    for str_v in lon_vals_range:
        v = float(str_v)
        if v < min_lon:
            min_lon = v
        if v > max_lon:
            max_lon = v

    center_lat = (max_lat+min_lat) / 2
    center_lon = (max_lon+min_lon) / 2

    data = Data([
        Scattermapbox(
            lat=hotel_lat_vals,
            lon=hotel_lon_vals,
            mode='markers',
            marker=Marker(
                size = 20,
                symbol = 'star',
                color = 'yellow'
            ),
            text=hotel_text_vals,
        ),
        Scattermapbox(
            lat=lat_vals,
            lon=lon_vals,
            mode='markers',
            marker=Marker(
                size=9,
                symbol = 'circle',
                color = 'blue'
            ),
            text=text_vals,
        )
    ])

    layout = Layout(
        autosize=True,
        hovermode='closest',
        mapbox=dict(
            accesstoken=mapbox_access_token,
            bearing=0,
            center=dict(
                lat=center_lat,
                lon=center_lon
            ),
            pitch=0,
            zoom=13
        ),
    )

    fig = dict(data=data, layout=layout)
    # py.plot(fig, validate=False)
    # fig = go.Figure(data=data, layout=layout)
    div = plot(fig, show_link=True, output_type="div", include_plotlyjs=False)
    return div
