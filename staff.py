from __main__ import app, render_template, request, session, url_for, redirect, conn
import pymysql.cursors
import hashlib
import sys
import datetime
from dateutil.relativedelta import relativedelta
from helperFuncs import *



@app.route('/Staff/staff')
@role_required("Staff")
def staff():
	'''
	The Staff Homepage. It creates 
	'''
	airports = get_airports()
	return render_template("Staff/staff.html", airports = airports)

@app.route('/FlightEditor/searchFlight', methods=['GET', 'POST'])
@role_required("Staff")
def staffSearchFlight():
	airline = session["staffAirline"]
	dep = request.form['dep']
	arr = request.form['arr']
	arrCity = request.form['arrCity']
	depCity = request.form['depCity']
	arrCountry = request.form['arrCountry']
	depCountry = request.form['depCountry']
	start = request.form['start']
	end = request.form['end']
	if(start): start = datetime.datetime.strptime(start, '%Y-%m-%d').date()
	if(end): end = datetime.datetime.strptime(end, '%Y-%m-%d').date()
	flights = searchFlight(dep = dep, arr = arr, arrCity=arrCity, depCity=depCity, start = start, end = end, arrCountry = arrCountry, depCountry = depCountry, airline=airline)
	add_time_difference(flights)
	for flight in flights: 
		cust = findCustomersForFlight(flight)
		flight["customers"] = cust 
		print(cust)
		print(len(cust))

	return flightEditor(flights = flights)

@app.route('/FlightEditor')
@role_required("Staff")
def flightEditor(addingFlight = False, addFlightError = None, addingAirplane = False, addAirplaneError = None, addingAirport = False, addAirportError = None, flights = None):
	staffAirline = session["staffAirline"]
	if(flights == None):
		flights = searchFlight(airline=staffAirline)
	flights = add_time_difference(flights)
	ap = get_airports()
	planes = getAirplanes(staffAirline)
	return render_template('Staff/FlightEditor.html', airports = ap, planes = planes, airline = staffAirline, 
	flights = flights, addingFlight = addingFlight, addFlightError = addFlightError, addingAirplane = addingAirplane, addAirplaneError =addAirplaneError,
	addingAirport = addingAirport, addAirportError = addAirportError )


@app.route('/FlightEditor/addFlight', methods=['GET', 'POST'])
@role_required("Staff")
def addFlight(): 
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
		return flightEditor(True, addFlightError)

	if(findFlight(staffAirline, flightnum)): 
		addFlightError = "Flight Number Already Exists"
		return flightEditor(True, addFlightError)

	if(arrDT < depDT):
		addFlightError = "Invalid Date and Time, Arrival is Before Departure"
		return flightEditor(True, addFlightError)
		
	
	values = ( session["staffAirline"], request.form['airplane'], flightnum, request.form['dpdate'], 
	request.form['dptime'], request.form['ardate'], request.form['artime'], request.form['baseprice'], 
	request.form['status'], roundTrip, depAirport, arrAirport
	)
	query = "INSERT INTO flight VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
	cursor = conn.cursor() 
	try:
		cursor.execute(query, values)
		 
	except: 
		addFlightError = "Invalid Inputs"
		return flightEditor(True, addFlightError)
	conn.commit()
	flights = getFutureFlights(staffAirline)
	addFlightError = "Successfully Added Flight"
	return flightEditor(True, addFlightError)



@app.route('/FlightEditor/editStatus', methods=['GET', 'POST'])
@role_required("Staff")
def editFlightStatus():

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


@app.route('/FlightEditor/addAirplane', methods=['GET', 'POST'])
@role_required("Staff")
def addAirplane():
	staffAirline = session["staffAirline"]
	airplaneNum = request.form["uniAir"]
	seats = request.form["seat"]
	company = request.form["company"]
	age = request.form["age"]
	query = "Select * FROM airplane WHERE airline_name = %s AND unique_airplane_num = %s"
	cursor = conn.cursor() 
	cursor.execute(query, (staffAirline, airplaneNum))
	data = cursor.fetchone() 
	if(data): 
		return flightEditor(False, None, True, "Airplane Number Already Exists")
	query = "INSERT INTO airplane VALUES(%s, %s,%s,%s, %s)"
	try:
		cursor.execute(query,(staffAirline, airplaneNum, seats, company, age))
	except: 
		error = "Invalid Inputs"
		return flightEditor(False, None, True, error)
		

	conn.commit()
	return flightEditor(False, None, True, "Successfully Added Airplane")


@app.route('/FlightEditor/addAirport', methods=['GET', 'POST'])
@role_required("Staff")
def addAirport():
	name = request.form["name"]
	aType = request.form['type']
	city = request.form['city']
	country = request.form['country']

	query = "Select * FROM airport WHERE name = %s"
	cursor = conn.cursor() 
	cursor.execute(query, (name))
	data = cursor.fetchone() 
	if(data): 
		return flightEditor(False, None, False, None, True, "Airport Name Already Exists")
	query = "INSERT INTO airport VALUES(%s, %s,%s,%s)"
	try:
		cursor.execute(query,(name, city, country, aType))
	except:
		error = "Invalid Inputs"
		return flightEditor(False, None, False, None, True, error)
	conn.commit()
	return flightEditor(False, None, False, None, True, "Successfully Added Airport")


# Queries frequent customers and displays to Staff
@app.route('/Staff/frequentcustomers')
@role_required("Staff")
def frequentCustomer():
	view = """CREATE VIEW customerflights AS SELECT email as customer, count(email) as flights 
	FROM (
		SELECT *
		FROM ticket
				WHERE departure_date >= cast(DATE_ADD(CURDATE(), INTERVAL -1 YEAR) AS DATE)
				) as TABLE1
			WHERE airline_name = %s GROUP BY email ORDER BY count(email) DESC;"""

	query = """SELECT * from customerflights
WHERE flights = (SELECT max(flights) FROM customerflights);"""

	dropView = "DROP VIEW customerflights;"
	
	
	
	cursor = conn.cursor()

	cursor.execute(view, (session["staffAirline"]))
	cursor.execute(query)
	data = cursor.fetchall();
	cursor.execute(dropView);

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


# Calculates the revenue for the last month and year for the airline
@app.route('/Staff/report', methods=['GET', 'POST'])
@role_required("Staff")
def report():
	
	ranged = request.form["range"]
	cursor = conn.cursor();

	if ranged == "Range":
		start = request.form["from"]
		end = request.form["to"]

	elif ranged == "Month":
		today = datetime.date.today();
		delta = relativedelta(months=1)
		start = (today - delta).strftime("%y-%m-%d")
		end = today

	elif ranged == "Year":
		today = datetime.date.today();
		delta = relativedelta(years=1)
		start = (today - delta).strftime("%y-%m-%d")
		end = today

	

	data = calculate_by_month(start, end, 'count(ticket_id)', "%", session["staffAirline"]);
	total = sum([i["tot"] for i in data])
	return render_template("/Staff/report.html", table_info=data, total=total);
	

@app.route('/Staff/ViewComments')
@role_required("Staff")
def viewComments(fNum = None, aNum = None, dDate = None, dTime = None, customer = None):
	airline = session["staffAirline"]
	comments = getComments(aName = airline, fNum=fNum, aNum=aNum, dDate=dDate, dTime=dTime, customer=customer)
	avg = 0 
	error = None
	if(len(comments) > 0): 
		for c in comments: 
			avg += c["rating"]
		avg = avg/len(comments)
	else: 
		error = "No Comments Found"
	return render_template("Staff/viewComments.html", airline = airline, comments = comments,fNum=fNum, aNum=aNum, dDate=dDate, dTime=dTime, customer=customer, avg = avg, error = error)
	
	
	
@app.route('/Staff/findComments', methods=['GET', 'POST'])
@role_required("Staff")
def findComments():
	fNum = request.form['fNum']
	aNum = request.form['aNum']
	dDate = request.form['dDate']
	dTime = request.form['dTime']
	customer = request.form['customer']
	return viewComments(fNum = fNum, aNum = aNum, dDate = dDate, dTime = dTime, customer = customer)
	