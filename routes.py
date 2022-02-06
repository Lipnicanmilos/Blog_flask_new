from flask import Flask, render_template, request, redirect, url_for, session, flash, make_response, request
from datetime import datetime
from flask_login import login_manager, login_user, logout_user, login_required, current_user, LoginManager
import sqlite3, random
from flask import render_template, url_for, flash, redirect, send_from_directory
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.local import F
from werkzeug.utils import secure_filename
from app import app, db
from models import User, Post, PostLike
from flask_login import login_user, current_user, logout_user, login_required
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import User, Comment, PostLike
import os, bcrypt, time
from flask import Flask, flash, request, redirect, url_for
from werkzeug.utils import secure_filename
from flask_mail import Mail, Message
from forms import *
from flask_bcrypt import Bcrypt
from flask_socketio import SocketIO, join_room, leave_room, emit, disconnect, ConnectionRefusedError
from flask_ckeditor import *


bcrypt = Bcrypt(app)
app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba245'
socketio = SocketIO( app )
class Socket:
    def __init__(self, sid):
        self.sid = sid
        self.connected = True

    # Emits data to a socket's unique room
    def emit(self, event, data):
        emit(event, data, room=self.sid)


CKEditor = CKEditor( app )
app.config['CKEDITOR_HEIGHT'] = 1048576



UPLOAD_FOLDER = './static/profile_pics'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 0.5 * 1024 * 1024



login = LoginManager(app)
login.login_view = 'login'

login.login_message_category = 'info'
login.login_message = 'Please log in ... '

mail_settings = {
    "MAIL_SERVER": 'smtp.gmail.com',
    "MAIL_PORT": 465,
    "MAIL_USE_TLS": False,
    "MAIL_USE_SSL": True,
    "MAIL_USERNAME": 'webappflask0@gmail.com',
    "MAIL_PASSWORD": 'Lipnican08'
}

app.config.update(mail_settings)
mail = Mail(app)



@login.user_loader
def load_user(id):
    return User.query.get(id)


@app.route("/")
@app.route("/home")
def index():
    # msg = Message(subject="Hlavička_mailu",
    #     sender=app.config.get("MAIL_USERNAME"),
    #     recipients=["lipnicanmilos@gmail.com"], # replace with your email for testing
    #     body="Toto je automatický mail z aplikácie ;)")
    # mail.send(msg)
    if "name" in session:
        image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
        return render_template('index.html', image_file=image_file)
    return render_template('index.html')


#registrácia usera do db 
#-----------------------------------------
@app.route("/register", methods=["GET", "POST"])
def register():

    error = None
    success = None
    
    #check the request method to ensure the handling of POST request only
    if request.method == "POST":
        #store the form value
        name = request.form["name"]
        email = request.form["email"].lower()
        password = request.form["password"]
        password2 = request.form["password2"]

        # porovnanie emailu s datami v db(emaily) a ukiženie v exstingInfo
        conn = sqlite3.connect('sqlite.db') 
        c = conn.cursor()
        c.execute("SELECT * from user where email = (?)", [email])
        existingInfo = c.fetchone()
        con = conn.cursor()
        con.execute("SELECT * from user where username = (?)", [name])
        existingInfo1 = con.fetchone()
        

        if len(name) < 1:
            error = "You must enter a name "
        
        elif len(email) < 1:
            error = "You must enter a email"

        elif len(password) < 1:
            error = "You must enter a password "
        
        elif password != password2:
            error = "password must be the same"

        elif len(password) < 4:
            error = "Your password is less than 4 characters"
        
        elif existingInfo is not None:
            error = "This email is already registered" 
        
        elif existingInfo1 is not None:
            error = "A user with this name already exists" 

        else:        
            # store the user details in the user database table
            user = User()
            user.username = name
            user.email = email
            user.set_password(password)
            
            # add the user object to the database
            db.session.add(user)

            
            session["name"] = name
            session["id"] = user.id
            session["email"] = user.email
            session["image_file"] = user.image_file
            
            # commit changes to the database 
            db.session.commit()

            msg = Message(subject="Registrácia do Aplikácie",
                sender=app.config.get("MAIL_USERNAME"),
                recipients=[session["email"]], # replace with your email for testing
                html = "<h2>Prihlasovacie údaje:</h2>\n<b>Email: " + session['email'] + "<br>Heslo: " + password + "<br>Nick: " + session['name'] + "<br><a href='http://192.168.100.20:8080/'>Moja webova aplikácia </a> <img src='https://miro.medium.com/max/1400/1*Q5EUk28Xc3iCDoMSkrd1_w.png' style='width:42px;height:42px;'>")
            mail.send(msg)

            session.clear()
            logout_user()
            flash("You have created an account, you can log in")
            return redirect(url_for('login'))

    return render_template('register.html', error=error)
# --------------------------------------

# užívatelia 
@app.route('/users')
def users():
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    conn = sqlite3.connect('sqlite.db') 
    c = conn.cursor()
    c.execute('SELECT * FROM user')  

    page = request.args.get('page', 1, type=int)
    users = User.query.paginate(page=page, per_page=5)

    return render_template('users.html', users = users, image_file=image_file)

# update - uživatela
# -------------------------------------------------------------
@app.route('/update',methods=['POST','GET'])
def update():

    if request.method == 'POST':
        id_data = request.form['id']
        name = request.form['name']
        email = request.form['email'].lower()
        

        conn = sqlite3.connect('sqlite.db') 
        c = conn.cursor()
        c.execute("""UPDATE user SET username=(?), email=(?) WHERE id=(?)""", (name, email, id_data))
        flash("All changes saved")
        c.connection.commit()
        c.close()

        return redirect(url_for('users'))




# delete - uživatela
# -------------------------------------------------------------
@app.route('/delete/<string:id>', methods = ['GET'])
def delete(id):
    
    conn = sqlite3.connect('sqlite.db') 
    c = conn.cursor()
    c.execute("DELETE FROM user WHERE id=(?)", [id]) 
    c.execute("DELETE FROM post WHERE user_id=(?)", [id]) #should be

    c.connection.commit()
   
    c.close()
    
    flash("the user has been successfully deleted and also his posts")
    
    return redirect(url_for('users'))

# login uživateľa
# -----------------------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    
    if "name" in session:
        return redirect(url_for('index2'))
    

    error = False
    # flash('Prosím príhláste sa...')

    if request.method == "POST":
        email = request.form.get("email").lower()
        password = request.form.get("password")
    

        user = User.query.filter_by(email=email).first()
        if user:
            if user.check_password(password):
                session["name"] = user.username
                session["id"] = user.id
                session["email"] = user.email
                session["image_file"] = user.image_file
                login_user(user)
                return redirect(url_for('index2'))
            else:
                error = "E-mail or password is incorrect."
        else:
            error = "E-mail or password is incorrect."
        
    return render_template("login.html", error=error)


# logout uživateľa
# -----------------------------------------------------
@app.route('/logout')
def logout():
    session.clear()
    logout_user()
    return render_template("login.html")




    
@app.route('/table')
@login_required
def table():
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file )
    return render_template('table.html', image_file=image_file)


@app.route("/moje_meno")
def moje_meno():
    if "name" not in session:
        return "nie si prihlaseny"

    return str(session["id"]) + ", ...  " + session["name"] + ", ...  " + session["email"]

# Profil
# -------------------------------------------------------
@app.route('/profile')
@login_required
def profile():
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('profile.html', title='Profile', image_file=image_file)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/profile', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            id_data = session["id"] 

            conn = sqlite3.connect('sqlite.db') 
            c = conn.cursor()
            c.execute("""UPDATE user SET image_file=(?) WHERE id=(?)""", (filename, id_data))
            flash("Changes saved")
            c.connection.commit()
            c.close()
    return redirect(url_for('profile'))

# update Profil
# -------------------------------------------------------
@app.route('/update_profile',methods=['POST','GET'])
def update_profile():

    if request.method == 'POST':
            id_data = request.form['id']
            name = request.form['name']
            email = request.form['email'].lower()
        
            conn = sqlite3.connect('sqlite.db') 
            c = conn.cursor()
            c.execute("""UPDATE user SET username=(?), email=(?) WHERE id=(?)""", (name, email, id_data))
            flash("Changes saved, will be displayed the next time you sign in")
            c.connection.commit()
            c.close()

    return redirect(url_for('profile'))

@app.route('/upload', methods=['POST'])
def upload():
    pic = request.files['pic']

    if not pic:
        return 'No pic upload', 400
    
    filename = secure_filename(pic.filename)
    image_file = pic.image_file

    img = User(img=pic.read())

# delete - uživatela z profilu
# -------------------------------------------------------------
@app.route('/delete_profil/<string:id>', methods = ['GET'])
def delete_profil(id):
    
    conn = sqlite3.connect('sqlite.db') 
    c = conn.cursor()
    c.execute("DELETE FROM user WHERE id=(?)", [id]) 
    c.execute("DELETE FROM post WHERE user_id=(?)", [id]) #should be
    #c.execute("DELETE FROM comment WHERE author=(?)", [id]) #should be

    c.connection.commit()
    c.close()

    session.clear()
    logout_user()
    flash("You have also deleted your posts")
    
    return redirect(url_for('login'))

# posts -------------------------------------------------------
@app.route('/index2', methods=['POST','GET'])
@login_required    
def index2():
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=2)

    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)

    
    #posts = Post.query.order_by(Post.date_posted.desc()).all()
    # image_file = url_for('static', filename='profile_pics/' )
    # conn = sqlite3.connect('sqlite.db') 
    # c = conn.cursor()
    # c.execute('SELECT * FROM post order by id desc')
    # rows = c.fetchall()
    #
     
    

    return render_template('index2.html', posts=posts, image_file=image_file, user=current_user, post= Post, postlike= PostLike)

    # return render_template('index2.html')

@app.route("/create_new", methods=["POST", "GET"])
def create_new():

    # error = None
    # success = None
    #store the form value
    title = request.form["title"]
    date_posted = datetime.now()
    content = request.form.get('editor1')
    #data = request.form.get('ckeditor')
    user_id = session["id"] 

    #         user.username = name
    #         user.email = email
    #         user.set_password(password)
            
    conn = sqlite3.connect('sqlite.db') 
    c = conn.cursor()
    c.execute("""INSERT INTO Post (title, date_posted, content, user_id) VALUES (?,?,?,?)""", (title, date_posted, content, user_id))
    flash("The post has been added")
    c.connection.commit()
    c.close()

    return redirect(url_for('index2'))

@app.route('/delete_post/<string:id_post>', methods = ['GET'])
def delete_post(id_post):
    id = id_post
    conn = sqlite3.connect('sqlite.db') 
    c = conn.cursor()
    c.execute("DELETE FROM post WHERE id=(?)", [id]) 

    c.connection.commit()
    c.close()
    
    flash("The post has been deleted")
    
    return redirect(url_for('index2'))

# create comments per post -------------------------------
@app.route("/create-comment/<post_id>", methods=['POST'])
@login_required
def create_comment(post_id):
    text = request.form.get('text')

    if not text:
        flash('Comment cannot be empty.', category='error')
    else:
        post = Post.query.filter_by(id=post_id)
        if post:
            comment = Comment(content=text, author=current_user.id, post_id=post_id)
            db.session.add(comment)
            db.session.commit()
        else:
            flash('Post does not exist.', category='error')

        

    return redirect(url_for('index2'))

# delete comment
@app.route("/delete-comment/<comment_id>")
@login_required
def delete_comment(comment_id):
    comment = Comment.query.filter_by(id=comment_id).first()
    if not comment:
        flash('Comment does not exist.', category='error')
        # current_user.id != comment.author
        #  current_user.id != comment.post.author
        
    elif current_user.id != comment.post.user_id and current_user.id != comment.author:
        flash('You do not have permission to delete this comment.', category='error')
    else:
        db.session.delete(comment)
        db.session.commit()

    return redirect(url_for('index2'))

# likes and unlikes post
@app.route('/like/<int:post_id>/<action>')
@login_required
def like_action(post_id, action): 
      p = Post.query.filter_by(id = 1).first()
      p.likes.count()
      post = Post.query.filter_by(id=post_id).first_or_404()
      if action == 'like':
        current_user.like_post(post)
        db.session.commit()
      if action == 'unlike':
        current_user.unlike_post(post)
        db.session.commit()
      return redirect(request.referrer)


#send mail reset password ------------------------------------------
def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Žiadosť o obnovenie hesla ',
                  sender='noreply@demo.com',
                  recipients=[user.email])
    msg.body = f'''Ak chcete obnoviť svoje heslo, kliknite na nasledujúci odkaz: 
{url_for('reset_token', token=token, _external=True)}
Ak ste túto žiadosť neodoslali, jednoducho tento e-mail ignorujte a nebudú vykonané žiadne zmeny. 
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
        flash('Ide o neplatný alebo vypršaný dotaz na reset hesla ', 'warning')
        return redirect(url_for('reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        password = request.form["password"]
        user.set_password(password)
        db.session.commit()
        flash('Your password has been updated! You can log in now.', 'success')
        return redirect(url_for('login'))
    return render_template('reset_token.html', title='Reset Password', form=form)

# chat .......................................
@app.route( '/chat' )
@login_required
def chat():
    time_stamp = time.strftime('%H:%M:%S', time.localtime())
    username = session['name']
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template( './ChatApp.html', image_file=image_file, username=username, time_stamp=time_stamp )

def messageRecived():
  print( 'message was received!!!' )

@socketio.on( 'my event' )
def handle_my_custom_event( json ):
  print( 'recived my event: ' + str( json ) )
  socketio.emit( 'my response', json, callback=messageRecived )

@socketio.on('connect')
def test_connect(auth):
    username = session['name']
    emit('my response', {'data': 'Connected' + username})

@socketio.on('disconnect')
def disconnected():
    print('Disconnected')

# @socketio.on('disconnect')
# def disconnect():
#     username = session['name']
#     disconnect('my response', {'data': 'disConnected' + username})
#     print('Client disconnected')

# ..........................................

def gen_rnd_filename():
    filename_prefix = datetime.now().strftime('%Y%m%d%H%M%S')
    return '%s%s' % (filename_prefix, str(random.randrange(1000, 10000)))

@app.route('/ckupload/', methods=['POST', 'OPTIONS'])
def ckupload():
    """CKEditor file upload"""
    error = ''
    url = ''
    callback = request.args.get("CKEditorFuncNum")
    if request.method == 'POST' and 'upload' in request.files:
        fileobj = request.files['upload']
        fname, fext = os.path.splitext(fileobj.filename)
        rnd_name = '%s%s' % (gen_rnd_filename(), fext)
        filepath = os.path.join(current_app.static_folder, 'upload', rnd_name)
        dirname = os.path.dirname(filepath)
        if not os.path.exists(dirname):
            try:
                os.makedirs(dirname)
            except:
                error = 'ERROR_CREATE_DIR'
        elif not os.access(dirname, os.W_OK):
            error = 'ERROR_DIR_NOT_WRITEABLE'
        if not error:
            fileobj.save(filepath)
            url = url_for('static', filename='%s/%s' % ('upload', rnd_name))
    else:
        error = 'post error'
    res = """<script type="text/javascript"> 
             window.parent.CKEDITOR.tools.callFunction(%s, '%s', '%s');
             </script>""" % (callback, url, error)
    response = make_response(res)
    response.headers["Content-Type"] = "text/html"
    return response
    

if __name__ == "__main__":
        app.run(host='0.0.0.0', port=80, DEBUG=True)