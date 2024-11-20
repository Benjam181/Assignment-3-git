#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask, session, redirect, request, jsonify, url_for, render_template
import sqlite3
import os
from werkzeug.security import check_password_hash, generate_password_hash
import configparser


app = Flask(__name__)

# Initialize ConfigParser
config = configparser.ConfigParser()
config.read('../config.ini')

app.secret_key = config['FLASK']['secret_key']

# Define the path to your SQLite database
DATABASE_PATH = os.path.join(os.path.dirname(__file__), '../Temperature_sql_database.db')

def ReadFile(path):
    # Attention : il faut bien mettre "rb" plutôt que "r", sinon
    # l'UTF-8 ne fonctionne pas sous Windows.
    with open(path, 'rb') as f:
        return f.read()

# Function to connect to the SQLite database
def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    return conn

@app.route('/')
def redirection():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    return render_template('graph.html')

# Route for the login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        
        if user and password == user['password']:  # Comparison of password
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('index'))
        else:
            return "Wrong Username or Password", 401
    
    return render_template('login.html')

@app.route('/index.html')
def index():
    if 'user_id' not in session:
            return redirect(url_for('login'))
    return ReadFile('templates/graph.html')

# Route to fetch data from a table
@app.route('/api/graph_data', methods=['GET'])
def get_graph_data():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    # Get the date params from the request
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')

    conn = get_db_connection()
    cursor = conn.cursor()

    # if the time parameters are given, filter the data
    if start_time and end_time:
        query = """
            SELECT time, temperature, output, target
            FROM airHeater 
            WHERE time BETWEEN ? AND ?
            ORDER BY time
        """
        cursor.execute(query, (start_time, end_time))
    else:
        # else, get all the data
        query = "SELECT time, temperature, output, target FROM airHeater ORDER BY time"
        cursor.execute(query)
        
    rows = cursor.fetchall()
    conn.close()

    # Transform the data into dictionnaire to send the data in json 
    data = {
        "time": [row["time"] for row in rows],
        "temperature": [row["temperature"] for row in rows],
        "output": [row["output"] for row in rows],
        "reference": [row["target"] for row in rows]
    }

    return jsonify(data)

# Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))
    
if __name__ == '__main__':
    app.run(debug=True)