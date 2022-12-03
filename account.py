from __main__ import app, render_template, request, session, url_for, redirect, conn
import pymysql.cursors
import hashlib
import sys
from helperFuncs import *


# Decorator to ensure routes can only be accessed
# With correct credentials
def login_required(func, login_state):
    def check():
        if login_state == "Customer":
            if "email" in session:
                return func();
        elif login_state == "Staff":
            if "username" in session:
                return func();
        else:
            return redirect("/login");


@app.route('/myaccount')
def myaccount():
	if "email" in session:
		return redirect('/Customers/customer')
	elif "username" in session:
		return redirect('/Staff/staff')

@app.route('/Staff/staff')
def staff():
    airports = get_airports();
    return render_template("Staff/staff.html", airports = airports);

@app.route('/Customers/customer')
def customer():
    return render_template("Customers/customer.html");


@app.route('/Staff/createflight', methods=['POST'])
def createflight():
    airport = request.form['airport'];
    # airport = request.form[]
