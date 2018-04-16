from fproject import *
from model import *
import unittest

class TestHotelInfo(unittest.TestCase):

    def test_get_hotels(self):
        hotel_list = get_hotels('San_Francisco')
        self.assertEqual(hotel_list[0][0], 'Hotel Beresford')

class TestCrimeInfo(unittest.TestCase):

    def test_crime_info(self):
        crime_list = get_crime_info('Villa Florence')
        self.assertEqual(crime_list[0].type, 'Assault')
        self.assertEqual(crime_list[2].address, '500 BLOCK OF ELLIS ST')
        self.assertEqual(crime_list[5].date, '04/11/18 09:54 PM')
        self.assertEqual(len(crime_list), 50)

class TestDatabase(unittest.TestCase):

    def test_hotel_table(self):
        conn = sqlite3.connect('hotel.db')
        cur = conn.cursor()

        sql = 'SELECT Name FROM Hotel'
        results = cur.execute(sql)
        result_list = results.fetchall()
        self.assertIn(('Hilton Boston Back Bay',), result_list)
        self.assertEqual(len(result_list), 350)

        sql = '''
            SELECT Name, Rate, Price, City
            FROM Hotel
            WHERE City="Oakland"
            ORDER BY Price DESC
        '''
        results = cur.execute(sql)
        result_list = results.fetchall()
        #print(result_list)
        self.assertEqual(len(result_list), 25)
        self.assertEqual(result_list[2][0], 'Waterfront Hotel Oakland')
        self.assertEqual(result_list[5][2], 216)

        conn.close()

    def test_crime_table(self):
        conn = sqlite3.connect('hotel.db')
        cur = conn.cursor()

        sql = '''
            SELECT Type, Date, Address, Hotel
            FROM Crime
            WHERE Type = 'Assault'
        '''
        results = cur.execute(sql)
        result_list = results.fetchall()
        self.assertEqual(len(result_list), 1873)

        sql = '''
            SELECT Hotel,COUNT(*)
            FROM Crime
                JOIN Hotel
                ON Hotel.name = Crime.Hotel
            Group BY Crime.Hotel
            ORDER BY COUNT(*) DESC
        '''
        results = cur.execute(sql)
        result_list = results.fetchall()
        self.assertIn(('Best Western PLUS Carriage Inn', 50), result_list)
        self.assertEqual(len(result_list), 326)
        self.assertEqual(result_list[-1][1], 5)

        conn.close()

    def test_city_table(self):
        conn = sqlite3.connect('hotel.db')
        cur = conn.cursor()

        sql = '''
            SELECT Name
            FROM City
        '''
        results = cur.execute(sql)
        result_list = results.fetchall()
        self.assertEqual(len(result_list), 18)
        self.assertIn(('Los_Angeles',), result_list)

        conn.close()

    def test_joins(self):
        conn = sqlite3.connect('hotel.db')
        cur = conn.cursor()

        sql = '''
            SELECT Address
            FROM Crime
                JOIN Hotel
                ON Hotel.name=Crime.hotel
            WHERE Hotel.city="Los_Angeles"
        '''
        results = cur.execute(sql)
        result_list = results.fetchall()
        self.assertIn(('10600 BLOCK OF VICTORY BL',), result_list)
        self.assertEqual(len(result_list), 957)
        conn.close()

class TestHotelSearch(unittest.TestCase):

    def test_search(self):
        hotel_list = get_hotels(cities='San_Francisco', sortby ='300', sortorder='desc')
        self.assertEqual(hotel_list[0][0], 'Omni San Francisco Hotel')
        self.assertEqual(hotel_list[2][1], 'Very Good, 8.5')
        self.assertEqual(hotel_list[-1][2], 205)
        self.assertEqual(len(hotel_list), 12)

class TestMapping(unittest.TestCase):

    def test_show_crime_map(self):
        try:
            plot_hotel_and_crimes(hotelname='Hotel Zephyr')
            # plot_hotel_and_crimes(hotelname='Hotel Zephyr')
        except:
            self.fail()



if __name__ == '__main__':
    unittest.main(verbosity=2)
