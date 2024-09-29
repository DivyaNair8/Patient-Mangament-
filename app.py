from flask import Flask, flash, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a strong key

# Function to establish a database connection  
def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host='database-1.c5ks2skiyrb7.us-east-1.rds.amazonaws.com',
            user='admin',
            password='noobdi12',
            database='pm'
        )
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

# Home route
@app.route('/')
def index():
    return render_template('index.html')

# Patient Registration route
@app.route('/patient_registration', methods=['GET', 'POST'])
def patient_registration():
    if request.method == 'POST':
        name = request.form['name']
        gender = request.form['gender']
        phone = request.form['phone']
        dob = request.form['dob']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])

        # Debug prints for form data
        print(f"Name: {name}, Email: {email}, Gender: {gender}, Phone: {phone}, DOB: {dob}")

        db = get_db_connection()
        if db is None:
            flash("Database connection error")
            return redirect(url_for('patient_registration'))

        cursor = db.cursor(dictionary=True)

        try:
            cursor.execute(
                "INSERT INTO patients (PatientName, Gender, PhoneNumber, DateOfBirth, Email, Password) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                (name, gender, phone, dob, email, password)
            )
            db.commit()

            # Check if the insert was successful
            if cursor.rowcount == 1:
                print("User successfully registered!")  # Debug print for successful registration
                flash('Thanks for registering! Please log in.')  # Display flash message
                return redirect(url_for('login'))  # Redirect to login page after successful registration
            else:
                flash("Registration failed. Please try again.")
                print("Registration failed, no rows were inserted.")  # Debugging info
        except mysql.connector.Error as err:
            flash(f"Database error: {err}")
            print(f"Database error occurred: {err}")  # Debug print for error logging
        except Exception as e:
            flash(f"Unexpected error: {e}")
            print(f"Unexpected error occurred: {e}")  # Debugging for unexpected errors
        finally:
            cursor.close()
            db.close()

    return render_template('patient_registration.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        db = get_db_connection()
        if db is None:
            flash("Database connection error")
            return redirect(url_for('login'))

        cursor = db.cursor(dictionary=True)

        try:
            cursor.execute("SELECT * FROM patients WHERE Email = %s", (email,))
            user = cursor.fetchone()

            if user and check_password_hash(user['Password'], password):
                session['user_id'] = user['PatientID']
                session['user_name'] = user['PatientName']
                return redirect(url_for('dashboard'))  # Redirect to dashboard after successful login
            else:
                flash('Invalid email or password')
        except mysql.connector.Error as err:
            flash(f"Database error: {err}")
        finally:
            cursor.close()
            db.close()

    return render_template('login.html')

# Dashboard route
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', user_name=session['user_name'])

# Appointment Booking route
@app.route('/book_appointment', methods=['GET', 'POST'])
def book_appointment():
    if 'user_id' not in session:
        return redirect(url_for('login'))  # Ensure user is logged in

    if request.method == 'POST':
        specialization = request.form.get('specialization')
        appointment_date = request.form.get('appointment_date')
        reason = request.form.get('reason')

        db = get_db_connection()
        if db is None:
            flash("Database connection error")
            return redirect(url_for('book_appointment'))

        cursor = db.cursor(dictionary=True)

        try:
            cursor.execute(
                "INSERT INTO Appointments (PatientID, Specialization, Reason, AppointmentDate) "
                "VALUES (%s, %s, %s, %s)",
                (session['user_id'], specialization, reason, appointment_date)
            )
            db.commit()
            flash("Your appointment has been booked!")
            return redirect(url_for('dashboard'))  # Redirect back to dashboard after booking
        except mysql.connector.Error as err:
            flash(f"Error: {err}")
        finally:
            cursor.close()
            db.close()

    # Render the form for GET request
    specializations = ['Cardiology', 'Dermatology', 'Neurology']
    return render_template('book_appointment.html', specializations=specializations)


# Patient Records route
@app.route('/patient_records')
def patient_records():
    if 'user_id' not in session:
        return redirect(url_for('login'))  # Ensure user is logged in

    db = get_db_connection()
    if db is None:
        flash("Database connection error")
        return redirect(url_for('dashboard'))

    cursor = db.cursor(dictionary=True)

    try:
        # Fetch patient info
        cursor.execute("""
            SELECT PatientID, PatientName AS name, PhoneNumber AS contact_info, Email
            FROM patients
            WHERE PatientID = %s
        """, (session['user_id'],))
        patient_info = cursor.fetchone()

        if not patient_info:
            flash("No patient information found")
            return redirect(url_for('dashboard'))

        # Fetch appointment details
        cursor.execute("""
            SELECT Specialization, AppointmentDate AS appointment_date, Reason
            FROM Appointments
            WHERE PatientID = %s
        """, (session['user_id'],))
        appointments = cursor.fetchall()

    except mysql.connector.Error as err:
        flash(f"Database error: {err}")
        return redirect(url_for('dashboard'))
    finally:
        cursor.close()
        db.close()

    return render_template('patient_records.html', patient_info=patient_info, appointments=appointments)

# Logout route
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)