import os
from flask import Flask, render_template, request, redirect, send_from_directory, session, url_for, flash
from werkzeug.utils import secure_filename
from flask_mysqldb import MySQL

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Nani@1234'
app.config['MYSQL_DB'] = 'nikil'

mysql = MySQL(app)

# ...
UPLOAD_FOLDER = 'uploads'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route('/')
def index():
    if 'username' in session:
        return render_template('index.html')
    return redirect(url_for('register'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        # Create a MySQL cursor
        cur = mysql.connection.cursor()

        # Execute a query to check if the username is already taken
        cur.execute("SELECT * FROM registration WHERE username = %s", (username,))
        existing_user = cur.fetchone()

        if existing_user:
            error_message = "Username already exists. Please choose a different one."
            cur.close()
            return render_template('register.html', error=error_message)

        cur.execute("INSERT INTO registration (username, password, email) VALUES (%s, %s, %s)", (username, password, email))

        mysql.connection.commit()
        cur.close()

        return redirect(url_for('login')) 

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Create a MySQL cursor
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM registration WHERE username = %s AND password = %s", (username, password))

        # Fetch the result
        user = cur.fetchone()

        # Close the cursor
        cur.close()

        if user:
            session['username'] = username
            return redirect(url_for('layout'))
        else:
            error_message = "Invalid username or password. Please try again."
            return render_template('login.html', error=error_message)
    return render_template('login.html')


@app.route('/')
def layout():
    return render_template('layout.html')
@app.route('/add_contact', methods=['GET', 'POST'])
def add_contact():
    if request.method == 'POST':
        # Get form data including the uploaded image
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        phone_number = request.form['phone_number']
        
        # Handle image upload
        image = request.files['image']
        if image:
            # Securely save the image file with a unique name
            filename = secure_filename(image.filename)
            image.save('uploads/' + filename)
            image_url = url_for('uploaded_file', filename=filename)
        else:
            image_url = None

        # Insert the data into the database
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO contacts (first_name, last_name, email, phone_number, image) VALUES (%s, %s, %s, %s, %s)",
                    (first_name, last_name, email, phone_number, image_url))
        mysql.connection.commit()
        cur.close()

        
        return redirect(url_for('view_contacts'))

    return render_template('add_contact.html')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory('uploads', filename)


@app.route('/view_contacts')
def view_contacts():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, first_name, last_name, email, image FROM contacts")
    contacts = [{'id': row[0], 'first_name': row[1], 'last_name': row[2], 'email': row[3], 'image': row[4]} for row in cur.fetchall()]
    cur.close()

    return render_template('view_contacts.html', contacts=contacts)


@app.route('/view_contact/<int:id>')
def view_contact(id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM contacts WHERE id = %s", (id,))
    contact = cur.fetchone()
    cur.close()

    if contact:
        print("Contact data retrieved successfully:", contact)
        return render_template('view_contact.html', contact=contact)
    else:
        print("Contact data not found")
        return render_template('error.html')

@app.route('/edit_contact/<int:id>', methods=['GET', 'POST'])
def edit_contact(id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM contacts WHERE id = %s", (id,))
    contact_tuple = cur.fetchone()
    
    if contact_tuple:
        # Convert the contact tuple to a dictionary
        contact = {
            'id': contact_tuple[0],
            'first_name': contact_tuple[1],
            'last_name': contact_tuple[2],
            'email': contact_tuple[3],
            'phone_number': contact_tuple[4],
            'image': contact_tuple[5]
        }

        # Initialize the image variable
        image = None

        if request.method == 'POST':
            # Process the form data here and update the contact in the database
            first_name = request.form['first_name']
            last_name = request.form['last_name']
            email = request.form['email']
            phone_number = request.form['phone_number']

            # Handle image update
            image = request.files['image']
            if image:
                # Securely save the image file with a unique name
                filename = secure_filename(image.filename)
                image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                image_url = url_for('uploaded_file', filename=filename)
                # Update the image URL in the database
                cur.execute("UPDATE contacts SET first_name=%s, last_name=%s, email=%s, phone_number=%s, image=%s WHERE id=%s",
                            (first_name, last_name, email, phone_number, image_url, contact['id']))
            else:
                # No new image provided, update other fields only
                cur.execute("UPDATE contacts SET first_name=%s, last_name=%s, email=%s, phone_number=%s WHERE id=%s",
                            (first_name, last_name, email, phone_number, contact['id']))
            mysql.connection.commit()
            cur.close()

            flash('Contact updated successfully', 'success')
            return redirect(url_for('view_contacts'))

        return render_template('edit_contact.html', contact=contact, image=image)
    else:
        flash('Contact not found', 'danger')
        return redirect(url_for('view_contacts'))



@app.route('/delete_contact/<int:id>', methods=['GET', 'POST'])
def delete_contact(id):
    if request.method == 'POST':
        # Perform the actual deletion of the contact
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM contacts WHERE id = %s", (id,))
        mysql.connection.commit()
        cur.close()
        
        flash('Contact deleted successfully', 'success')
        return redirect(url_for('view_contacts'))
    
    # If it's a GET request, display a confirmation page
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM contacts WHERE id = %s", (id,))
    contact_tuple = cur.fetchone()
    cur.close()

    if contact_tuple:
        contact = {
            'id': contact_tuple[0],
            'first_name': contact_tuple[1],
            'last_name': contact_tuple[2],
            'email': contact_tuple[3],
            'phone_number': contact_tuple[4],
            'image': contact_tuple[5]
        }

        return render_template('delete_contact.html', contact=contact)
    else:
        flash('Contact not found', 'danger')
        return redirect(url_for('view_contacts'))


@app.route('/search', methods=['GET'])
def search_contacts():
    query = request.args.get('query')  # Get the search query

    # Define an SQL query to search across all relevant fields
    sql_query = "SELECT id, first_name, image FROM contacts WHERE first_name LIKE %s OR last_name LIKE %s OR phone_number LIKE %s"

    cur = mysql.connection.cursor()
    cur.execute(sql_query, ('%' + query + '%', '%' + query + '%', '%' + query + '%'))
    search_results = [{'id': row[0], 'first_name': row[1], 'image': row[2]} for row in cur.fetchall()]
    cur.close()

    # Check if there are search results
    if not search_results:
        no_results_message = "No contacts found."
        return render_template('view_contacts.html', contacts=[], no_results_message=no_results_message)
    else:
        return render_template('view_contacts.html', contacts=search_results)





if __name__ == '__main__':
    app.secret_key = 'your_secret_key'
    app.run(debug=True)