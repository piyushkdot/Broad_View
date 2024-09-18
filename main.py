from flask import Flask, flash, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import requests

app = Flask(__name__)
app.secret_key = 'my_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///C:/Users/Piyush yadav/PycharmProjects/Broad View/blogs.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

login_manager = LoginManager(app)
login_manager.login_view = 'login'


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(100), nullable=False)

    def __init__(self, email, password):
        self.email = email
        self.set_password(password)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Content(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    pub_date = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    author = db.relationship('User', backref=db.backref('blogs', lazy=True))


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def fetch_blogs(api_url, api_key):
    response = requests.get(api_url, headers={"Authorization": api_key})
    if response.status_code == 200:
        return response.json().get('articles')
    else:
        return none


@app.route("/")
def index():
    api_url = 'https://newsapi.org/v2/top-headlines?language=en&category=technology'
    api_key = '3e8f4f5b98e247a4912b12a7056250b8'
    fetched_blogs = fetch_blogs(api_url, api_key) or []

    user_blogs = Content.query.order_by(Content.pub_date.desc()).all()
    combined_blogs = fetched_blogs + [
        {
            'title': blog.title,
            'description': blog.description,
            'author': blog.author.email,
            'publishedAt': blog.pub_date.strftime('%Y-%m-%d %H:%M:%S'),
            'url': None  # Assuming user blogs don't have an external URL
        }
        for blog in user_blogs
    ]

    return render_template('home.html', blogs=combined_blogs)


@app.route("/create_account")
def accounts_page():
    return render_template('create_account.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            flash("Login Successfully!", 'success')
            return redirect(url_for('index'))
        else:
            error = 'Invalid credentials'
            return render_template('login.html', error=error)
    return render_template('login.html')


@app.route("/sign-up", methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        new_user = User(email=email, password=password)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        flash('Account Created Successfully!', 'success')
        return redirect(url_for('index'))
    return render_template('sign-up.html')


@app.route("/profile")
@login_required
def profile_page():
    user_blogs = Content.query.filter_by(author_id=current_user.id).order_by(Content.pub_date.desc()).all()
    return render_template('profile.html', User=current_user, user_blogs=user_blogs)


@app.route("/about")
def about_us():
    return render_template('about.html')


@app.route("/books")
def book_recommendation():
    return render_template('books.html')


@app.route("/write-blog", methods=["GET", "POST"])
@login_required
def writing_blog():
    if request.method == "POST":
        title = request.form["blog_title"]
        description = request.form["main_content"]
        if title and description:
            new_blog = Content(title=title, description=description, author_id=current_user.id)
            db.session.add(new_blog)
            db.session.commit()
            flash("Blog posted successfully!", "success")
            return redirect(url_for('index'))
    return render_template('write-blog.html')


@app.route("/edit-blog/<int:blog_id>", methods=["GET", "POST"])
@login_required
def edit_blog(blog_id):
    blog = Content.query.get_or_404(blog_id)
    if blog.author_id != current_user.id:
        flash('You are not authorized to edit this blog', 'danger')
        return redirect(url_for('profile_page'))
    if request.method == "POST":
        blog.title = request.form["blog_title"]
        blog.description = request.form["main_content"]
        db.session.commit()
        flash('Blog updated successfully!', 'success')
        return redirect(url_for('profile_page'))
    return render_template('edit-blog.html', blog=blog)


@app.route("/delete-blog/<int:blog_id>", methods=["POST"])
@login_required
def delete_blog(blog_id):
    blog = Content.query.get_or_404(blog_id)
    if blog.author_id != current_user.id:
        flash('You are not authorized to delete this blog', 'danger')
        return redirect(url_for('profile_page'))
    db.session.delete(blog)
    db.session.commit()
    flash('Blog deleted successfully!', 'success')
    return redirect(url_for('profile_page'))


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You Have Been Logged Out!", "info")
    return redirect(url_for('index'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=3000)
