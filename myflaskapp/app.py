from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
from flask.logging import create_logger
from flask_mysqldb import MySQL
import mysql.connector
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps

app = Flask(__name__)
LOG = create_logger(app)


@app.route('/')
def index():
    return render_template('home.html')

# About Page
@app.route('/about')
def about():
    return render_template('about.html')

# Articles Page
@app.route('/articles')
def articles():
    # config MySQL
    conn = mysql.connector.Connect(host='localhost', user='root', password='password', database='myflaskapp')
    # Create cursor
    cur = conn.cursor(buffered=True, dictionary=True)

    # Get user by username
    cur.execute("SELECT * FROM articles")

    articles = cur.fetchall()

    if articles is not None:
        return render_template('articles.html', articles=articles)
    else:
        msg = "No Articles Found"
        return render_template('articles.html', msg=msg)
    
    cur.close()

# Single article
@app.route('/article/<string:id>/')
def article(id):
    # config MySQL
    conn = mysql.connector.Connect(host='localhost', user='root', password='password', database='myflaskapp')
    # Create cursor
    cur = conn.cursor(buffered=True, dictionary=True)

    # Get user by username
    cur.execute("SELECT * FROM articles WHERE id = %s", [id])

    article = cur.fetchone()

    return render_template('article.html', article=article)

# Register form class
class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Password do not match')
    ])
    confirm = PasswordField('Confirm Password')

# User Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # config MySQL
        conn = mysql.connector.Connect(host='localhost', user='root', password='password', database='myflaskapp')
        # Create cursor
        curs = conn.cursor()
        curs.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)", (name, email, username, password))

        # Commit to DB
        conn.commit()

        # Close connection
        curs.close()
        conn.close()

        flash('You are now registered and can log in', 'success')
        return redirect(url_for('index'))

    return render_template('register.html', form=form)

# User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get Form Fields
        username = request.form['username']
        password_candidate = request.form['password']

        # config MySQL
        conn = mysql.connector.Connect(host='localhost', user='root', password='password', database='myflaskapp')
        # Create cursor
        cur = conn.cursor(buffered=True, dictionary=True)

        # Get user by username
        cur.execute("SELECT * FROM users WHERE username = %s", [username])
        
        data = cur.fetchone()
        if data is not None:
            # Get stored hash
            password = data['password']

            # Compare Passwords
            if sha256_crypt.verify(password_candidate, password):
                # passed
                session['logged_in'] = True
                session['username'] = username

                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid login'
                return render_template('login.html', error=error)
            # Close connection
            cur.close()
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)

    return render_template('login.html')

# Check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized Access', 'danger')
            return redirect(url_for('login'))
    return wrap

# Logout
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'sucess')
    return redirect(url_for('login'))

# dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():

    # config MySQL
    conn = mysql.connector.Connect(host='localhost', user='root', password='password', database='myflaskapp')
    # Create cursor
    cur = conn.cursor(buffered=True, dictionary=True)

    # Get user by username
    cur.execute("SELECT * FROM articles")

    articles = cur.fetchall()

    if articles is not None:
        return render_template('dashboard.html', articles=articles)
    else:
        msg = "No Articles Found"
        return render_template('dashboard.html', msg=msg)
    
    cur.close()

    return render_template('dashboard.html')

# Artcile Class
class ArticleForm(Form):
    title = StringField('Title', [validators.Length(min=1, max=200)])
    body = TextAreaField('Body', [validators.Length(min=30)])

# Add Article
@app.route('/add_article', methods=['GET', 'POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data

        # config MySQL
        conn = mysql.connector.Connect(host='localhost', user='root', password='password', database='myflaskapp')
        # Create cursor
        curs = conn.cursor(buffered=True, dictionary=True)

        # Get user by username
        curs.execute("INSERT INTO articles(title, body, author) VALUES(%s, %s, %s)", (title, body, session['username']))
        
        # Commit to DB
        conn.commit()

        # Close connection
        curs.close()
        conn.close()

        flash('Article Created', 'success')

        return redirect(url_for('dashboard'))

    return render_template('add_article.html', form=form)

# Edit Article
@app.route('/edit_article/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_article(id):

    # config MySQL
    conn = mysql.connector.Connect(host='localhost', user='root', password='password', database='myflaskapp')
    # Create cursor
    curs = conn.cursor(buffered=True, dictionary=True)

    # Get Articles
    curs.execute("SELECT * FROM articles WHERE id = %s", [id])
    article = curs.fetchone()

    # Get Form
    form = ArticleForm(request.form)

    # Populate article form fields
    form.title.data = article['title']
    form.body.data = article['body']

    if request.method == 'POST' and form.validate():
        title = request.form['title']
        body = request.form['body']

        # config MySQL
        conn = mysql.connector.Connect(host='localhost', user='root', password='password', database='myflaskapp')
        # Create cursor
        curs = conn.cursor(buffered=True, dictionary=True)

        # Get user by username
        curs.execute("UPDATE articles SET title=%s, body=%s WHERE id=%s", (title, body, id))
        
        # Commit to DB
        conn.commit()

        # Close connection
        curs.close()
        conn.close()

        flash('Article Updated', 'success')

        return redirect(url_for('dashboard'))

    return render_template('edit_article.html', form=form)

# Delete Article
@app.route('/delete_article/<string:id>', methods=['POST'])
@is_logged_in
def delete_article(id):

    # config MySQL
    conn = mysql.connector.Connect(host='localhost', user='root', password='password', database='myflaskapp')
    # Create cursor
    curs = conn.cursor(buffered=True, dictionary=True)
    # Get Articles
    curs.execute("DELETE FROM articles WHERE id = %s", [id])

     # Commit to DB
    conn.commit()

    # Close connection
    curs.close()
    conn.close()

    flash('Article Deleted', 'success')
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.secret_key = 'secret123'
    app.run(debug=True)