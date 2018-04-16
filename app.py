from flask import Flask, render_template, request, Markup
import model
from plotly.graph_objs import *
from plotly.offline import plot


app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def hotel():
    if request.method == 'POST':
        if request.form['Get_Hotels'] == 'Get Hotels':
            cities = request.form['cities']
            sortby = request.form['sortby']
            sortorder = request.form['sortorder']
            hotels = model.get_hotels(cities, sortby, sortorder)
    else:
        hotels = model.get_hotels()
    return render_template("user.html", hotels=hotels)

@app.route('/results', methods=['GET', 'POST'])
def crime():
    if request.method == 'POST':
        if request.form['Get_Crimes_Map'] == 'Get Crimes Map':
            hotelname= request.form['hotelname']
            div = model.plot_hotel_and_crimes(hotelname)
    else:
        div = model.plot_hotel_and_crimes()
    return render_template("results.html", name = hotelname, div_placeholder=Markup(div))

if __name__ == '__main__':
    model.init_database()
    app.run(debug=True)
