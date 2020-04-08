#Import Flask Library
from flask import Flask, render_template, request, session, url_for, redirect
import pymysql.cursors
import hashlib


SALT='cs3083'
#Initialize the app from Flask
app = Flask(__name__)

#Configure MySQL
conn = pymysql.connect(host='localhost',
                       port = 8889,
                       user='root',
                       password='root',
                       db='finstagram',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)

#Define a route to hello function
@app.route('/')
def hello():
    return render_template('index.html')

#Define route for login
@app.route('/login')
def login():
    return render_template('login.html')

#Define route for register
@app.route('/register')
def register():
    return render_template('register.html')

#Authenticates the login
@app.route('/loginAuth', methods=['GET', 'POST'])
def loginAuth():
    #grabs information from the forms
    username = request.form['username']
    password = request.form['password'] + SALT
    hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()

    #cursor used to send queries
    cursor = conn.cursor()
    #executes query
    query = 'SELECT * FROM Person WHERE username = %s and password = %s'
    cursor.execute(query, (username, hashed_password))
    #stores the results in a variable
    data = cursor.fetchone()
    #use fetchall() if you are expecting more than 1 data row
    cursor.close()
    error = None
    if(data):
        #creates a session for the the user
        #session is a built in
        session['username'] = username
        return redirect(url_for('home'))
    else:
        #returns an error message to the html page
        error = 'Invalid login or username'
        return render_template('login.html', error=error)

#Authenticates the register
@app.route('/registerAuth', methods=['GET', 'POST'])
def registerAuth():
    #grabs information from the forms
    username = request.form['username']
    password = request.form['password'] + SALT
    firstName = request.form['firstName']
    lastName = request.form['lastName']
    email = request.form['email']
    hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()

    #cursor used to send queries
    cursor = conn.cursor()
    #executes query
    query = 'SELECT * FROM Person WHERE username = %s'
    cursor.execute(query, (username))
    #stores the results in a variable
    data = cursor.fetchone()
    #use fetchall() if you are expecting more than 1 data row
    error = None
    if(data):
        #If the previous query returns data, then user exists
        error = "This user already exists"
        return render_template('register.html', error = error)
    else:
        ins = 'INSERT INTO Person VALUES(%s, %s, %s, %s, %s)'
        cursor.execute(ins, (username, hashed_password, firstName, lastName, email))
        conn.commit()
        cursor.close()
        return render_template('index.html')


@app.route('/home')
def home():
    user = session['username']
    cursor = conn.cursor()
    query = 'SELECT pID, postingDate FROM Photo NATURAL JOIN SharedWith JOIN BelongTo ON ' \
            '(BelongTo.groupName = SharedWith.groupName) WHERE BelongTo.username = %s UNION ' \
            '(SELECT pID, postingDate FROM Photo WHERE poster = %s) ORDER BY postingDate Desc '
    cursor.execute(query, (user, user))
    data = cursor.fetchall()
    cursor.close()
    return render_template('home.html', username=user, posts=data)

        
@app.route('/post', methods=['GET', 'POST'])
def post():
    username = session['username']
    cursor = conn.cursor()
    filePath = request.form['filePath']
    getAllFollowers = request.form.get('allFollowers')
    allFollowers = 0
    if getAllFollowers == 'on':
        allFollowers = 1

    caption = request.form['caption']
    query = 'INSERT INTO Photo (postingDate, filePath, allFollowers, caption, poster) VALUES(current_timestamp, ' \
            '%s, %s, %s, %s)'
    insertBLOB(filePath, allFollowers, caption, username)
    conn.commit()

    groups_query = "SELECT * FROM BelongTo WHERE username = %s"
    cursor.execute(groups_query, (username))
    group_data = cursor.fetchall()
    pid_query = "SELECT LAST_INSERT_ID()"
    cursor.execute(pid_query)
    pid = cursor.fetchall()
    pid = pid[0]['LAST_INSERT_ID()']
    cursor.close()

    if allFollowers == 0:
        return render_template('/select_groups.html', groups=group_data, pid=pid)
    else:
        return redirect(url_for("home"))

@app.route('/select_blogger')
def select_blogger():
    #check that user is logged in
    #username = session['username']
    #should throw exception if username not found
    
    cursor = conn.cursor()
    query = 'SELECT DISTINCT username FROM Person'
    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()
    return render_template('select_blogger.html', user_list=data)

@app.route('/show_posts', methods=["GET", "POST"])
def show_posts():
    poster = request.args['poster']
    cursor = conn.cursor()
    query = 'SELECT ts, blog_post FROM blog WHERE username = %s ORDER BY ts DESC'
    cursor.execute(query, poster)
    data = cursor.fetchall()
    cursor.close()
    return render_template('show_posts.html', poster_name=poster, posts=data)

@app.route('/logout')
def logout():
    session.pop('username')
    return redirect('/')

@app.route('/add_friend_group')
def add_friend_group():
    return render_template('add_group.html')

@app.route('/friend_group_confirm', methods=["GET", "POST"])
def friend_group_confirmation():
    group_name = request.form['groupName']
    group_owner = session['username']
    description = request.form['description']

    # cursor used to send queries
    cursor = conn.cursor()
    # executes query
    query = 'SELECT * FROM FriendGroup WHERE groupCreator = %s AND groupName = %s'
    cursor.execute(query, (group_owner, group_name))
    # stores the results in a variable
    data = cursor.fetchall()
    # use fetchall() if you are expecting more than 1 data row
    error = None
    if (data):
        # If the previous query returns data, then user exists
        error = "This group name already exists"
        conn.close()
        return render_template('add_group.html', error=error)
    else:
        ins = 'INSERT INTO FriendGroup (groupName, groupCreator, description) VALUES(%s, %s, %s)'
        cursor.execute(ins, (group_name, group_owner, description))
        conn.commit()
        ins = 'INSERT INTO BelongTo (groupName, groupCreator, username) VALUES (%s, %s, %s)'
        cursor.execute(ins, (group_name, group_owner, group_owner))
        conn.commit()
        cursor.close()
        return render_template('home.html')

@app.route('/selectGroupsAuth', methods=["GET", "POST"])
def select_groups():
    username = session['username']
    pid = request.form['PID']

    cursor = conn.cursor()
    groups_query = 'SELECT * FROM BelongTo WHERE username = %s'
    cursor.execute(groups_query, username)
    group_data = cursor.fetchall()

    for group in group_data:
        if request.form.get(group['groupName']):
            query = 'INSERT INTO SharedWith (pID, groupName, groupCreator) VALUES (%s, %s, %s)'
            cursor.execute(query, (pid, group['groupName'], group['groupCreator']))
            conn.commit()
    cursor.close()
    return redirect(url_for('home'))


app.secret_key = 'some key that you will never guess'
#Run the app on localhost port 5000
#debug = True -> you don't have to restart flask
#for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
    app.run('127.0.0.1', 5000, debug = True)
