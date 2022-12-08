from __main__ import app, render_template, request, session, url_for, redirect, conn
import pymysql.cursors
import hashlib
import sys
from helperFuncs import *
from functools import wraps
from datetime import datetime
import random
from datetime import datetime, timedelta, date

@app.route('/myaccount')
def myaccount():
	if "email" in session:
		return redirect('/Customers/customer')
	elif "username" in session:
		return redirect('/Staff/staff')

# Customer Use Cases
@app.route('/Customers/customer')
@role_required("Customer")
def customer():
    return render_template("Customers/customer.html")

#Define a route to hello function
@app.route('/')
def root():
    # should only show future flights for which the traveler has purchased tickets from - also shouldn't manage tickets (canceling flights) here, should be done on the ticket page
    airports = get_airports()
    if 'email' in session: # check if a customer is logged in 
        email = session['email']
        cursor = conn.cursor()
        query = 'SELECT distinct F.airline_name, F.unique_airplane_num, F.flight_number, F.departure_date, F.departure_time, F.arrival_date, F.arrival_time, F.base_price, F.status_flight, F.roundtrip, F.depart_from, F.arrive_at from flight as F, ticket as T where F.airline_name = T.airline_name and F.unique_airplane_num = T.unique_airplane_num and F.flight_number = T.flight_number and F.departure_date = T.departure_date and F.departure_time = T.departure_time and email = %s'       
        cursor.execute(query, (email)) 
        flights = cursor.fetchall()
        # storing all flights in one big session, the button can still have a few hidden inputs to match the flights
        flights = add_time_difference(flights)

        # for flight in flights:
        #     key = str(flight['airline_name']) + str(flight['unique_airplane_num']) + str(flight['flight_number']) + str(flight['departure_date']) + str(flight['departure_time'])
        #     session[key] = [
        #         flight['airline_name'], #0
        #         flight['unique_airplane_num'], #1
        #         flight['flight_number'], #2
        #         flight['departure_date'], #3
        #         str(flight['departure_time']), #4 
        #         flight['arrival_date'], #5
        #         str(flight['arrival_time']), #6 
        #         flight['base_price'], #7
        #         flight['status_flight'], #8 
        #         flight['depart_from'], #9
        #         flight['arrive_at']] #10

            # print(key, session[key])

        return render_template('index.html', flights=flights, airports=airports, book_flights=False)
    else:
        # flights = getFutureFlights()
        cursor = conn.cursor()
        query = 'SELECT * from flight'
        cursor.execute(query)
        flights = cursor.fetchall()      

        # query = 'SELECT * from f'
        print(flights)  
        return render_template('index.html', flights=flights, airports=airports)

@app.route('/searchFlights', methods=['GET', 'POST'])
def flights():
    # storing all flights in one big session, the button can still have a few hidden inputs to match the flights
    # fix nonroundtrip search first

    cursor = conn.cursor()
    query = 'SELECT * from flight'
    cursor.execute(query)
    flights = cursor.fetchall()

    # add all flights to the session
    flights = add_time_difference(flights)

    for flight in flights:
        key = str(flight['airline_name']) + str(flight['unique_airplane_num']) + str(flight['flight_number']) + str(flight['departure_date']) + str(flight['departure_time'])
        session[key] = [
            flight['airline_name'], #0
            flight['unique_airplane_num'], #1
            flight['flight_number'], #2
            flight['departure_date'], #3
            str(flight['departure_time']), #4 
            flight['arrival_date'], #5
            str(flight['arrival_time']), #6 
            flight['base_price'], #7
            flight['status_flight'], #8 
            flight['depart_from'], #9
            flight['arrive_at']] #10
    

    arrival_airport, arrival_city, arrival_date = None, None, None
    if 'email' in session:
        print(request.form)
        arrival_airport = request.form['arrival_airport']
        arrival_city = request.form['arrival_city']
        arrival_date = request.form['arrival_date']

    try:
        roundtrip_date = request.form['roundtrip_date']
    except:
        roundtrip_date = None

    # print(request.form['roundtrip_date'])   
    departure_airport = request.form['departure_airport']
    departure_city = request.form['departure_city']
    departure_date = request.form['departure_date']
    show_book_button = False

    if departure_airport == "": departure_airport = None  
    if departure_date == "": departure_date = None
    if departure_city == "": departure_city = None
    if arrival_airport == "": arrival_airport = None
    if arrival_city == "": arrival_city = None
    if arrival_date == "": arrival_date = None

    if 'email' in session:
        data = userSearchFlight(departure_airport, arrival_airport, departure_city, arrival_city, departure_date, arrival_date, roundtrip_date)
        print(data)
        # cursor = conn.cursor()

        # if roundtrip selected, do the below query (but when you get back to the flask code, save the previous keys in prev session states)
        #departure_date = %s and depart_from = %s and arrive_at = %s"
        show_book_button = True
        return render_template('index.html', flights=data, hide_header=True, book_flights=show_book_button, roundtrip_date=roundtrip_date)

    else:
        cursor = conn.cursor()        
        query = 'SELECT * from flight where departure_date = %s and depart_from = %s and arrive_at = %s'
        cursor.execute(query, (departure_date, departure_airport, arrival_airport))	
        data = cursor.fetchall()
        return render_template('index.html', flights=data, hide_header=True, book_flights=show_book_button, re_search=True)


@app.route('/pastFlights', methods=["GET"])
@role_required('Customer')
def pastFlights():
    email = session['email']
    cursor = conn.cursor()
    query = "SELECT * from flight natural join ticket as C left join ratings on (ratings.airline_name = C.airline_name and ratings.email = C.email and ratings.unique_airplane_num = C.unique_airplane_num and ratings.flight_number = C.flight_number and ratings.departure_date = C.departure_date and ratings.departure_time = C.departure_time) where flight.departure_date < CAST(CURRENT_DATE() as Date) and C.email = %s"
    cursor.execute(query, (email))
    
    flights = cursor.fetchall() 
    flights = add_time_difference(flights)

    return render_template('index.html', flights=flights, hide_header=True, past_flights=True) # this doesn't seem to work ??????

@app.route('/comment', methods=["POST"])
@role_required('Customer')
def comment():
	email = session['email']
	rating = request.form['rating']
	comment = request.form['comment']
	airline_name = str(request.form['airline_name'])
	unique_airplane_num = int(float(request.form['unique_airplane_num']))
	flight_number = int(float(request.form['flight_number']))
	departure_date = str(request.form['departure_date'])
	departure_time = str(request.form['departure_time'])

    # need to check for duplicate entry still here
	cursor = conn.cursor()
	query = 'INSERT into ratings Values (%s, %s, %s, %s, %s, %s, %s, %s)'
	
	cursor.execute(query, (email, airline_name, unique_airplane_num, flight_number, departure_date, departure_time, rating, comment))	
	conn.commit()
	cursor.close()
	return render_template('submitted.html')

# Ticket management
@app.route('/getTickets', methods=["GET", "POST"])
@role_required('Customer')
def get_tickets():
    email = session['email']
    cursor = conn.cursor()
    query = 'SELECT * from ticket where email = %s'
    
    # need to add 24 hour requirement still
    cursor.execute(query, (email))
    tickets = cursor.fetchall()

    for ticket in tickets:
        departure = datetime.strptime(str(ticket["departure_date"])+" "+str(ticket["departure_time"]),  '%Y-%m-%d %H:%M:%S')
        current = departure - datetime.now() 
        if current > timedelta(days=1):
            ticket["can_cancel"] = True
        else:
            ticket["can_cancel"] = False
        # print(current)
        # arr = datetime.strptime(str(flight["arrival_date"])+" "+str(flight["arrival_time"]),  '%Y-%m-%d %H:%M:%S')
        # flight["total_time"] = str(arr - dep)

    return render_template('index.html', flights=tickets, hide_header=True, view_tickets=True)

# Buying a ticket
@app.route('/buyTicket', methods=["GET", "POST"])
@role_required('Customer')
def buyTicket():  
    # if roundtrip_book:
    #     pass

    ticket_id = generate_ticket_id()
    purchase_date = date.today()
    purchase_time = datetime.now().strftime("%H:%M:%S")
    email = session['email']

    airline_name = request.form['airline_name']
    unique_airplane_num = request.form['unique_airplane_num']
    flight_number = str(request.form['flight_number'])
    departure_date = str(request.form['departure_date'])
    departure_time = str(request.form['departure_time'])
    # key = airline_name + str(unique_airplane_num) + str(flight_number) + departure_date + departure_time
    key = str(airline_name) + str(unique_airplane_num) + str(flight_number) + str(departure_date) + str(departure_time)
    print(key)

    card_type = request.form['card_type']
    card_number = int(request.form['card_number'])
    name_on_card = request.form['name_on_card']
    expiration = request.form['expiration'] + "-01" #adding extra day to conform with db

    # print(key)
    # print(session)


        #session[key] = [
        #         flight['airline_name'], #0
        #         flight['unique_airplane_num'], #1
        #         flight['flight_number'], #2
        #         flight['departure_date'], #3
        #         str(flight['departure_time']), #4 
        #         flight['arrival_date'], #5
        #         str(flight['arrival_time']), #6 
        #         flight['base_price'], #7
        #         flight['status_flight'], #8 
        #         flight['depart_from'], #9
        #         flight['arrive_at']] #10

    # base_price = int(float(request.form['base_price']))
    # arrival_date = request.form('arrival_date')
    print(session)
    departure_airport = session[key][9]
    arrival_airport = session[key][10]
    base_price = session[key][7]
    try:
        roundtrip_date = request.form['roundtrip_date']
        # print(roundtrip_date)
        session['roundtrip_date'] = roundtrip_date
    except:
        roundtrip_date = None

    # print(roundtrip_date)
    cursor = conn.cursor()        


    if roundtrip_date:
        # set previous flight info before it gets overwritten
        print("Reached here!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        session['prev_airline_name'] = session[key][0]
        session['prev_unique_airplane_num'] = session[key][1]
        session['prev_flight_number'] = session[key][2]
        session['prev_departure_date'] = session[key][3]
        session['prev_departure_time'] = session[key][4]
        session['prev_base_price'] = session[key][7]
        session['card_type'] = card_type
        session['card_number'] = card_number
        session['name_on_card'] = name_on_card
        session['expiration'] = expiration


        # get the roundtrip flights
        # query = 'SELECT * from flight where departure_date = %s and depart_from = %s'
        # data1 = cursor.execute(query, (departure_date, departure_airport, arrival_airport))
        # data2 = cursor.execute(query, (roundtrip_date, arrival_airport, ))
        
        # # All flights where departure_date is the arrival_date, depart_from is arrival_airport, dearture_date is dep, arrive_at is depart_from   
        # and arrive_at in (Select depart_from from flight where departure_date = %s and arrive_at = %s );'
        query = 'SELECT * from flight where departure_date = %s and depart_from = %s and arrive_at = %s' # , departure_date, departure_airport
        cursor.execute(query, (roundtrip_date, arrival_airport, departure_airport))
        # print(roundtrip_date, arrival_airport, departure_airport)
        data = cursor.fetchall()    
        # print(data)

        return render_template("index.html", flights=data, changed_book=True, hide_header=True)
    else:   
        data = unique_flight(airline_name, unique_airplane_num, flight_number, departure_date, departure_time)

        if (data):  
            base_price = price_modify(airline_name, unique_airplane_num, flight_number, departure_date, departure_time, base_price)

            query = 'INSERT into ticket Values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
            cursor.execute(query, (ticket_id, airline_name, unique_airplane_num, flight_number, departure_date, departure_time, card_type, card_number, name_on_card, expiration, base_price, email, purchase_date, purchase_time))
            conn.commit()
            cursor.close()

        return render_template('submitted.html')

@app.route('/roundtripBook', methods=["GET", "POST"])
@role_required('Customer')
def roundtripBook():
    purchase_date = date.today()
    purchase_time = datetime.now().strftime("%H:%M:%S")
    email = session['email']
    print(session)
    card_type = session['card_type']
    card_number = session['card_number']
    name_on_card = session['name_on_card']
    expiration = session['expiration']

    airline_name = request.form['airline_name']
    unique_airplane_num = request.form['unique_airplane_num']
    flight_number = request.form['flight_number']
    departure_date = request.form['departure_date']
    departure_time = request.form['departure_time']
    base_price = request.form['base_price']

    prev_airline_name = session['prev_airline_name']
    prev_unique_airplane_num = session['prev_unique_airplane_num']
    prev_flight_number = session['prev_flight_number']
    prev_departure_date = session['prev_departure_date']
    prev_departure_time = session['prev_departure_time']
    prev_base_price = session['prev_base_price']
    
    cursor = conn.cursor()
    ticket_id_1 = generate_ticket_id()
    data1 = unique_flight(prev_airline_name, prev_unique_airplane_num, prev_flight_number, prev_departure_date, prev_departure_time)
    # print("really")
    # print(card_type)

    if (data1):  
        prev_base_price = price_modify(prev_airline_name, prev_unique_airplane_num, prev_flight_number, prev_departure_date, prev_departure_time, prev_base_price)
        query = 'INSERT into ticket Values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
        cursor.execute(query, (ticket_id_1, prev_airline_name, prev_unique_airplane_num, prev_flight_number, prev_departure_date, prev_departure_time, card_type, card_number, name_on_card, expiration, prev_base_price, email, purchase_date, purchase_time))
        conn.commit()

    ticket_id_2 = generate_ticket_id()
    data2 = unique_flight(airline_name, unique_airplane_num, flight_number, departure_date, departure_time)

    if (data2):  
        base_price = price_modify(airline_name, unique_airplane_num, flight_number, departure_date, departure_time, base_price)
        query = 'INSERT into ticket Values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
        cursor.execute(query, (ticket_id_2, airline_name, unique_airplane_num, flight_number, departure_date, departure_time, card_type, card_number, name_on_card, expiration, base_price, email, purchase_date, purchase_time))
        conn.commit()

    cursor.close()
    return render_template('submitted.html')



@app.route('/cancelTicket', methods=["GET", "POST"])
def cancelTicket():
    cursor = conn.cursor()
    email = session['email']
    ticket_id = int(float(request.form['ticket_id']))

    #check that the ticket_id is in your email so you can't delete someone elses ticket
    query = 'SELECT * from ticket where email = %s and ticket_id = %s'
    cursor.execute(query, (email, ticket_id))
    data = cursor.fetchone()
    print(ticket_id)

    if (data):
        query = 'DELETE from ticket where ticket.ticket_id = %s' # only works temporarily? a bit strange 
        cursor.execute(query, (ticket_id))
        conn.commit()

    cursor.close()
    return render_template('submitted.html')

@app.route('/spending')
@role_required("Customer")
def spending_default():
    email = session['email']
    start_date = datetime(2022, 6, 3)
    end_date = datetime(2022, 12, 3)
    table_info, total_spending = calculate_spending(email, start_date, end_date)
    return render_template('spending.html', table_info=table_info, total=total_spending)

@app.route('/spendSpecify', methods=["POST"])
@role_required("Customer")
def spending_specify():
    email = session['email']
    start_year, start_month, start_day  = request.form['start'].split("-") 
    start_date = datetime(int(start_year), int(start_month), int(start_day))
    end_year, end_month, end_day  = request.form['end'].split("-") 
    end_date = datetime(int(end_year), int(end_month), int(end_day))

    table_info, total_spending = calculate_spending(email, start_date, end_date)
    return render_template('spending.html', table_info=table_info, total=total_spending)

# @app.route('/Staff/createflight', methods=['POST'])
# @role_required("Staff")
# def createflight():
#     airport = request.form['airport'];
#     # airport = request.form[]

