#Import Flask Library
from flask import Flask, render_template, request, session, url_for, redirect
import pymysql.cursors
import hashlib
import base64

# Finished "Adding Friend Groups", "View visible photos", "Posting a photo", "View further photo info", "Manage follows"
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
    cursor.execute(query, (username, password))
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
    query1 = 'SELECT DISTINCT photo.pId, filePath, postingDate FROM Photo JOIN SharedWith ON (Photo.pID = SharedWith.pID) ' \
        'WHERE SharedWith.groupCreator IN (SELECT BelongTo.groupCreator FROM BelongTo JOIN Person ON ' \
        'BelongTo.username = Person.username WHERE Person.username= %s ) UNION ' \
        'SELECT DISTINCT pID, filePath, postingDate FROM Person JOIN Follow ON (follower = %s) JOIN Photo ' \
        'ON (Photo.poster = Follow.followee) WHERE followStatus = 1 AND allFollowers = 1 UNION SELECT pID, filePath, postingDate ' \
        'FROM Photo JOIN Person ON (Person.username = Photo.poster) WHERE poster = %s ORDER BY postingDate Desc '
    cursor.execute(query1, (user, user, user))
    data = cursor.fetchall()
    for photo in data:
        image = str(base64.b64encode(photo['filePath']).decode('utf-8'))
        photo['filePath'] = image
    cursor.close()
    return render_template('home.html', username=user, posts=data)

        
@app.route('/post', methods=['GET', 'POST'])
def post():
    username = session['username']
    cursor = conn.cursor()
    filePath = request.form['filePath']
    blobData = convertToBinaryData(filePath)

    getAllFollowers = request.form.get('allFollowers')
    allFollowers = 0
    if getAllFollowers == 'on':
        allFollowers = 1

    caption = request.form['caption']
    query = 'INSERT INTO Photo (postingDate, filePath, allFollowers, caption, poster) VALUES(current_timestamp, ' \
            '%s, %s, %s, %s)'
    cursor.execute(query, (blobData, allFollowers, caption, username))
    conn.commit()

    groups_query = "SELECT * FROM BelongTo WHERE username = %s"
    cursor.execute(groups_query, (username))
    group_data = cursor.fetchall()
    pid_query = "SELECT LAST_INSERT_ID()"
    cursor.execute(pid_query)
    pid = cursor.fetchall()
    pid = pid[0]['LAST_INSERT_ID()']
    cursor.close()

    if allFollowers == 0 and group_data:
        return render_template('/select_groups.html', groups=group_data, pid=pid)
    else:
        return redirect(url_for("home"))

@app.route('/tags_and_reacts/<pId>', methods=["GET", "POST"])
def tags_and_reacts(pId):
    cursor = conn.cursor()
    query1 = 'SELECT firstName, lastName FROM Photo JOIN Person ON (Photo.poster = Person.username) WHERE pID = %s'
    cursor.execute(query1, pId)
    poster = cursor.fetchall()

    # Get the tagged users
    query2 = 'SELECT username, firstName, lastName FROM Tag NATURAL JOIN Person WHERE pID = %s AND tagStatus = 1'
    cursor.execute(query2, pId)
    tag_data = cursor.fetchall()

    # Get the names and reactions of users
    query3 = "SELECT username, comment, emoji FROM ReactTo WHERE pID = %s"
    cursor.execute(query3, pId)
    react_data = cursor.fetchall()

    cursor.close()
    return render_template('tags_and_reacts.html', poster=poster, tag_data=tag_data, react_data=react_data)

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
        return redirect(url_for('home'))

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

@app.route('/manage_follows')
def manage_follows():
    username = session['username']
    cursor = conn.cursor()
    # Get pending follow requests
    query = 'SELECT follower FROM Follow WHERE followee = %s AND followStatus = 0'
    cursor.execute(query, username)
    pending_requests = cursor.fetchall()
    cursor.close()
    return render_template('manage_follows.html', pending_requests=pending_requests)

@app.route('/accept_request/<follower>')
def accept_request(follower):
    username = session['username']
    cursor = conn.cursor()

    query = 'UPDATE Follow SET followStatus = 1 WHERE followee = %s AND follower = %s'
    cursor.execute(query, (username, follower))
    conn.commit()
    cursor.close()
    return redirect(url_for('manage_follows'))

@app.route('/delete_request/<follower>')
def delete_request(follower):
    username = session['username']
    cursor = conn.cursor()
    query = 'DELETE FROM Follow WHERE followee = %s AND follower = %s'
    cursor.execute(query, (username, follower))
    conn.commit()
    cursor.close()
    return redirect(url_for('manage_follows'))

@app.route('/send_request', methods=['GET', 'POST'])
def send_request():
    username = session['username']
    followee = request.form['followSearch']
    cursor = conn.cursor()
    query = "INSERT INTO Follow (follower, followee, followStatus) VALUES (%s, %s, 0)"
    cursor.execute(query, (username, followee))
    conn.commit()
    cursor.close()
    return redirect(url_for('manage_follows'))

def convertToBinaryData(filename):
    # Convert digital data to binary format
    with open(filename, 'rb') as file:
        binaryData = file.read()
    return binaryData

app.secret_key = 'some key that you will never guess'
#Run the app on localhost port 5000
#debug = True -> you don't have to restart flask
#for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
    app.run('127.0.0.1', 5000, debug = True)
