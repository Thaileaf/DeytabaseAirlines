#Import Flask Library
from flask import Flask, render_template, request, session, url_for, redirect
import pymysql.cursors
import hashlib
import sys
from datetime import datetime, timedelta, date
from dateutil import rrule
import re
import random

#Initialize the app from Flask
app = Flask(__name__)

#Configure MySQL
conn = pymysql.connect(host='localhost',
                       user='root',
                       password='',
                       db='flight_sim',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor,
					   port=3306
					   )
import register
import account
from helperFuncs import *

#Define a route to hello function
@app.route('/')
def root():
	cursor = conn.cursor()
	flights_query = 'SELECT * from flight where flight.departure_date >= CAST(CURRENT_DATE() as Date)'
	cursor.execute(flights_query)
	flights = cursor.fetchall()
	airports = get_airports()
	cursor.close()
	
	return render_template('index.html', flights=flights, airports=airports)

@app.route('/flights', methods=['GET', 'POST'])
def flights():
	# non-logged in use case for search
	airport = request.form['airport']
	departure_date = request.form['depart']
	return_date = request.form['return']
	print(return_date)
	cursor = conn.cursor()

	if not return_date:
		query = 'SELECT * from flight where departure_date = %s and depart_from = %s'
		cursor.execute(query, (departure_date, airport))
	else:
		query = 'SELECT * from flight where departure_date = %s and depart_from = %s and arrive_at in (Select depart_from from flight where departure_date = %s);' 
		cursor.execute(query, (departure_date, airport, return_date))	

	data = cursor.fetchall()	
	return render_template('index.html', flights=data)

@app.route('/pastFlights', methods=["GET"])
# @role_required('Customer')
def past_flights():
    # email = session['email']
	email = "totallylegit@nyu.edu"
	cursor = conn.cursor()
	query = "SELECT * from flight natural join ticket as C left join ratings on (ratings.airline_name = C.airline_name and ratings.email = C.email and ratings.unique_airplane_num = C.unique_airplane_num and ratings.flight_number = C.flight_number and ratings.departure_date = C.departure_date and ratings.departure_time = C.departure_time) where flight.departure_date < CAST(CURRENT_DATE() as Date) and C.email = %s"
	cursor.execute(query, (email))

	data = cursor.fetchall() 
	print(data)
	return render_template('index.html', flights=data, hide_header=True, past_flights=True)


@app.route('/comment', methods=["POST"])
def comment():
	rating = request.form['rating']
	comment = request.form['comment']
	
	email = "sonic@nyu.edu"
	airline_name = str(request.form['airline_name'])
	unique_airplane_num = int(float(request.form['unique_airplane_num']))
	flight_number = int(float(request.form['flight_number']))
	departure_date = str(request.form['departure_date'])
	departure_time = str(request.form['departure_time'])

	cursor = conn.cursor()
	query = 'INSERT into ratings Values (%s, %s, %s, %s, %s, %s, %s, %s)'
	
	cursor.execute(query, (email, airline_name, unique_airplane_num, flight_number, departure_date, departure_time, rating, comment))	
	conn.commit()
	cursor.close()
	return render_template('submitted.html')

# should be customer only
@app.route('/futureFlights', methods=["GET"])
# @role_required('Customer')
def future_flights():
	# customer version  
	email = "notlegit@nyu.edu"
	cursor = conn.cursor()
	# add email check here too
	query = 'SELECT * from flight natural join ticket where flight.departure_date >= CAST(CURRENT_DATE() as Date) and email = %s;'
	cursor.execute(query, (email))
	data = cursor.fetchall()
	return render_template('index.html', flights=data, hide_header=True)

@app.route('/getTickets', methods=["GET", "POST"])
def get_tickets():
	email = "totallylegit@nyu.edu"
	cursor = conn.cursor()
	query = 'SELECT * from ticket where email = %s'
	
	cursor.execute(query, (email))
	data = cursor.fetchall()
	return render_template('index.html', flights=data, hide_header=True, bought_tickets=True)

@app.route('/buyTicket', methods=["GET", "POST"])
def buyTicket():
	cursor = conn.cursor()

	ticket_id = random.randrange(1, 10**10)
	query = 'SELECT * from ticket where ticket.ticket_id = %s'
	cursor.execute(query, (ticket_id))	
	check = cursor.fetchone()
	error_count = 0
	
	while check and error_count < 50:
		error_count += 1
		ticket_id = '{:05}'.format(random.randrange(1, 10**5))
		cursor.execute(query, (ticket_id))	
		check = cursor.fetchone()
	if check:
		raise RuntimeError("Unable to generate ticket_id")

	# print(ticket_id)

	#add random addition to base 
	#purchase date, purchase time, email in python code

	purchase_date = date.today()
	purchase_time = datetime.now().strftime("%H:%M:%S")
	email = "sonic@nyu.edu"

	airline_name = str(request.form['airline_name'])
	unique_airplane_num = int(float(request.form['unique_airplane_num']))
	flight_number = int(float(request.form['flight_number']))
	departure_date = str(request.form['departure_date'])
	departure_time = str(request.form['departure_time'])
	card_type = request.form['drone']
	card_number = int(request.form['card_number'])
	name_on_card = request.form['name_on_card']
	expiration = request.form['expiration'] + "-01" #adding extra day to conform with db
	base_price = int(float(request.form['base_price']))
	# print(expiration)

	print(airline_name)
	print(unique_airplane_num)
	print(flight_number)
	print(departure_date)
	print(departure_time)

	
	query = 'SELECT * from flight where airline_name = %s and unique_airplane_num = %s and flight_number = %s and departure_date = %s and departure_time = %s'
	cursor.execute(query, (airline_name, unique_airplane_num, flight_number, departure_date, departure_time)) #departure_date, departure_date
	data = cursor.fetchone()
	# print(data)
	if (data):
		query = 'INSERT into ticket Values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
		cursor.execute(query, (ticket_id, airline_name, unique_airplane_num, flight_number, departure_date, departure_time, card_type, card_number, name_on_card, expiration, base_price + 10, email, purchase_date, purchase_time))
		conn.commit()
		cursor.close()
		# print("")

	return render_template('submitted.html')


app.secret_key = 'some key that you will never guess'
#Run the app on localhost port 5000
#debug = True -> you don't have to restart flask
#for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
	app.run('127.0.0.1', 5000, debug = True)