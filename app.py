import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import mysql.connector
from werkzeug.utils import secure_filename
import os
import random
from flask_mail import Message, Mail
import uuid
from werkzeug.security import generate_password_hash, check_password_hash







from chat import get_response

app = Flask(__name__)


# configure mail settings
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'ctquia-eo.ccit@unp.edu.ph'
app.config['MAIL_PASSWORD'] = ''

mail = Mail(app)  # initialize the mail object
# Set the secret key for the session
app.secret_key = 'mysecretkey'





# Database connection configuration
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="chatbot"
)


@app.route('/')
def home():
    # Clear the session when the user lands on the home page
    session.clear()
    return render_template('login.html')


@app.route('/chatbot')
def chatbot():
    # Check if the user is logged in
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    # Retrieve the user's email from the session
    email = session['email']

    # Retrieve the conversations from the database for the logged-in user
    cursor = db.cursor()
    query = "SELECT user_query, bot_response FROM conversations WHERE email=%s"
    cursor.execute(query, (email,))
    conversations = cursor.fetchall()
    cursor.close()

  
    return render_template('base.html', conversations=conversations)

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    # Check the user's credentials against the database
    cursor = db.cursor()
    query = "SELECT * FROM user_credentials WHERE username=%s"
    cursor.execute(query, (username,))
    user = cursor.fetchone()
    cursor.close()

    # If the user doesn't exist in the database, show an error message
    if user is None:
        error = 'Invalid username or password'
        return render_template('login.html', error=error)

    # If the user exists, verify the entered password against the hashed password
    hashed_password = user[4]
    print(f"Entered password: {password}")
    print(f"Stored hash: {hashed_password}")
    if not check_password_hash(hashed_password, password):
        error = 'Invalid username or password'
        return render_template('login.html', error=error)

    # If the passwords match, set the session to indicate that the user is logged in and redirect to the chatbot UI
    session['logged_in'] = True

    # Add the user's email to the session
    session['email'] = user[2]
    session['full_name'] = user[1]

    return redirect(url_for('chatbot'))
    

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form['full_name']
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if full_name and email and password and confirm_password:
            # check if email already exists
            cursor = db.cursor()
            query = "SELECT * FROM user_credentials WHERE email=%s"
            cursor.execute(query, (email,))
            user = cursor.fetchone()

            if user is not None:
                cursor.close()
                return render_template('login.html', error='Email already exists')

            # generate a unique identifier
            identifier = str(uuid.uuid4())

            # send verification email
            verify_link = f"{request.host_url}verify_email/{identifier}"
            msg = Message('Email Verification', sender='your_email@example.com', recipients=[email])
            msg.body = f"Please click the following link to verify your email address: {verify_link}."
            mail.send(msg)

            # save user data to session
            session['full_name'] = full_name
            session['email'] = email
            session['username'] = username
            session['password'] = generate_password_hash(password)
            session['verification_id'] = identifier

            # insert verification id into database
            insert_query = "INSERT INTO user_credentials (email, verification_id) VALUES (%s, %s)"
            cursor.execute(insert_query, (email, identifier))
            db.commit()

            cursor.close()

            # render the success page
            return render_template('login.html', error='Verification link sent to your email')

        else:
            return render_template('login.html', error='Please fill out all fields')

    return render_template('login.html')

@app.route('/verify_email/<identifier>')
def verify_email(identifier):
    cursor = db.cursor()
    query = "SELECT * FROM user_credentials WHERE verification_id=%s"
    cursor.execute(query, (identifier,))
    user = cursor.fetchone()

    if user is not None:
        # update user credentials in the same row where email is located
        update_query = "UPDATE user_credentials SET full_name=%s, username=%s, password=%s, verification_id=NULL, verified=true WHERE email=%s"
        cursor.execute(update_query, (session['full_name'], session['username'], session['password'], session['email']))

        db.commit()

        # clear session data
        session.pop('full_name', None)
        session.pop('email', None)
        session.pop('username', None)
        session.pop('password', None)
        session.pop('verification_id', None)

        cursor.close()
        return render_template('login.html', error='Email verified. You can now login.')

    else:
        cursor.close()
        return render_template('login.html', error='Invalid verification link.')



@app.route('/feedback', methods=['GET', 'POST'])
def feedback():

# Check if the user is logged in
    if 'email' not in session:
        # If the user is not logged in, redirect them to the login page
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        # Get the feedback message from the form data
        feedback_message = request.form['feedback_message']
        feedback_category = request.form['feedback_category']
        # Get the email address of the logged-in user
        email = session.get('email')
        
        # Insert the feedback message into the database
        cursor = db.cursor()
        query = "INSERT INTO feedback (email, message) VALUES (%s, %s)"
        values = (email, feedback_message)
        cursor.execute(query, values)
        db.commit()
        cursor.close()
        
        
        # Send email to ctquia-eo.ccit@unp.edu.ph
        msg = Message('Feedback from ' + email, sender=app.config['MAIL_USERNAME'], recipients=['ctquia-eo.ccit@unp.edu.ph'])
        msg.html = "<h3>Email: " + email + "</h3><h3>Category: " + feedback_category + "</h3><p>" + feedback_message + "</p>"
        mail.send(msg)
        
        # Show a success message to the user
        success_message = "Thank you for your feedback!"
        return render_template('feedback.html', success_message=success_message)
    
    # If the request method is GET, show the feedback form
    return render_template('feedback.html')


    

@app.post("/predict")
def predict():
    message = request.get_json().get("message")

    # Call the get_response() function to get the chatbot's response
    response = get_response(message)

    # Insert the conversation into the database
    if session.get('email'):
        email = session['email']
        cursor = db.cursor()
        query = "INSERT INTO conversations (email, user_query, bot_response) VALUES (%s, %s, %s)"
        values = (email, message, response)
        cursor.execute(query, values)
        db.commit()
        cursor.close()

    # Prepare the response to be sent back to the client
    response_data = {"answer": response}

    return jsonify(response_data)



@app.route('/logout', methods=['GET', 'POST'])
def logout():
    # Clear the session
    session.clear()
    # Redirect to the home page
    return redirect(url_for('home'))


@app.route('/forgotpass')
def forgotpass():
   
    # Redirect to the home page
    return render_template('forgotpassword.html')





@app.route('/loginpage')
def loginpage():
   
    # Redirect to the home page
    return render_template('login.html')


@app.route('/university_map')
def university_map():
    if not session.get('logged_in'):
        return redirect(url_for('home'))
    # Redirect to the university map
    return render_template('university_map.html')



@app.route('/chatbox')
def chatbox():
    if not session.get('logged_in'):
        return redirect(url_for('home'))
    return render_template('base.html')



@app.route('/', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        if email:
            cursor = db.cursor()
            query = "SELECT * FROM user_credentials WHERE email=%s"
            cursor.execute(query, (email,))
            user = cursor.fetchone()

            if user is not None:
                identifier = str(uuid.uuid4())
                verification_code = str(random.randint(100000, 999999))
                update_query = "UPDATE user_credentials SET reset_password_id=%s, verification_code=%s WHERE email=%s"
                cursor.execute(update_query, (identifier, verification_code, email))
                db.commit()

                reset_link = f"{request.host_url}reset_password/{identifier}"
                msg = Message('Password Reset Request', sender='ctquia-eo.ccit@unp.edu.ph', recipients=[email])
                msg.body = f"Please click the following link to reset your password: {reset_link}. Your verification code is {verification_code}."
                mail.send(msg)

                return render_template('forgotpassword.html', email=email, show_verification=True)

            else:
                cursor.close()
                return render_template('forgotpassword.html', error='Email not found')

        elif 'code' in request.form:
            code = request.form['code']
            email = request.form['email']
            cursor = db.cursor()
            query = "SELECT * FROM user_credentials WHERE email=%s AND verification_code=%s"
            cursor.execute(query, (email, code,))
            user = cursor.fetchone()

            if user is not None:
                cursor.close()
                return render_template('resetpassword.html', email=email)

            else:
                cursor.close()
                return render_template('forgotpassword.html', email=email, show_verification=True, error='Invalid verification code')

        else:
            return render_template('forgotpassword.html', error='Please enter a valid email address')

    return render_template('forgotpassword.html')



      




@app.route('/reset_password/<identifier>', methods=['GET', 'POST'])
def reset_password(identifier):
    if request.method == 'POST':
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        # check if new password is same as old password
        cursor = db.cursor()
        query = "SELECT * FROM user_credentials WHERE reset_password_id=%s"
        cursor.execute(query, (identifier,))
        user = cursor.fetchone()
        cursor.close()

        if user is None:
            return render_template('enternewpassword.html', error='Invalid reset link')

        if check_password_hash(user[1], password):
            return render_template('enternewpassword.html', password_error='New password cannot be the same as old password')

        # check if password and confirm_password match
        if password != confirm_password:
            return render_template('enternewpassword.html', password_error='Passwords do not match')

        # hash the new password and update the database
        password_hash = generate_password_hash(password)
        cursor = db.cursor()
        query = "UPDATE user_credentials SET password=%s, reset_password_id=NULL WHERE email=%s"
        cursor.execute(query, (password_hash, user[2]))
        db.commit()
        cursor.close()

        return render_template('enternewpassword.html', success='Password successfully updated')

    # check if reset link is valid
    cursor = db.cursor()
    query = "SELECT * FROM user_credentials WHERE reset_password_id=%s"
    cursor.execute(query, (identifier,))
    user = cursor.fetchone()
    cursor.close()

    if user is None:
        return render_template('enternewpassword.html', error='Invalid reset link')

    return render_template('enternewpassword.html')


if __name__ == "__main__":
    app.run(debug=True)
