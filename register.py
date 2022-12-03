from __main__ import app, render_template, request, session, url_for, redirect, conn
import pymysql.cursors
import hashlib
import sys
#Define route for login
@app.route('/login')
def login():
	return render_template('LoginAuth/login.html')

#Define route for register
@app.route('/signup')
def signup():
	return render_template('LoginAuth/signup.html')

@app.route('/userSignUp')
def userSignUp():
	return render_template('LoginAuth/userSignUp.html')

@app.route('/staffSignUp')
def staffSignUp():
	return render_template('LoginAuth/staffSignUp.html')

#Authenticates the login
@app.route('/loginAuth', methods=['GET', 'POST'])
def loginAuth():
	#grabs information from the forms
	email = request.form['email']
	password = request.form['password']#.md5()
	hashed_password = hashlib.md5(password.encode())

	#cursor used to send queries
	cursor = conn.cursor()
	#executes query
	query = 'SELECT * FROM customers WHERE email = %s and password = %s'
	cursor.execute(query, (email, password))
	#stores the results in a variable
	data = cursor.fetchone()
	#use fetchall() if you are expecting more than 1 data row
	cursor.close()
	error = None
	if (data):
		#creates a session for the the user
		#session is a built in
		session['email'] = email
		return redirect('/')
	else:
		#returns an error message to the html page
		error = 'Invalid login or username'
		return render_template('LoginAuth/login.html', error=error)

#Authenticates the user register
@app.route('/userRegisterAuth', methods=['GET', 'POST'])
def registerUserAuth():
	#grabs information from the forms
	username = request.form['username']
	password = request.form['password']
	# hashed_password = hashlib.md5(password.encode())

	#cursor used to send queries
	cursor = conn.cursor()
	#executes query
	query = 'SELECT * FROM customers WHERE email = %s'
	cursor.execute(query, (username))
	#stores the results in a variable
	data = cursor.fetchone()
	#use fetchall() if you are expecting more than 1 data row
	error = None
	if (data):
		#If the previous query returns data, then user exists
		error = "This user already exists"
		return render_template('LoginAuth/userSignUp.html', error = error)
	else:
		return render_template('index.html')
		ins = 'INSERT INTO customers VALUES(%s, %s)'
		cursor.execute(ins, (username, hashed_password))
		conn.commit()
		cursor.close()
		return render_template('index.html')

#Authenticates the Staff register
@app.route('/staffRegisterAuth', methods=['GET', 'POST'])
def registerStaffAuth():
	#grabs information from the forms
	username = request.form['username']
	password = request.form['password']
	airline = request.form['airline']
	firstName = request.form['first name']
	lastName = request.form['last name']
	bday = request.form['bday']
	
	# hashed_password = hashlib.md5(password.encode())

	#cursor used to send queries
	cursor = conn.cursor()
	#executes query
	query = 'SELECT * FROM airlinestaff WHERE username = %s'
	cursor.execute(query, (username))
	
	#stores the results in a variable
	userData = cursor.fetchone()
	#use fetchall() if you are expecting more than 1 data row
	error = None
	query = 'SELECT * FROM airline WHERE airline_name = %s'
	cursor.execute(query, (airline))
	airlineData = cursor.fetchone() 
	if (userData):
		#If the previous query returns data, then user exists
		error = "This user already exists"
		return render_template('LoginAuth/staffSignUp.html', error = error)
	if(not airlineData): 
		error = "Invalid Airline"
		return render_template('LoginAuth/staffSignUp.html', error = error)
	else:
		return render_template('index.html')
		ins = 'INSERT INTO customers VALUES(%s, %s)'
		cursor.execute(ins, (username, hashed_password))
		conn.commit()
		cursor.close()
		return render_template('index.html')


@app.route('/logout')
def logout():	
    if not session.email:
        session.pop('email')
    elif not session.username:
        session.pop('username')
    
    return redirect('/')