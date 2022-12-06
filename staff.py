from __main__ import app, render_template, request, session, url_for, redirect, conn
import pymysql.cursors
import hashlib
import sys
import datetime
from helperFuncs import *

@app.route('/FlightEditor')
@role_required("Staff")
def flightEditor():
	staffAirline = session["staffAirline"]
	flights = getFutureFlights(staffAirline)
	ap = get_airports()
	planes = getAirplanes(staffAirline)
	return render_template('Staff/FlightEditor.html', airports = ap, planes = planes, airline = staffAirline, flights = flights)


@app.route('/FlightEditor/addFlight', methods=['GET', 'POST'])
@role_required("Staff")
def addFlight(): 
	ap = get_airports()
	planes = getAirplanes()
	flights = getFutureFlights(staffAirline)
	staffAirline = session["staffAirline"]
	arrAirport = request.form['arrAir']
	depAirport = request.form['depAir']
	flightnum = request.form['flightnum']
	depTime = request.form["dptime"]
	depDate = request.form['dpdate']
	arrTime = request.form["artime"]
	arrDate = request.form['ardate']
	depDT = datetime.datetime.strptime(depDate +" "+depTime, '%Y-%m-%d %H:%M')
	arrDT = datetime.datetime.strptime(arrDate + " "+arrTime, '%Y-%m-%d %H:%M')
	roundTrip = False
	
	if(depAirport == arrAirport): 
		addFlightError = "Invalid Flight Departure and Arrival Airport are the Same"
		return render_template('Staff/FlightEditor.html', airports = ap, planes = planes, airline = staffAirline, addFlightError = addFlightError, addingFlight = True, flights = flights)

	if(findFlight(staffAirline, flightnum)): 
		addFlightError = "Flight Number Already Exists"
		return render_template('Staff/FlightEditor.html', airports = ap, planes = planes, airline = staffAirline, addFlightError = addFlightError, addingFlight = True, flights = flights)

	if(arrDT < depDT):
		addFlightError = "Invalid Date and Time, Arrival is Before Departure"
		return render_template('Staff/FlightEditor.html', airports = ap, planes = planes, airline = staffAirline, addFlightError = addFlightError, addingFlight = True, flights = flights)
		
	
	values = ( session["staffAirline"], request.form['airplane'], flightnum, request.form['dpdate'], 
	request.form['dptime'], request.form['ardate'], request.form['artime'], request.form['baseprice'], 
	request.form['status'], roundTrip, depAirport, arrAirport
	)
	query = "INSERT INTO flight VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
	cursor = conn.cursor() 
	cursor.execute(query, values)
	conn.commit()
	flights = getFutureFlights(staffAirline)
	return render_template('Staff/FlightEditor.html', airports = ap, planes = planes, airline = staffAirline, addFlightError = "Flight Successfully Added", addingFlight = True, flights = flights)


@app.route('/FlightEditor/editStatus', methods=['GET', 'POST'])
@role_required("Staff")
def editFlightStatus():

	print("i got here bitch")
	staffAirline = session["staffAirline"]
	uniPlanNum = request.form['unique_airplane_num']
	flight_number = request.form['flight_number']
	depDate = request.form['departure_date']
	depTime = request.form['departure_time']
	status = request.form['flight_status_val']
	query = "UPDATE flight SET status_flight = %s WHERE airline_name = %s AND unique_airplane_num = %s AND flight_number = %s AND departure_date = %s AND departure_time = %s"
	values = (status, staffAirline, uniPlanNum,flight_number, depDate, depTime)
	cursor = conn.cursor() 
	cursor.execute(query,values)
	conn.commit() 

	return flightEditor()


# Queries frequent customers and displays to Staff
@app.route('/Staff/frequentcustomers')
@role_required("Staff")
def frequentCustomer():
	query = """SELECT email as customer, count(email) as flights 
			FROM (
				SELECT *
				FROM ticket
				WHERE departure_date >= cast(DATE_ADD(CURDATE(), INTERVAL -1 YEAR) AS DATE)
				) as TABLE1
			WHERE airline_name = %s
			GROUP BY email 
			ORDER BY count(email) DESC;"""


	cursor = conn.cursor()


	cursor.execute(query, (session["staffAirline"]))
	data = cursor.fetchall();

	return render_template('/Staff/frequentCustomers.html', table_info=data);


# Calculates the revenue for the last month and year for the airline
@app.route('/Staff/revenue')
@role_required("Staff")
def revenue():

	# Revenue last year
	query = """SELECT sum(sold_price) as tot
				FROM (
				SELECT *
				FROM ticket
				WHERE departure_date >= cast(DATE_ADD(CURDATE(), INTERVAL -1 YEAR) AS DATE)
				) as TABLE1
				WHERE airline_name = %s;"""
	
	# Revenue last month
	query2 = """SELECT sum(sold_price) as tot 
				FROM (
				SELECT *
				FROM ticket
				WHERE departure_date >= cast(DATE_ADD(CURDATE(), INTERVAL -1 MONTH) AS DATE)
				) as TABLE1
				WHERE airline_name = %s;"""

	cursor = conn.cursor()

	airline = session["staffAirline"]


	# Query month and year
	cursor.execute(query, (airline))
	year = cursor.fetchone();
	cursor.execute(query2, (airline))
	month = cursor.fetchone();


	# If did not sum anything sets it to 0 else just the int
	year = 0 if not year["tot"] else year["tot"];
	month = 0 if not month["tot"] else month["tot"];

	return render_template("/Staff/revenue.html", month=month, year=year);