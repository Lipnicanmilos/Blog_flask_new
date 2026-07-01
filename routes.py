import os
import time
import random
from datetime import datetime

from flask import (
    render_template, request, redirect, url_for, session,
    flash, make_response, current_app
)
from flask_login import login_user, logout_user, login_required, current_user
from flask_mail import Message
from flask_socketio import emit
from werkzeug.utils import secure_filename

from app import app, db, mail, socketio
from models import User, Post, Comment, PostLike
from forms import RequestResetForm, ResetPasswordForm


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@app.route("/")
@app.route("/home")
def index():
    if current_user.is_authenticated:
        image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
        return render_template('index.html', image_file=image_file)
    return render_template('index.html')


# --- Registrácia ---------------------------------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    error = None

    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"].lower()
        password = request.form["password"]
        password2 = request.form["password2"]

        existing_email = User.query.filter_by(email=email).first()
        existing_name = User.query.filter_by(username=name).first()

        if len(name) < 1:
            error = "You must enter a name"
        elif len(email) < 1:
            error = "You must enter an email"
        elif len(password) < 1:
            error = "You must enter a password"
        elif password != password2:
            error = "Passwords must match"
        elif len(password) < 4:
            error = "Your password is less than 4 characters"
        elif existing_email is not None:
            error = "This email is already registered"
        elif existing_name is not None:
            error = "A user with this name already exists"
        else:
            user = User(username=name, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()

            login_user(user)
            session["name"] = user.username

            if app.config.get('MAIL_USERNAME') and app.config.get('MAIL_PASSWORD'):
                msg = Message(
                    subject="Registrácia do aplikácie",
                    sender=app.config.get("MAIL_USERNAME"),
                    recipients=[user.email],
                    html=f"<h2>Vitaj, {user.username}!</h2><p>Tvoj účet bol úspešne vytvorený.</p>"
                )
                mail.send(msg)

            flash("You have created an account, you can log in")
            return redirect(url_for('login'))

    return render_template('register.html', error=error)


# --- Zoznam a správa používateľov -----------------------------------
@app.route('/users')
@login_required
def users():
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    page = request.args.get('page', 1, type=int)
    users_page = User.query.paginate(page=page, per_page=5)
    return render_template('users.html', users=users_page, image_file=image_file)


@app.route('/update', methods=['POST'])
@login_required
def update():
    user = User.query.get_or_404(request.form['id'])
    user.username = request.form['name']
    user.email = request.form['email'].lower()
    db.session.commit()
    flash("All changes saved")
    return redirect(url_for('users'))


@app.route('/delete/<int:id>', methods=['GET'])
@login_required
def delete(id):
    user = User.query.get_or_404(id)
    Post.query.filter_by(user_id=id).delete()
    db.session.delete(user)
    db.session.commit()
    flash("The user has been successfully deleted and also their posts")
    return redirect(url_for('users'))


# --- Prihlásenie / odhlásenie ----------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index2'))

    error = None
    if request.method == "POST":
        email = request.form.get("email", "").lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            session["name"] = user.username
            return redirect(url_for('index2'))
        error = "E-mail or password is incorrect."

    return render_template("login.html", error=error)


@app.route('/logout')
@login_required
def logout():
    session.clear()
    logout_user()
    return redirect(url_for('login'))


# --- Profil -----------------------------------------------------------
@app.route('/profile')
@login_required
def profile():
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('profile.html', title='Profile', image_file=image_file)


@app.route('/profile/upload', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(url_for('profile'))

    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('profile'))

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        current_user.image_file = filename
        db.session.commit()
        flash("Changes saved")

    return redirect(url_for('profile'))


@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    current_user.username = request.form['name']
    current_user.email = request.form['email'].lower()
    db.session.commit()
    flash("Changes saved, will be displayed the next time you sign in")
    return redirect(url_for('profile'))


@app.route('/delete_profile', methods=['GET'])
@login_required
def delete_profile():
    user_id = current_user.id
    Post.query.filter_by(user_id=user_id).delete()
    session.clear()
    logout_user()
    user = User.query.get(user_id)
    db.session.delete(user)
    db.session.commit()
    flash("You have also deleted your posts")
    return redirect(url_for('login'))


# --- Príspevky ----------------------------------------------------------
@app.route('/posts', methods=['GET'])
@login_required
def index2():
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=2)
    return render_template('index2.html', posts=posts, image_file=image_file,
                            user=current_user, post=Post, postlike=PostLike)


@app.route("/create_new", methods=["POST"])
@login_required
def create_new():
    title = request.form["title"]
    content = request.form.get('editor1')

    post = Post(title=title, content=content, user_id=current_user.id)
    db.session.add(post)
    db.session.commit()
    flash("The post has been added")

    return redirect(url_for('index2'))


@app.route('/delete_post/<int:id_post>', methods=['GET'])
@login_required
def delete_post(id_post):
    post = Post.query.get_or_404(id_post)
    if post.user_id != current_user.id:
        flash('You do not have permission to delete this post.', category='error')
        return redirect(url_for('index2'))
    db.session.delete(post)
    db.session.commit()
    flash("The post has been deleted")
    return redirect(url_for('index2'))


# --- Komentáre ----------------------------------------------------------
@app.route("/create-comment/<int:post_id>", methods=['POST'])
@login_required
def create_comment(post_id):
    text = request.form.get('text')

    if not text:
        flash('Comment cannot be empty.', category='error')
    else:
        post = Post.query.get(post_id)
        if post:
            comment = Comment(content=text, author=current_user.id, post_id=post_id)
            db.session.add(comment)
            db.session.commit()
        else:
            flash('Post does not exist.', category='error')

    return redirect(url_for('index2'))


@app.route("/delete-comment/<int:comment_id>")
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get(comment_id)
    if not comment:
        flash('Comment does not exist.', category='error')
    elif current_user.id != comment.post.user_id and current_user.id != comment.author:
        flash('You do not have permission to delete this comment.', category='error')
    else:
        db.session.delete(comment)
        db.session.commit()
    return redirect(url_for('index2'))


# --- Lajky ----------------------------------------------------------------
@app.route('/like/<int:post_id>/<action>')
@login_required
def like_action(post_id, action):
    post = Post.query.get_or_404(post_id)
    if action == 'like':
        current_user.like_post(post)
    elif action == 'unlike':
        current_user.unlike_post(post)
    db.session.commit()
    return redirect(request.referrer or url_for('index2'))


# --- Reset hesla ------------------------------------------------------------
def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Žiadosť o obnovenie hesla',
                  sender=app.config.get('MAIL_USERNAME', 'noreply@demo.com'),
                  recipients=[user.email])
    msg.body = f'''Ak chcete obnoviť svoje heslo, kliknite na nasledujúci odkaz:
{url_for('reset_token', token=token, _external=True)}
Ak ste túto žiadosť neodoslali, jednoducho tento e-mail ignorujte.
'''
    mail.send(msg)


@app.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An email has been sent with instructions on how to reset your password.', 'info')
        return redirect(url_for('login'))
    return render_template('reset_request.html', title='Reset Password', form=form)


@app.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('index2'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('Ide o neplatný alebo vypršaný dotaz na reset hesla', 'warning')
        return redirect(url_for('reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been updated! You can log in now.', 'success')
        return redirect(url_for('login'))
    return render_template('reset_token.html', title='Reset Password', form=form)


# --- Chat (Socket.IO) ---------------------------------------------------------
@app.route('/chat')
@login_required
def chat():
    time_stamp = time.strftime('%H:%M:%S', time.localtime())
    username = current_user.username
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('ChatApp.html', image_file=image_file, username=username, time_stamp=time_stamp)


@socketio.on('my event')
def handle_my_custom_event(json):
    emit('my response', json)


@socketio.on('connect')
def handle_connect(auth):
    username = current_user.username if current_user.is_authenticated else 'Guest'
    emit('my response', {'data': 'Connected ' + username})


@socketio.on('disconnect')
def handle_disconnect():
    pass


# --- CKEditor upload --------------------------------------------------------
def gen_rnd_filename():
    prefix = datetime.now().strftime('%Y%m%d%H%M%S')
    return f"{prefix}{random.randrange(1000, 10000)}"


@app.route('/ckupload/', methods=['POST', 'OPTIONS'])
@login_required
def ckupload():
    """CKEditor file upload"""
    error = ''
    url = ''
    callback = request.args.get("CKEditorFuncNum")

    if request.method == 'POST' and 'upload' in request.files:
        fileobj = request.files['upload']
        _, fext = os.path.splitext(fileobj.filename)
        rnd_name = f"{gen_rnd_filename()}{fext}"
        filepath = os.path.join(current_app.static_folder, 'upload', rnd_name)
        dirname = os.path.dirname(filepath)

        if not os.path.exists(dirname):
            try:
                os.makedirs(dirname)
            except OSError:
                error = 'ERROR_CREATE_DIR'
        elif not os.access(dirname, os.W_OK):
            error = 'ERROR_DIR_NOT_WRITEABLE'

        if not error:
            fileobj.save(filepath)
            url = url_for('static', filename=f'upload/{rnd_name}')
    else:
        error = 'post error'

    res = f"""<script type="text/javascript">
             window.parent.CKEDITOR.tools.callFunction({callback}, '{url}', '{error}');
             </script>"""
    response = make_response(res)
    response.headers["Content-Type"] = "text/html"
    return response
