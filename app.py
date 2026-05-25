from datetime import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask import render_template, request, redirect
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin, current_user
import os
from werkzeug.utils import secure_filename


app = Flask(__name__)

app.config['SECRET_KEY'] = 'secretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))

    friends_count = db.Column(db.Integer, default=0)
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))  
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    content = db.Column(db.Text)

    image = db.Column(db.String(200))
    video = db.Column(db.String(200))

    likes = db.Column(db.Integer, default=0)
    shares = db.Column(db.Integer, default=0)

    created_at = db.Column(
    db.DateTime,
    default=datetime.utcnow
)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    comments = db.relationship(
    'Comment',
    backref='post',
    lazy=True
)
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    text = db.Column(db.Text)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
class Friend(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer)

    friend_id = db.Column(db.Integer)
@app.route("/")
def home():
    return redirect("/login")
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form['username']
        password = request.form['password']

        user = User(
            username=username,
            password=password
        )

        db.session.add(user)
        db.session.commit()

        return redirect("/login")

    return render_template("register.html")
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(
            username=username,
            password=password
        ).first()

        if user:
            login_user(user)

            return redirect("/feed")

    return render_template("login.html")
@app.route("/feed")
@login_required
def feed():

    posts = Post.query.all()

    users = User.query.all()

    return render_template(
        "feed.html",
        posts=posts,
        users=users
    )
def can_post(user):

    today_posts = Post.query.filter_by(
        user_id=user.id
    ).count()

    # No friends
    if user.friends_count == 0:
        return False

    # 1 friend = 1 post/day
    elif user.friends_count == 1:
        return today_posts < 1

    # 2 friends = 2 posts/day
    elif user.friends_count == 2:
        return today_posts < 2

    # More than 10 friends = unlimited
    elif user.friends_count > 10:
        return True

    return False

@app.route("/create-post", methods=["GET", "POST"])
@login_required
def create_post():

    if not can_post(current_user):
        return "Posting limit reached"

    if request.method == "POST":

        content = request.form['content']

        image_file = request.files.get('image')
        video_file = request.files.get('video')

        image_name = None
        video_name = None

        # Save image
        if image_file and image_file.filename != "":

            image_name = secure_filename(
                image_file.filename
            )

            image_file.save(
                os.path.join(
                    "static/uploads",
                    image_name
                )
            )

        # Save video
        if video_file and video_file.filename != "":

            video_name = secure_filename(
                video_file.filename
            )

            video_file.save(
                os.path.join(
                    "static/uploads",
                    video_name
                )
            )

        post = Post(
            content=content,
            image=image_name,
            video=video_name,
            user_id=current_user.id
        )

        db.session.add(post)
        db.session.commit()

        return redirect("/feed")

    return render_template("create_post.html")
@app.route("/like/<int:id>")
@login_required
def like(id):

    post = Post.query.get(id)

    post.likes += 1

    db.session.commit()

    return redirect("/feed")
@app.route("/share/<int:id>")
@login_required
def share(id):

    post = Post.query.get(id)

    post.shares += 1

    db.session.commit()

    return redirect("/feed")
@app.route("/comment/<int:id>", methods=["POST"])
@login_required
def comment(id):

    text = request.form['text']

    new_comment = Comment(
        text=text,
        user_id=current_user.id,
        post_id=id
    )

    db.session.add(new_comment)
    db.session.commit()

    return redirect("/feed")
@app.route("/add-friend/<int:id>")
@login_required
def add_friend(id):

    friend = Friend(
        user_id=current_user.id,
        friend_id=id
    )

    db.session.add(friend)

    current_user.friends_count += 1

    db.session.commit()

    return redirect("/feed")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)