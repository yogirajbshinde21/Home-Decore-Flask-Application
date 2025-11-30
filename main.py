import os
import threading
# import tkinter as tk  # Not needed for web deployment
from flask import Flask, abort, jsonify, render_template, request, redirect, url_for,session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from werkzeug.utils import secure_filename
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64
import plotly.graph_objects as go
import plotly.io as pio
# import psycopg2
import re 
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file


# os.environ['TCL_LIBRARY'] = r"C:\Users\Yogiraj Shinde\AppData\Local\Programs\Python\Python313\tcl\tcl8.6"
# os.environ['TK_LIBRARY'] = r"C:\Users\Yogiraj Shinde\AppData\Local\Programs\Python\Python313\tcl\tk8.6"


curr_dir = os.path.dirname(os.path.abspath(__file__))


app = Flask(__name__)    #Application instance
app.secret_key = 'secret'  #flash requires a secret key that's why added it.
app.config['PASSWORD_HASH'] = 'sha512'

# Database Configuration
# Use PostgreSQL in production (Render), SQLite for local development
database_url = os.environ.get("DATABASE_URL")
if database_url:
    # Fix for Render's postgres:// URL (SQLAlchemy needs postgresql://)
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    # Local development with SQLite
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///HouseHoldService.sqlite3'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", "secret")  # Use env variable in production

app.config['UPLOAD_EXTENSIONS'] = ['.pdf']
app.config['UPLOAD_FOLDER'] = os.path.join(curr_dir, 'static', "pdfs") 

db = SQLAlchemy()  #Database instance


db.init_app(app)   # To intialize the SQLAlchemy database
app.app_context().push()   #pushing databases into the app_content() function which pushes the databases into the app.


# SQLalchemy is also a ORM (Object Relational Mapping).


    ############### User table ################

class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key = True)
    user_name = db.Column(db.String(80), unique = True, nullable = False)
    password = db.Column(db.String(256), nullable=False)  # Increased length for hash
    address = db.Column(db.String(80), nullable = False)
    pincode = db.Column(db.Integer, nullable = True)
    is_admin = db.Column(db.Boolean, default = False)             #Admin
    is_professional = db.Column(db.Boolean, default = False)  #Contractor
    is_customer = db.Column(db.Boolean, default = False)      #Home Owner
    is_approved = db.Column(db.Boolean, default = False)
    avg_rating = db.Column(db.Float, default = 0.0)
    rating_count = db.Column(db.Integer, default = 0)        
    prof_file = db.Column(db.String(80), nullable = True)     #con_file - stores the location of PDF uploaded by contractor/service professional.
    prof_experience = db.Column(db.String(80), nullable = True)

    #Relationship of user with service : "One service - Many user". 
    # Setting ondelete="CASCADE" ensures that if a service is deleted,
    # then all User entries associated with that service will also have their service_id set to NULL or gets deleted.
    # for e.g. if professional decided to delete his service, then all user entries associated with that service must be deleted.
    service_id  = db.Column(db.Integer, db.ForeignKey('householdServices.id', ondelete = "SET NULL"),nullable=True)   #foreign key from services table.
    # In service_id, why nullable=True, because Admin and Customer cannot have service_id.

    #------------- Relationship -------------#

    # using 'service' to connect with HouseholdServices table. just like JOIN in SQL.
    service = db.relationship('HouseholdServices', back_populates="professional")

    #Relationship for requests that customer made
    customer_requests = db.relationship('HouseholdServiceRequest', back_populates='customer', foreign_keys="HouseholdServiceRequest.customer_id")
    
    #Relationship for requests sent to service professional 
    professional_requests = db.relationship('HouseholdServiceRequest', back_populates='professional', foreign_keys="HouseholdServiceRequest.professional_id")

    def set_password(self, password):
      self.password = generate_password_hash(password)  # Using default method
    
    def check_password(self, password):
        return check_password_hash(self.password, password)

    #This function is for search_professionals.html
    def completed_services(self):
        return HouseholdServiceRequest.query.filter_by(professional_id=self.id, status_of_serviceRequest='completed').all()
    
    #This function is for search_customers.html
    def completed_service_requests(self):
        return HouseholdServiceRequest.query.filter_by(customer_id=self.id, status_of_serviceRequest='completed').all()
    


    ############### HouseholdServices table ################
class HouseholdServices(db.Model):
    __tablename__ = "householdServices"
    id = db.Column(db.Integer, primary_key = True)
    service_name = db.Column(db.String(80), unique=True, nullable = False)
    service_description = db.Column(db.String(80), nullable = True)
    base_price = db.Column(db.Integer, nullable = True)
    time_required = db.Column(db.String(80), nullable = True)

    #Foreign key to connect with Category table.
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable = False)

    #Relationship of service with category : "One category - Many service". 
    category = db.relationship('Categories', back_populates="services")



  #------------- Relationship -------------#
    professional = db.relationship('User', back_populates="service", cascade="all, delete-orphan")
    request = db.relationship("HouseholdServiceRequest", back_populates = "service", cascade="all, delete-orphan") 
    # cascade="all, delete-orphan" means if parent service record (i.e. HouseholdServices) is deleted,
    # then this will allow any associated HouseholdServiceRequest records to be automatically deleted as well.



    ############### HouseholdServiceRequest table ################
class HouseholdServiceRequest(db.Model):
    __tablename__ = 'householdServiceRequest'
    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('householdServices.id'), nullable=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    professional_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    request_type = db.Column(db.String(10), nullable=False)  # public or private
    request_description = db.Column(db.Text, nullable=True)   # Description of the service request
    status_of_serviceRequest = db.Column(db.String(80), nullable=True)  # pending, accepted, completed, rejected
    date_created = db.Column(db.Date, nullable=False, default=datetime.now().date())
    date_closed = db.Column(db.Date, nullable=True)
    rating_by_The_customer = db.Column(db.Float, default=0.0)
    review_by_The_customer = db.Column(db.String(80), nullable=True)

  #------------- Relationship -------------#
    service = db.relationship("HouseholdServices", back_populates = "request")
    customer = db.relationship("User", back_populates = "customer_requests", foreign_keys=[customer_id])
    professional = db.relationship("User", back_populates = "professional_requests", foreign_keys = [professional_id])



    ############### Categories table ################
class Categories(db.Model):
    __tablename__ = "categories"
    id = db.Column(db.Integer, primary_key=True)
    category_name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=True)

    # Relationship with HouseholdServices
    services = db.relationship("HouseholdServices", back_populates="category")







# Creating a function to create an admin user.
def create_admin():
    with app.app_context():
        # First, check if admin exists
        admin_user = User.query.filter_by(is_admin=True).first()
        
        if not admin_user:
            print("Creating new admin user...")
            admin_user = User(
                user_name="admin",
                address="admin address",
                pincode=000000,
                is_admin=True,
                is_approved=True
            )
            # Set password using the new method
            admin_user.set_password("12345678")
            
            db.session.add(admin_user)
            try:
                db.session.commit()
                print("Admin user created successfully")
                # Print the stored hash for debugging
                print(f"Stored password hash: {admin_user.password}")
            except Exception as e:
                db.session.rollback()
                print(f"Error creating admin: {e}")
        else:
            print("Admin user already exists")
            # Update admin's password
            admin_user.set_password("12345678")
            try:
                db.session.commit()
                print("Admin password updated")
                print(f"Updated password hash: {admin_user.password}")
            except Exception as e:
                db.session.rollback()
                print(f"Error updating admin: {e}")

with app.app_context():
  db.create_all()    #Creates all tables in the database based on the above defined models, if they don't already exists.
  create_admin()


@app.route("/", methods = ['GET'])
def home():
  return render_template("index.html")

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(user_name=username).first()
        
        if user:  # Check if user exists first
            if not user.check_password(password):
                flash("Invalid password!", "danger")
                return render_template("login.html", username=username)
            
            # Check if the user is a customer and if they are approved
            if user.is_customer and not user.is_approved:
                flash("Your account has been blocked. Please contact support.", "danger")
                return render_template("login.html", username=username)

            # Username exists and password is correct
            session['username'] = username
            session['user_id'] = user.id
            session['is_professional'] = user.is_professional
            session['is_customer'] = user.is_customer
            
            if user.is_customer:
                flash("Login successful!", "success")
                return redirect(url_for("customer_dashboard"))
            
            if user.is_professional:
                if not user.is_approved:
                    flash("Your account is blocked or not approved yet. Please wait for approval.", "danger")
                    return redirect(url_for("login"))
                
                if user.service_id is None:
                    flash("Your requested service is unavailable. Please create a new account with a different service option.", "danger")
                    return redirect(url_for("login"))
                
                return redirect(url_for("professional_dashboard"))
        
        # If user does not exist
        flash("Username does not exist!", "danger")
        return render_template("login.html")
    
    # GET request, render login page normally
    return render_template("login.html")


@app.route("/admin_login_page", methods=['GET', 'POST'])
def admin_login():
    if request.method == "POST":
        username = request.form['admin_username']
        password = request.form['admin_password']
        
        print(f"Login attempt for username: {username}")
        
        admin = User.query.filter_by(is_admin=True, user_name=username).first()
        
        if admin:
            print("Admin user found in database")
            print(f"Stored hash in database: {admin.password}")
            
            if admin.check_password(password):
                print("Password verified successfully")
                session['username'] = username
                session['is_admin'] = True
                session['user_id'] = admin.id  # Also store user_id in session
                flash("Login successful!", "success")
                return redirect(url_for("admin_dashboard"))
            else:
                print(f"Password verification failed for input: {password}")
                flash("Invalid password!", "danger")
        else:
            print("Admin user not found")
            flash("Invalid username!", "danger")
        
    return render_template("admin_login.html")

# Used the below code for reseting entire database to fix the issue of hash password not working properly for admin_login.html page.
# def reset_database():
#     with app.app_context():
#         print("Dropping all tables...")
#         db.drop_all()
#         print("Creating all tables...")
#         db.create_all()
#         print("Creating admin user...")
#         create_admin()


@app.route("/professional_register", methods=['GET', 'POST'])
def professional_register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        address = request.form['address']
        pincode = request.form['pincode']
        service = request.form['service']  # Get the selected service
        prof_experience = request.form['prof_experience']
        prof_file = request.files['prof_file']
        
        # Fetch the service ID based on the selected service name
        service_id = HouseholdServices.query.filter_by(service_name=service).first().id
        final_file = secure_filename(prof_file.filename)

        user = User.query.filter_by(user_name=username).first()
        if user:  # If user (i.e., username) exists, then flash this below message.
            flash("User  already exists. Please try another name.", 'danger')
            return redirect("/professional_register")
        
        if final_file != "":
            file_extension = os.path.splitext(final_file)[1]
            newly_renamed_file = username + file_extension
            if file_extension not in app.config['UPLOAD_EXTENSIONS']:
                flash("Invalid file format. Please upload in PDF file.", 'danger')
                abort(400)
            prof_file.save(os.path.join(app.config['UPLOAD_FOLDER'], newly_renamed_file))

        # If user doesn't exist already then...
        new_User = User(
            user_name=username,
            address=address,
            pincode=pincode,
            is_professional=True,
            service_id=service_id,
            prof_file=newly_renamed_file,
            prof_experience=prof_experience
        )
        new_User.set_password(password)  # Hash the password
        db.session.add(new_User)
        db.session.commit()
        flash("Registration successful. Please login.", "success")
        return redirect(url_for("login"))

    # GET request: Fetch all services to display in the dropdown
    services = HouseholdServices.query.all()
    return render_template("professional_register.html", services=services)

@app.route("/customer_register", methods = ['GET', 'POST'])
def customer_register():
  if request.method == 'POST':
    username = request.form['username']
    password = request.form['password']
    address = request.form['address']
    pincode = request.form['pincode']

    user = User.query.filter_by(user_name = username).first()
    if user:    #if user (i.e. username) exists, then flash this below message.
      flash("User already exists. Please try another name.", 'danger')
      return redirect("/customer_register")
    # If user doesn't exist already then...


    # def validate_password(password):
    #  password = str(password)
    #  if len(password>8):
    #   for i in password:
    #     if not len(i.upper())<1:
    #         return False
    #     elif not len(i.lower())<1:
    #         return False
    #     else:
    #         return True
    #  else:
    #     flash("Incorrect password format.")
    #     return render_template("customer_register.html")
    
    # if not validate_password(password):
    #     flash("Incorrect password format.")
    #     return render_template("customer_register.html")
    
        # if not re.match(r"[A-Z]", password)
    # if len(password)<8:
    #     re.match(r"[a-z]")

    def validate_password(password):
        if len(password)<8:
            return False
        if not re.search("[a-z]", password):
            return False
        if not re.search("[A-Z]", password):
            return False
        if not re.search("[0-9]", password):
            return False
        return True
    
    if not validate_password(password):
        flash("Incorrect password format.", "danger")
        return render_template("customer_register.html")
    
    new_User = User(user_name=username, address=address, pincode=pincode, is_customer = True, is_approved= True)
    new_User.set_password(password)
    db.session.add(new_User)
    db.session.commit()
    flash("Registration successful. Please login.", "success")
    return redirect(url_for("login"))

  return render_template("customer_register.html")

@app.route("/admin_dashboard", methods=['GET', 'POST'])
def admin_dashboard():
    if 'username' not in session or not session.get('is_admin'):   #or condition may get error due to first condition - check it 
        flash("Please login as admin first!", "danger")
        return redirect(url_for('admin_login'))
    services = HouseholdServices.query.all()
    requests = HouseholdServiceRequest.query.all()
    unapproved_professionals = User.query.filter_by(is_professional = True, is_approved = False).all()

    #Count the total number of service requests
    total_requests = HouseholdServiceRequest.query.count()

    #Count the total number of categories
    total_categories = Categories.query.count()
    return render_template("admin_dashboard.html", unapproved_professionals = unapproved_professionals, services = services, requests = requests, total_categories = total_categories, total_requests = total_requests, admin_name=session['username'])



@app.route("/admin_dashboard/admin_availableService", methods=['GET'])
def admin_availableService():
    if 'username' not in session or not session.get('is_admin'):
        flash("Please login as admin first!", "danger")
        return redirect(url_for('admin_login'))
    
    # Fetch the latest services and categories from the database
    services = HouseholdServices.query.all()
    categories = Categories.query.all()

    # To get count of professionals in each service
    for service in services:
        service.professionals_count = User.query.filter_by(service_id=service.id, is_professional = True, is_approved = True).count()
    return render_template("admin_availableService.html", services=services, categories=categories)


@app.route("/admin_dashboard/admin_add_service", methods=['GET', 'POST'])
def admin_add_service():
    if 'username' not in session or not session.get('is_admin'):
        flash("Please login as admin first!", "danger")
        return redirect(url_for('admin_login'))
    
    if request.method == 'POST':
        service_name = request.form['service_name']
        service_description = request.form['service_description']
        base_price = request.form.get("base_price")
        time_required = request.form.get("time_required")
        category_id = request.form.get("category_id")
        
        the_new_service = HouseholdServices(
            service_name=service_name,
            service_description=service_description,
            base_price=base_price,
            time_required=time_required,
            category_id=category_id
        )
        db.session.add(the_new_service)
        db.session.commit()
        flash("Service added successfully!", "success")
        
        # Redirect to the available services page
        return redirect(url_for('admin_availableService'))
    
    # Get all categories to populate the dropdown
    categories = Categories.query.all()
    return render_template("admin_add_service.html", categories=categories)


@app.route("/admin_dashboard/admin_add_category", methods=['GET', 'POST'])
def admin_add_category():
    if 'username' not in session or not session.get('is_admin'):
        flash("Please login as admin first!", "danger")
        return redirect(url_for('admin_login'))
    
    if request.method == 'POST':
        category_name = request.form['category_name']
        description = request.form.get("description")
        
        the_new_category = Categories(category_name=category_name, description=description)
        db.session.add(the_new_category)
        db.session.commit()
        flash("Category added successfully!", "success")
        
        # Redirect to the available services page
        return redirect(url_for('admin_availableService'))
    
    return render_template("admin_add_category.html")


@app.route("/admin_dashboard/edit_category/<int:category_id>", methods=["GET", "POST"])
def edit_category(category_id):
    if 'username' not in session or not session.get('is_admin'):
        flash("Please login as admin first!", "danger")
        return redirect(url_for('admin_login'))
    
    category = Categories.query.get_or_404(category_id)
    
    if request.method == "POST":
        category.category_name = request.form.get("category_name")
        category.description = request.form.get("description")
        
        try:
            db.session.commit()
            flash("Category updated successfully!", "success")
        except Exception as e:
            db.session.rollback()
            flash("Error updating category. Please try again.", "danger")
        
        return redirect(url_for('admin_availableService'))
    
    return render_template("admin_edit_category.html", category=category)


@app.route("/admin_dashboard/delete_category/<int:category_id>", methods=["POST"])
def delete_category(category_id):
    if 'username' not in session or not session.get('is_admin'):
        flash("Please login as admin first!", "danger")
        return redirect(url_for('admin_login'))
    
    category = Categories.query.get_or_404(category_id)
    
    # Check if there are any services associated with this category
    if category.services:
        flash("Cannot delete category that has services associated with it. Please delete or reassign the services first.", "danger")
        return redirect(url_for('admin_availableService'))
    
    try:
        db.session.delete(category)
        db.session.commit()
        flash("Category deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash("Error deleting category. Please try again.", "danger")
    
    return redirect(url_for('admin_availableService'))


@app.route("/admin_dashboard/edit_service/<int:service_id>", methods=["GET", "POST"])
def edit_service(service_id):
    if 'username' not in session or not session.get('is_admin'):
        flash("Please login as admin first!", "danger")
        return redirect(url_for('admin_login'))
    
    service = HouseholdServices.query.get_or_404(service_id)
    
    if request.method == "POST":
        service.service_name = request.form.get("service_name")
        service.service_description = request.form.get("service_description")
        service.base_price = request.form.get("base_price")
        service.time_required = request.form.get("time_required")
        
        db.session.commit()
        
        flash("Service updated successfully!", "success")
        return redirect(url_for('admin_availableService'))
    
    # return render_template("admin_edit_service.html", service=service)


@app.route("/admin_dashboard/delete_service/<int:service_id>", methods=["POST"])
def delete_service(service_id):
    if 'username' not in session or not session.get('is_admin'):
        flash("Please login as admin first!", "danger")
        return redirect(url_for('admin_login'))
    

    approved_Service_professionals = User.query.filter_by(is_professional = True, is_approved = True, service_id = service_id).all()
    for service_professional in approved_Service_professionals:
        # service_professional.service_id = None  #Must check if it works
        service_professional.is_approved = False
        #Above we are deactivating professionals instead of deleting them.

    service = HouseholdServices.query.get_or_404(service_id)
    db.session.delete(service)
    db.session.commit()
    

    flash("Service deleted successfully!", "success")
    return redirect(url_for('admin_availableService'))




@app.route("/pending_professionals", methods=['GET'])
def pending_professionals():
    if 'username' not in session or not session.get('is_admin'):
        flash("Please login as admin first!", "danger")
        return redirect(url_for('admin_login'))

    unapproved_professionals = User.query.filter_by(is_professional=True, is_approved=False).all()
    return render_template("pending_professionals.html", unapproved_professionals=unapproved_professionals)

@app.route("/approve_professional/<int:professional_id>", methods=['POST'])
def approve_professional(professional_id):
    if 'username' not in session or not session.get('is_admin'):
        flash("Please login as admin first!", "danger")
        return redirect(url_for('admin_login'))

    professional = User.query.get_or_404(professional_id)

    # Check if the action is to approve or deny
    if request.form.get('action') == 'approve':
        professional.is_approved = True  # Approve the professional
        db.session.commit()
        flash(f"{professional.user_name} has been approved successfully!", "success")
    else:
        # delete the pdf file stored in pdfs folder
        pdf_file = f"{professional.user_name}.pdf"
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], pdf_file))
        except OSError:
            pass
    
        # If denying, you can either delete the professional or set is_approved to False
        db.session.delete(professional)  # This will remove the professional from the database
        db.session.commit()
        flash(f"{professional.user_name} has been denied successfully!", "danger")

    return redirect(url_for('pending_professionals'))

@app.route("/approve_all_professionals", methods=['POST'])
def approve_all_professionals():
    if 'username' not in session or not session.get('is_admin'):
        flash("Please login as admin first!", "danger")
        return redirect(url_for('admin_login'))

    unapproved_professionals = User.query.filter_by(is_professional=True, is_approved=False).all()
    for professional in unapproved_professionals:
        professional.is_approved = True  # Approve each professional
    db.session.commit()
    flash("All pending professionals have been approved successfully!", "success")
    return redirect(url_for('pending_professionals'))


@app.route("/admin_dashboard/view_professional/<int:professional_id>", methods=['GET'])
def view_professional(professional_id):
    if 'username' not in session or not session.get('is_admin'):
        flash("Please login as admin first!", "danger")
        return redirect(url_for('admin_login'))

    professional = User.query.get_or_404(professional_id)  # Fetch the professional's details
    return render_template("view_professional.html", professional=professional)




@app.route("/professional_dashboard", methods=['GET', 'POST'])
def professional_dashboard():
    if 'username' not in session or not session.get('is_professional'):
        flash("Please login as a professional first!", "danger")
        return redirect(url_for('login'))
    
    # Fetch any necessary data for the professional dashboard
    # For example, you might want to fetch the professional's details or their service requests
    professional_id = session.get('user_id')
    professional = User.query.get_or_404(professional_id)

    if not professional.is_approved:
        flash("Please wait for admin approval before accessing your dashboard!", "warning")
        return redirect(url_for('login'))
    
    pending_reqsts = HouseholdServiceRequest.query.filter_by(professional_id=professional_id, status_of_serviceRequest="pending", request_type="private").all()
    accepted_reqsts = HouseholdServiceRequest.query.filter_by(professional_id=professional_id, status_of_serviceRequest="accepted").all()
    completed_reqsts = HouseholdServiceRequest.query.filter_by(professional_id=professional_id, status_of_serviceRequest="completed").all()
    return render_template("professional_dashboard.html", professional=professional, pending_reqsts=pending_reqsts, accepted_reqsts=accepted_reqsts, completed_reqsts=completed_reqsts)


@app.route('/handle_request/<int:request_id>', methods=['POST'])
def handle_request(request_id):
    if 'username' not in session or not session.get('is_professional'):
        flash("Please login as a professional first!", "danger")
        return redirect(url_for('login'))

    action = request.form.get('action')
    service_request = HouseholdServiceRequest.query.get_or_404(request_id)

    if action == 'accept':
        service_request.status_of_serviceRequest = 'accepted'
        flash('Request accepted successfully!', 'success')
    elif action == 'reject':
        service_request.status_of_serviceRequest = 'rejected'
        flash('Request rejected successfully!', 'success')
    else:
        flash('Invalid action!', 'danger')

    db.session.commit()
    return redirect(url_for('professional_dashboard'))


# Creating a customer dashboard route
@app.route("/customer_dashboard", methods = ['GET','POST'])
def customer_dashboard():
    if 'username' not in session or not session.get('is_customer'):
        flash("Please login as a customer first!", "danger")
        return redirect(url_for('login'))
    
    customer = User.query.get_or_404(session.get('user_id'))
    services = HouseholdServices.query.join(User).filter(User.is_approved == True).all()
    service_history = HouseholdServiceRequest.query.filter_by(customer_id=session.get('user_id')).all()   #Revisit and Update please
    return render_template("customer_dashboard.html", customer=customer, services=services, service_history=service_history)



# Creating a request service route for the customer
@app.route("/customer_dashboard/request_service/<int:service_id>", methods=['GET', 'POST'])
def request_service(service_id):
    if 'username' not in session or not session.get('is_customer'):
        flash("Please login as a customer first!", "danger")
        return redirect(url_for('login'))

    service = HouseholdServices.query.get_or_404(service_id)

    if request.method == 'POST':
        description = request.form.get('prof_description')
        customer = User.query.get_or_404(session.get('user_id'))
        public_request = request.form.get('public_request')  # Check if the public request checkbox is checked

        if public_request:
            # Create a public request for all professionals related to the selected service
            professionals = User.query.filter_by(is_professional=True, is_approved=True, service_id=service_id).all()
            for professional in professionals:
                new_request = HouseholdServiceRequest(
                    service_id=service.id,
                    customer_id=customer.id,
                    professional_id=professional.id,  # Associate with each professional
                    request_type='public',  # Mark as public request
                    request_description=description,  # Optional description
                    status_of_serviceRequest='pending',  # Initial status
                )
                db.session.add(new_request)
            db.session.commit()
            flash("Public service request created successfully!", "success")
        else:
            # Create a private request for the selected professional
            prof = request.form.get('professional_name')
            prof_id = User.query.filter_by(user_name=prof).first().id

            new_request = HouseholdServiceRequest(
                professional_id=prof_id,
                service_id=service.id,
                customer_id=customer.id,
                request_type='private',  # Mark as private request
                request_description=description,  # Optional description
                status_of_serviceRequest='pending',  # Initial status
            )
            db.session.add(new_request)
            db.session.commit()
            flash("Service request created successfully!", "success")

        return redirect(url_for('customer_dashboard'))

    professionals = User.query.filter_by(is_professional=True, is_approved=True, service_id=service_id).all()
    return render_template("request_service.html", service=service, professionals=professionals)


@app.route("/edit_request/<int:request_id>", methods=['GET','POST'])
def edit_request(request_id):
    if 'username' not in session or not session.get('is_customer'):
        flash("Please login as a customer first!", "danger")
        return redirect(url_for('login'))

    service_request = HouseholdServiceRequest.query.get_or_404(request_id)

    if service_request.status_of_serviceRequest != 'pending':
        flash("You cannot edit this request as it has already been processed.", "danger")
        return redirect(url_for('customer_dashboard'))

    if service_request.customer_id != session.get('user_id'):
        flash("You are not authorized to edit this request.", "danger")
        return redirect(url_for('customer_dashboard'))

    service_request.request_description = request.form['request_description']
    db.session.commit()
    flash("Service request updated successfully!", "success")
    return redirect(url_for('customer_dashboard'))

@app.route("/delete_request/<int:request_id>", methods=['GET','POST'])
def delete_request(request_id):
    if 'username' not in session or not session.get('is_customer'):
        flash("Please login as a customer first!", "danger")
        return redirect(url_for('login'))

    service_request = HouseholdServiceRequest.query.get_or_404(request_id)

    if service_request.status_of_serviceRequest != 'pending':
        flash("You cannot delete this request as it has already been processed.", "danger")
        return redirect(url_for('customer_dashboard'))

    if service_request.customer_id != session.get('user_id'):
        flash("You are not authorized to delete this request.", "danger")
        return redirect(url_for('customer_dashboard'))

    db.session.delete(service_request)
    db.session.commit()
    flash("Service request deleted successfully!", "success")
    return redirect(url_for('customer_dashboard'))

@app.route("/close_request/<int:request_id>", methods=['POST'])
def close_request(request_id):
    if 'username' not in session or not session.get('is_customer'):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    service_request = HouseholdServiceRequest.query.get_or_404(request_id)
    
    if service_request.customer_id != session.get('user_id'):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    if service_request.status_of_serviceRequest != 'accepted':
        return jsonify({'success': False, 'message': 'Invalid request status'}), 400

    # Update request status and add feedback
    service_request.status_of_serviceRequest = 'completed'
    service_request.rating_by_The_customer = float(request.form.get('rating', 0))
    service_request.review_by_The_customer = request.form.get('feedback')
    service_request.date_closed = datetime.now().date()

    # Update professional's average rating
    professional = service_request.professional
    total_ratings = professional.rating_count * professional.avg_rating
    professional.rating_count += 1
    professional.avg_rating = (total_ratings + float(request.form.get('rating', 0))) / professional.rating_count

    try:
        db.session.commit()
        return jsonify({'success': True, 'message': 'Request closed successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    
    

@app.route("/customer_Searching", methods=['GET'])
def customer_Searching():
    search_type = request.args.get('search_type')
    query = request.args.get('query')
    results = []

    if search_type and query:
        if search_type == 'pincode':
            results = User.query.filter_by(
                is_professional=True, 
                is_approved=True,
                pincode=query
            ).all()
        elif search_type == 'service':
            results = User.query.join(HouseholdServices).filter(
                User.is_professional == True,
                User.is_approved == True,
                HouseholdServices.service_name.ilike(f'%{query}%')   # used 'ilike' because it's not case sensitive. but 'like' is case sensitive.
            ).all()
        elif search_type == 'address':
            results = User.query.filter(
                User.is_professional == True,
                User.is_approved == True,
                User.address.ilike(f'%{query}%')
            ).all()

    # Fetch customer reviews for each professional
    for result in results:
        result.customer_reviews = HouseholdServiceRequest.query.filter(
            HouseholdServiceRequest.professional_id == result.id,
            HouseholdServiceRequest.status_of_serviceRequest == 'completed',
            HouseholdServiceRequest.rating_by_The_customer.isnot(None)  # Ensure there's a rating
        ).all()

    return render_template('customer_Searching.html', 
                           results=results, 
                           search_type=search_type, 
                           query=query)



@app.route("/professional_ratings", methods=['GET'])
def professional_ratings():
    if 'username' not in session or not session.get('is_professional'):
        flash("Please login as a professional first!", "danger")
        return redirect(url_for('login'))

    professional_id = session.get('user_id')
    
    # Fetch completed service requests for the logged-in professional
    ratings = HouseholdServiceRequest.query.filter_by(professional_id=professional_id, status_of_serviceRequest="completed").all()

    # Calculate average rating
    total_rating = 0
    rating_count = 0
    for rating in ratings:
        if rating.rating_by_The_customer:
            total_rating += rating.rating_by_The_customer
            rating_count += 1

    average_rating = total_rating / rating_count if rating_count > 0 else 0

    return render_template("professional_ratings.html", ratings=ratings, average_rating=average_rating)




@app.route("/admin_dashboard/service_requests", methods=['GET'])
def service_requests():
    if 'username' not in session or not session.get('is_admin'):
        flash("Please login as admin first!", "danger")
        return redirect(url_for('admin_login'))

    # Fetch all service requests
    requests = HouseholdServiceRequest.query.all()
    
    return render_template("admin_service_requests.html", requests=requests)


@app.route("/admin_dashboard/summary", methods=['GET'])
def admin_summary():
    if 'username' not in session or not session.get('is_admin'):
        flash("Please login as admin first!", "danger")
        return redirect(url_for('admin_login'))

    # Data for request status distribution
    request_status_counts = HouseholdServiceRequest.query.with_entities(
        HouseholdServiceRequest.status_of_serviceRequest,
        db.func.count(HouseholdServiceRequest.id)
    ).group_by(HouseholdServiceRequest.status_of_serviceRequest).all()

    request_status_data = {
        "labels": [status[0] for status in request_status_counts],
        "data": [status[1] for status in request_status_counts]
    }

    # Create a Plotly bar chart for request status distribution
    fig1 = go.Figure(data=[go.Bar(x=request_status_data['labels'], y=request_status_data['data'])])
    fig1.update_layout(title='Request Status Distribution',
                       xaxis_title='Status',
                       yaxis_title='Count')

    # Create a Plotly pie chart for user roles distribution
    user_roles_counts = {
        'Admin': User.query.filter_by(is_admin=True).count(),
        'Professional': User.query.filter_by(is_professional=True, is_approved=True).count(),
        'Customer': User.query.filter_by(is_customer=True).count()
    }

    fig2 = go.Figure(data=[go.Pie(labels=list(user_roles_counts.keys()), values=list(user_roles_counts.values()))])
    fig2.update_layout(title='User  Roles Distribution')

    # Convert the figures to HTML
    chart1_html = pio.to_html(fig1, full_html=False)
    chart2_html = pio.to_html(fig2, full_html=False)

    return render_template("admin_summary.html", 
                           total_requests=HouseholdServiceRequest.query.count(),
                           total_categories=Categories.query.count(),
                           total_professionals=User .query.filter_by(is_professional=True).count(),
                           total_customers=User .query.filter_by(is_customer=True).count(),
                           chart1=chart1_html,
                           chart2=chart2_html)

@app.route("/search_professionals", methods=['GET', 'POST'])
def search_professionals():
    professionals = []
    if request.method == 'POST':
        search_query = request.form.get('search_query')
        professionals = User.query.filter(
            User.is_professional == True,
            User.user_name.ilike(f'%{search_query}%')  # Search by username
        ).all()
    else:
        # If it's a GET request, fetch all professionals
        professionals = User.query.filter_by(is_professional=True).all()

    # Convert professionals to a list of dictionaries
    professionals_list = []
    for professional in professionals:
        service_name = professional.service.service_name if professional.service else 'N/A'
        professionals_list.append({'id': professional.id, 'user_name': professional.user_name, 'service_name': service_name})

    return render_template("search_professionals.html", professionals=professionals, professionals_list=professionals_list)


# Route for blocking a professional
@app.route("/block_professional/<int:professional_id>", methods=['POST'])
def block_professional(professional_id):
    professional = User.query.get_or_404(professional_id)
    professional.is_approved = False  # Block the professional
    db.session.commit()
    flash(f"{professional.user_name} has been blocked successfully!", "danger")
    return redirect(url_for('search_professionals'))

# Route for unblocking a professional
@app.route("/unblock_professional/<int:professional_id>", methods=['POST'])
def unblock_professional(professional_id):
    professional = User.query.get_or_404(professional_id)
    professional.is_approved = True  # Unblock the professional
    db.session.commit()
    flash(f"{professional.user_name} has been unblocked successfully!", "success")
    return redirect(url_for('search_professionals'))

    
@app.route("/search_suggestions", methods=['GET'])
def search_suggestions():
    search_type = request.args.get('search_type')
    query = request.args.get('query')
    suggestions = []

    if search_type == 'service' and query:
        suggestions = HouseholdServices.query.filter(
            HouseholdServices.service_name.ilike(f'%{query}%')
        ).all()
        suggestions = [service.service_name for service in suggestions]
    elif search_type == 'pincode' and query:
        suggestions = User.query.filter(
            User.pincode.ilike(f'%{query}%')
        ).all()
        suggestions = [str(user.pincode) for user in suggestions]
    elif search_type == 'address' and query:
        suggestions = User.query.filter(
            User.address.ilike(f'%{query}%')
        ).all()
        suggestions = [user.address for user in suggestions]

    return jsonify(suggestions)



@app.route("/service_summary", methods=['GET'])
def service_summary():
    if 'username' not in session or not session.get('is_customer'):
        flash("Please login as a customer first!", "danger")
        return redirect(url_for('login'))

    try:
        customer_id = session.get('user_id')

        # Fetch service requests for the customer
        service_requests = HouseholdServiceRequest.query.filter_by(customer_id=customer_id).all()

        # Count the status of service requests
        total_requests = len(service_requests)
        accepted_requests = sum(1 for request in service_requests if request.status_of_serviceRequest == 'accepted')
        completed_requests = sum(1 for request in service_requests if request.status_of_serviceRequest == 'completed')
        rejected_requests = sum(1 for request in service_requests if request.status_of_serviceRequest == 'rejected')
        pending_requests = sum(1 for request in service_requests if request.status_of_serviceRequest == 'pending')

        # Prepare data for Plotly
        labels = ["Total Requests", "Accepted", "Completed", "Rejected", "Pending"]
        values = [total_requests, accepted_requests, completed_requests, rejected_requests, pending_requests]

        # Create a Plotly bar chart
        fig = go.Figure(data=[go.Bar(x=labels, y=values)])
        fig.update_layout(title='Service Request Summary',
                          xaxis_title='Request Status',
                          yaxis_title='Count')

        # Convert the figure to HTML
        graph_html = pio.to_html(fig, full_html=False)

        # Determine the most used service by the customer
        most_used_service_query = (
            db.session.query(
                HouseholdServices.service_name,
                db.func.count(HouseholdServiceRequest.id).label('request_count')
            )
            .join(HouseholdServiceRequest, HouseholdServiceRequest.service_id == HouseholdServices.id)
            .filter(HouseholdServiceRequest.customer_id == customer_id)
            .group_by(HouseholdServices.service_name)
            .order_by(db.func.count(HouseholdServiceRequest.id).desc())
            .first()
        )

        most_used_service_name = most_used_service_query[0] if most_used_service_query else "No services used yet"

        # Generate a helpful tip based on the request history
        if total_requests == 0:
            tip_message = "Tip: You haven't made any service requests yet. Consider exploring available services to find what you need."
        elif completed_requests < accepted_requests:
            tip_message = "Tip: It seems you have some accepted requests that are still pending completion. Follow up with the professionals to ensure timely service."
        elif rejected_requests > 0:
            tip_message = "Tip: You have some rejected requests. Consider reviewing the reasons for rejection and adjusting your requests accordingly."
        else:
            tip_message = "Tip: You're actively using the service! Keep exploring new services and professionals to enhance your experience."

        return render_template("service_summary.html", 
                               graph_html=graph_html, 
                               most_used_service=most_used_service_name,
                               tip_message=tip_message)
    
    except Exception as e:
        db.session.rollback()
        print(f"Error in service_summary: {str(e)}")
        flash("An error occurred while loading the summary. Please try again.", "danger")
        return redirect(url_for('customer_dashboard'))


@app.route("/professional_summary", methods=['GET'])
def professional_summary():
    if 'username' not in session or not session.get('is_professional'):
        flash("Please login as a professional first!", "danger")
        return redirect(url_for('login'))

    professional_id = session.get('user_id')
    professional = User.query.get_or_404(professional_id)  # Fetch the professional object
    
    # Fetch completed service requests for the logged-in professional
    completed_requests = HouseholdServiceRequest.query.filter_by(professional_id=professional_id, status_of_serviceRequest="completed").all()

    # Calculate ratings
    total_rating = sum(request.rating_by_The_customer for request in completed_requests if request.rating_by_The_customer)
    rating_count = len([request for request in completed_requests if request.rating_by_The_customer])
    average_rating = total_rating / rating_count if rating_count > 0 else 0

    # Count services provided by the logged-in professional
    professional_service_count = len(completed_requests)

    # Calculate average number of services provided by other professionals
    all_professionals = User.query.filter_by(is_professional=True, is_approved=True).all()
    total_services_by_others = 0
    total_professionals = 0

    for prof in all_professionals:
        if prof.id != professional_id:  # Exclude the logged-in professional
            completed_requests_for_prof = HouseholdServiceRequest.query.filter_by(professional_id=prof.id, status_of_serviceRequest="completed").count()
            total_services_by_others += completed_requests_for_prof
            total_professionals += 1

    average_services_by_others = total_services_by_others / total_professionals if total_professionals > 0 else 0

    # Prepare data for Plotly
    service_counts = {}
    for request in completed_requests:
        service_name = request.service.service_name
        if service_name in service_counts:
            service_counts[service_name] += 1
        else:
            service_counts[service_name] = 1

    # Create a bar chart for services provided
    services = list(service_counts.keys())
    counts = list(service_counts.values())

    # Add the average services by others to the chart data
    services.append("Average by Others")
    counts.append(average_services_by_others)

    fig1 = go.Figure(data=[go.Bar(x=services, y=counts)])
    fig1.update_layout(title='Services Provided Comparison',
                       xaxis_title='Service Name',
                       yaxis_title='Count')

    # Create a pie chart for ratings distribution
    rating_distribution = [0, 0, 0, 0, 0]  # 1 to 5 stars
    for request in completed_requests:
        if request.rating_by_The_customer:
            rating_distribution[int(request.rating_by_The_customer) - 1] += 1

    fig2 = go.Figure(data=[go.Pie(labels=[1, 2, 3, 4, 5], values=rating_distribution)])
    fig2.update_layout(title='Rating Distribution')

    # Convert the figures to HTML
    chart1_html = pio.to_html(fig1, full_html=False)
    chart2_html = pio.to_html(fig2, full_html=False)

    # Determine the overall performance tip
    if professional_service_count < average_services_by_others or average_rating < 3:
        tip_message = "Tip: Focus on improving your service quality and customer satisfaction to increase your service requests."
    else:
        tip_message = "Tip: You're doing great! Keep up the good work and continue to provide excellent service."

    return render_template("professional_summary.html", 
                           professional=professional,
                           average_rating=average_rating,
                           professional_service_count=professional_service_count,
                           average_services_by_others=average_services_by_others,
                           chart1=chart1_html,
                           chart2=chart2_html,
                           tip_message=tip_message)



@app.route("/search_customers", methods=['GET', 'POST'])
def search_customers():
    customers = []
    if request.method == 'POST':
        search_query = request.form.get('search_query')
        customers = User.query.filter(
            User.is_customer == True,
            User.user_name.ilike(f'%{search_query}%')  # Search by username
        ).all()
    else:
        # If it's a GET request, fetch all customers
        customers = User.query.filter_by(is_customer=True).all()

    # Convert customers to a list of dictionaries
    customers_list = [{'id': customer.id, 'user_name': customer.user_name} for customer in customers]

    return render_template("search_customers.html", customers=customers, customers_list=customers_list)


# Route for blocking a customer
@app.route("/block_customer/<int:customer_id>", methods=['POST'])
def block_customer(customer_id):
    customer = User.query.get_or_404(customer_id)
    customer.is_approved = False  # Block the customer
    db.session.commit()
    flash(f"{customer.user_name} has been blocked successfully!", "danger")
    return redirect(url_for('search_customers'))

# Route for unblocking a customer
@app.route("/unblock_customer/<int:customer_id>", methods=['POST'])
def unblock_customer(customer_id):
    customer = User.query.get_or_404(customer_id)
    customer.is_approved = True  # Unblock the customer
    db.session.commit()
    flash(f"{customer.user_name} has been unblocked successfully!", "success")
    return redirect(url_for('search_customers'))


@app.route("/delete_professional/<int:professional_id>", methods=["POST"])
def delete_professional(professional_id):
    professional = User.query.get_or_404(professional_id)

    # Remove the PDF file from the static folder
    if professional.prof_file:
        pdf_file_path = os.path.join(app.config['UPLOAD_FOLDER'], professional.prof_file)
        try:
            os.remove(pdf_file_path)
        except OSError:
            flash(f"Error deleting file {professional.prof_file}", "danger")

    # Delete the professional from the database
    db.session.delete(professional)
    db.session.commit()
    flash(f"{professional.user_name} has been deleted successfully!", "success")
    return redirect(url_for('search_professionals'))

@app.route("/delete_customer/<int:customer_id>", methods=["POST"])
def delete_customer(customer_id):
    customer = User.query.get_or_404(customer_id)

    # Delete all service requests associated with this customer
    HouseholdServiceRequest.query.filter_by(customer_id=customer.id).delete()

    # Now delete the customer from the database
    db.session.delete(customer)
    db.session.commit()
    flash(f"{customer.user_name} has been deleted successfully!", "success")
    return redirect(url_for('search_customers'))


@app.route("/logout")
def logout():
   session.pop('username', None)
   session.pop('is_professional', None) 
   session.pop('is_customer', None)
   flash("Logout successful!", "success")
   if session.get('is_admin'):
       session.pop('is_admin', None)
       return redirect(url_for("admin_login"))
   else:
       session.pop('is_admin', None)
       return redirect(url_for("login"))







if __name__=="__main__":   #means : if my app is running in the main file only, then only run the app else don't run it.
    # reset_database()  #reset the database everytime we do the changes in database.

    # Create tables if they don't exist
    with app.app_context():
        db.create_all()
        print("Database tables created successfully!")

    # Start the Flask development server
    # Use environment variables for host and port in production
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=os.environ.get("FLASK_ENV") != "production")









# Error fixed :
# so In the Column() , we will use table name.
# In the relationship(), we will use class name.
