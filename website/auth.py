# website/auth.py
from flask import Blueprint, render_template, request, flash, redirect, url_for
from . import db 
from website.models import User, Book
from flask_login import login_user, current_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta

auth = Blueprint('auth', __name__)
# Routes
#Sign Up Logic
@auth.route("/sign-up", methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        # Get Information to register new user
        email = request.form.get('email')
        name = request.form.get('firstName')  
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        # Default role for new users
        role = 'student'

        # Check for issues with information
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exists.', category='error')
        elif len(email) < 4 or len(name) < 2 or len(password1) < 7:
            flash('Invalid input. Please check your data.', category='error')
        elif password1 != password2:
            flash('Passwords don\'t match.', category='error')
        else:
            # If information clears above then register the new user
            # Password Hashing using sha256 from werkzeug.security library
            hashed_password = generate_password_hash(password1, method='pbkdf2:sha256')
            new_user = User(email=email, name=name, role=role, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user, remember=True)
            flash('Account created!', category='success')

            # Redirect to home page based on the user's role
            return redirect(url_for('auth.home'))
    return render_template("sign_up.html", user=current_user)

#Login Page Logic
@auth.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        #Get the login credentials 
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()   
        #Check for Password Hashing    
        if user and check_password_hash(user.password, password):
            flash('Logged in successfully!', category='success')
            login_user(user, remember=True)
            # Redirect based on the user's role
            if user.role == 'admin':
                return redirect(url_for('auth.admin'))
            elif user.role == 'librarian':
                return redirect(url_for('auth.librarian'))
            elif user.role == 'faculty':
                return redirect(url_for('auth.faculty'))
            elif user.role == 'student':
                return redirect(url_for('auth.student'))
            else:
                return redirect(url_for('auth.home'))
        else:
            flash('Incorrect email or password. Please try again.', category='error')

    return render_template("login.html", user=current_user)

#Logout Page Logic
@auth.route('/logout')
@login_required
#Log out if clicked and redirect to login
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

#Homepage and default page Logic
@auth.route("/")
@auth.route("/home")
@login_required
def home():
    #Show different Home pages based on the Role the User has
    # Redirect users to their role-specific pages
    if current_user.role == 'admin':
        return redirect(url_for('auth.admin'))
    elif current_user.role == 'librarian':
        return redirect(url_for('auth.librarian'))
    elif current_user.role == 'faculty':
        return redirect(url_for('auth.faculty'))
    elif current_user.role == 'student':
        return redirect(url_for('auth.student'))
    else:
        return render_template("home.html", user=current_user, content="Welcome, User!")

#Librarian Logic
@auth.route("/librarian")
@login_required
def librarian():
    if current_user.role != 'librarian':
        flash('You do not have permission to access the librarian page.', category='error')
        return redirect(url_for('auth.home'))

    # Fetch books from the database for display
    books = Book.query.all()

    return render_template("librarian.html", user=current_user, books=books)

@auth.route("/add-book", methods=['POST'])
@login_required
def add_book():
    if current_user.role != 'librarian':
        flash('You do not have permission to add books.', category='error')
        return redirect(url_for('auth.librarian'))

    # Retrieve book information from the form
    title = request.form.get('title')
    author = request.form.get('author')

    # Create a new book
    new_book = Book(title=title, author=author)
    db.session.add(new_book)
    db.session.commit()

    flash(f'Book "{new_book.title}" added successfully!', category='success')

    return redirect(url_for('auth.librarian'))

@auth.route("/remove-book/<int:book_id>", methods=['POST'])
@login_required
def remove_book(book_id):
    if current_user.role != 'librarian':
        flash('You do not have permission to remove books.', category='error')
        return redirect(url_for('auth.librarian'))

    book_to_remove = Book.query.get(book_id)
    if book_to_remove:
        db.session.delete(book_to_remove)
        db.session.commit()
        flash(f'Book "{book_to_remove.title}" removed successfully!', category='success')
    else:
        flash(f'Book not found.', category='error')

    return redirect(url_for('auth.librarian'))

# Student Logic
@auth.route("/student", methods=['GET'])
@login_required
def student():
    # Get available and checked out books
    available_books = Book.query.filter_by(is_checked_out=False).all()
    checked_out_books = Book.query.filter_by(borrower_id=current_user.id, is_checked_out=True).all()

    return render_template("student.html", user=current_user, available_books=available_books, checked_out_books=checked_out_books)

#Faculty Page Logic
@auth.route("/faculty", methods=['GET'])
@login_required
def faculty():
    # Get available and checked out books
    available_books = Book.query.filter_by(is_checked_out=False).all()
    checked_out_books = Book.query.filter_by(borrower_id=current_user.id, is_checked_out=True).all()

    return render_template("faculty.html", user=current_user, available_books=available_books, checked_out_books=checked_out_books)

#Checkout Logic
@auth.route("/checkout_book/<role>", methods=['POST'])
@login_required
def checkout_book(role):
    book_id = request.form.get('book_id')

    if role == 'student':
        book = Book.query.get(book_id)
        if book and not book.is_checked_out:
            book.is_checked_out = True
            book.due_date = datetime.utcnow() + timedelta(weeks=2)
            book.borrower_id = current_user.id
            db.session.commit()
            flash(f'You have checked out {book.title}!', category='success')
        else:
            flash('Book not available for checkout.', category='error')
        return redirect(url_for('auth.student'))

    elif role == 'faculty':
        book = Book.query.get(book_id)
        if book and not book.is_checked_out:
            book.is_checked_out = True
            book.due_date = datetime.utcnow() + timedelta(weeks=20)  # 20 weeks for faculty
            book.borrower_id = current_user.id
            db.session.commit()
            flash('Book checked out successfully!', category='success')
        else:
            flash('Book not available for checkout.', category='error')
        return redirect(url_for('auth.faculty'))

#Return Logic
@auth.route("/return_book/<role>", methods=['POST'])
@login_required
def return_book(role):
    book_id = request.form.get('book_id')

    if role == 'student':
        book = Book.query.get(book_id)
        if book and book.is_checked_out and book.borrower_id == current_user.id:
            book.is_checked_out = False
            book.due_date = None
            book.borrower_id = None
            db.session.commit()
            flash(f'You have returned {book.title}.', category='success')
        else:
            flash('Error returning the book.', category='error')
        return redirect(url_for('auth.student'))

    elif role == 'faculty':
        book = Book.query.get(book_id)
        if book and book.is_checked_out and book.borrower_id == current_user.id:
            book.is_checked_out = False
            book.due_date = None
            book.borrower_id = None
            db.session.commit()
            flash('Book returned successfully!', category='success')
        else:
            flash('Invalid book or not checked out by you.', category='error')
        return redirect(url_for('auth.faculty'))

#Admin Page Logic 
@auth.route("/admin")
@login_required
def admin():
    if current_user.role != 'admin':
        return redirect(url_for('auth.home'))  # Redirect if not an admin

    users = User.query.all()
    return render_template("admin.html", user=current_user, users=users)

@auth.route("/modify-role", methods=['POST'])
@login_required
def modify_role():
    if current_user.role != 'admin':
        return redirect(url_for('auth.home'))  # Redirect if not an admin
    #Get input from page
    user_email = request.form.get('user_email')
    new_role = request.form.get('new_role')
    #Modify the user Roles 
    user = User.query.filter_by(email=user_email).first()
    if user:
        user.role = new_role
        db.session.commit()
        flash(f'Role for {user.email} modified to {new_role}.', category='success')
    else:
        flash(f'User with email {user_email} not found.', category='error')

    return redirect(url_for('auth.admin'))

@auth.route("/add-user", methods=['POST'])
@login_required
def add_user():
    if current_user.role != 'admin':
        return redirect(url_for('auth.home'))  # Redirect if not an admin

    new_user_email = request.form.get('new_user_email')
    new_user_name = request.form.get('new_user_name')
    new_user_role = request.form.get('new_user_role')
    new_user_password = request.form.get('new_user_password')

    existing_user = User.query.filter_by(email=new_user_email).first()
    if existing_user:
        flash(f'User with email {new_user_email} already exists.', category='error')
    else:
        hashed_password = generate_password_hash(new_user_password, method='pbkdf2:sha256')
        new_user = User(email=new_user_email, name=new_user_name, role=new_user_role, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash(f'User {new_user_email} added successfully.', category='success')

    return redirect(url_for('auth.admin'))

@auth.route("/delete-user", methods=['POST'])
@login_required
def delete_user():
    if current_user.role != 'admin':
        return redirect(url_for('auth.home'))  # Redirect if not an admin

    delete_user_email = request.form.get('delete_user_email')

    user_to_delete = User.query.filter_by(email=delete_user_email).first()
    if user_to_delete:
        db.session.delete(user_to_delete)
        db.session.commit()
        flash(f'User {delete_user_email} deleted successfully.', category='success')
    else:
        flash(f'User with email {delete_user_email} not found.', category='error')

    return redirect(url_for('auth.admin'))