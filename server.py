import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response, make_response, url_for, session

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)

app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'

db_address = "postgresql+psycopg2://project:6156@127.0.0.1/Iris"

engine = create_engine(db_address)

@app.before_request
def before_request():
	try:
		g.conn = engine.connect()
	except:
		print "An error has occurred: Failed to Connect to the Database."
		import traceback; traceback.print_exc()
		g.conn = None

@app.teardown_request
def teardown_request(exception):
	try:
		g.conn.close()
	except Exception as e:
		pass


@app.route('/')
def index():
	if 'username' in session:
		ifLoggedOn = True
		username = session['username']
		if_dev = session['if_dev']
	else:
		ifLoggedOn = False
		username = None
		if_dev = False

	return render_template("index.html", ifLoggedOn = ifLoggedOn, username = username, if_dev = if_dev)

@app.route('/logout')
def logout():
	if 'username' not in session:
		return redirect(url_for('index'))

	session.pop('username', None)
	session.pop('user_id', None)
	session.pop('if_dev', None)

	return redirect(url_for('index'))

@app.route('/login')
def login():
	
	return render_template("login.html")

@app.route('/login', methods = ['POST'])
def login_authen():

	username = request.form['username']
	password = request.form['password']

	cur = g.conn.execute('SELECT U.user_id, U.username, U.if_dev FROM USERS U WHERE U.username = %s AND U.password = %s', username, password)

	user_id = []
	username = []
	if_dev = []

	for tuple in cur:
		user_id.append(str(tuple[0]))
		username.append(str(tuple[1]))
		if_dev = if_dev.append(bool(tuple[2]))

	cur.close()

	if len(user_id) == 1 and len(username) == 1 and len(if_dev) == 1:
		session['username'] = username[0]
		session['user_id'] = user_id[0]
		session['if_dev'] = if_dev
	else:
		return render_template("login.html", status = 'Invalid Credential: Username and/or Password may be Incorrent.')

	return redirect(url_for('index'))

@app.route('/register')
def register():

	return render_template("register.html")

@app.route('/register', methods = ['POST'])
def register_authen():

	username = request.form['username']
	password = request.form['password']
	try:
		ifdev = bool(request.form['ifdev'])
	except:
		ifdev = False
	if_firstrun = True

	try:
		g.conn.execute('INSERT INTO USERS VALUES (DEFAULT, %s, %s, %s, %s)', username, password, ifdev, if_firstrun)
		return redirect(url_for('login'))
	except:
		return render_template('register.html', status = 'Invalid Credential: Please Try a Different Username/Password Combination.')

##
@app.route('/review',methods = ['GET'])
def review():

	#Verify if it is the first time user vising Iris
	try:
		user_id = session['user_id']
	except:
		return redirect(url_for('login'))

	cur = g.conn.execute('SELECT if_firstrun FROM USERS WHERE USERS.user_id = %s', user_id)
	for i in cur:
		if_firstrun = bool(i[0])

	cur.close()

	if if_firstrun == True and if_dev == False:
		return redirect(url_for('register_product'))

	if if_firstrun == True and if_dev == True:
		return redirect(url_for('add_product'))

	#Accepting Parameters
	try:
		notice = request.args['notice']
	except:
		notice = None

	try:
		current_section_id = int(request.args['section_id'])
	except:
		current_section_id = 0

	#Load Product
	cur = g.conn.execute('SELECT product_id FROM SIGNUP WHERE user_id = %s', user_id)
	for i in cur:
		product_id = i[0]
	cur.close()

	#Load Sections
	section_seq = []
	section_id = []
	section_name = []
	cur = g.conn.execute('SELECT section_id, section_name FROM SECTIONS_NEW WHERE product_id = %s', product_id)
	for i in cur:
		section_id.append(i[0])
		section_name.append(i[1])
	cur.close()

	section_seq = range(0, len(section_id))

	#Load Posts
	post_seq = []
	post_id = []
	post_title = []
	post_content = []
	upvotes = []
	downvotes = []
	usernames = []
	post_time = []

	if current_section_id == 0:
		cur = g.conn.execute('SELECT P.post_id, P.post_title, P.post_content, P.upvotes, P.downvotes, U.username, U.post_time FROM POSTS_NEW P, USERS_POSTS_NEW U WHERE P.product_id = %s AND P.post_id = U.post_id', product_id)
	else:
		cur = g.conn.execute('SELECT P.post_id, P.post_title, P.post_content, P.upvotes, P.downvotes, U.username, U.post_time FROM POSTS_NEW P, USERS_POSTS_NEW U WHERE P.product_id = %s AND P.post_id = U.post_id AND P.section_id = %s', product_id, current_section_id)
	for i in cur:
		post_id.append(i[0])
		post_title.append(i[1])
		post_content.append(i[2])
		upvotes.append(i[3])
		downvotes.append(i[4])
		usernames.append(i[5])
		post_time.append(i[6])
	cur.close()

	post_seq = range(0, len(post_id))

	#Load Configurations
	cur = g.conn.execute('SELECT if_upvote_allowed, if_downvote_allowed, max_votes, if_followup_allowed, if_user_generated_feature_request_allowed FROM DEVS_PRODUCTS WHERE product_id = %s', product_id)
	controls = []
	for i in cur:
		controls.append(bool(i[0]))
		controls.append(bool(i[1]))
		controls.append(bool(i[2]))
		controls.append(bool(i[3]))
		controls.append(bool(i[4]))
	cur.close()

	print product_id

	return render_template('review.html', product_id = product_id, section_seq = section_seq, section_id = section_id, section_name = section_name, post_seq = post_seq, post_id = post_id, post_title = post_title, post_content = post_content, upvotes = upvotes, downvotes = downvotes, usernames = usernames, post_time = post_time, notice = notice, controls = controls, current_section_id = current_section_id)
##
@app.route('/review_addpost', methods = ['GET','POST'])
def review_addpost():
	try:
		product_id = request.form['product_id']
		current_section_id = int(request.form['section_id'])
		post_title = request.form['request_title']
		post_content = request.form['request_content']
	except:
		return redirect(url_for('review'), notice = 'Unable to Complete Your Request.')

	user_id = session['user_id']
	username = session['username']

	replace_section_id = current_section_id

	if current_section_id == 0:
		replace_section_id = 1

	cur = g.conn.execute('INSERT INTO POSTS_NEW VALUES (DEFAULT, %s, %s, %s, %s, 0, 0, false)', replace_section_id, product_id, post_title, post_content)
	cur = g.conn.execute('SELECT post_id FROM POSTS_NEW WHERE product_id = %s AND section_id = %s AND post_title = %s AND post_content = %s', product_id, replace_section_id, post_title, post_content)
	
	for i in cur:
		post_id = i[0]
	
	cur = g.conn.execute('INSERT INTO USERS_POSTS_NEW VALUES (%s, %s, %s, DEFAULT)', user_id, username, post_id)
	cur.close()

	return redirect(url_for('review', section_id = current_section_id))
##
@app.route('/review_addvote', methods = ['GET','POST'])
def review_addvote():
	try:
		upvotes = int(request.form['upvotes'])
		downvotes = int(request.form['downvotes'])
		post_id = int(request.form['post_id'])
		current_section_id = request.form['section_id']
		product_id = request.form['product_id']
		vote_type = request.form['vote_type']
	except:
		return redirect(url_for('review', notice = 'Unable to Complete Your Request'))

	user_id = session['user_id']

	if_upvoted = None
	if_downvoted = None

	cur = g.conn.execute('SELECT if_upvoted, if_downvoted FROM USERS_VOTES_NEW WHERE post_id = %s AND user_id = %s', post_id, user_id)
	for i in cur:
		if_upvoted = i[0]
		if_downvoted = i[1]

	if vote_type == 'upvote' and if_upvoted:
		return redirect(url_for('review', notice = "You Have Already Voted For This Feature Request"))

	if vote_type == 'downvote' and if_downvoted:
		return redirect(url_for('review', notice = "You Have Already Voted For This Feature Request"))

	if vote_type == 'upvote' and if_downvoted:
		downvotes = downvotes - 1
		g.conn.execute('UPDATE USERS_VOTES_NEW SET if_upvoted = True, if_downvoted = False WHERE post_id = %s AND user_id = %s', post_id, user_id)

	if vote_type == 'downvote' and if_upvoted:
		upvotes = upvotes - 1
		g.conn.execute('UPDATE USERS_VOTES_NEW SET if_upvoted = False, if_downvoted = True WHERE post_id = %s AND user_id = %s', post_id, user_id)

	if not if_upvoted and not if_downvoted and vote_type == 'upvote':
		g.conn.execute('INSERT INTO USERS_VOTES_NEW VALUES (%s, %s, True, False)', user_id, post_id)

	if not if_upvoted and not if_downvoted and vote_type == 'downvote':
		g.conn.execute('INSERT INTO USERS_VOTES_NEW VALUES (%s, %s, False, True)', user_id, post_id)

	cur = g.conn.execute('UPDATE POSTS_NEW SET upvotes = %s, downvotes = %s WHERE post_id = %s AND product_id = %s', upvotes, downvotes, post_id, product_id)
	cur.close()

	return redirect(url_for('review', section_id = current_section_id, notice = "Your Vote Has Been Cast."))
##
@app.route('/register_product')
def register_product():
	
	try:
		user_id = session['user_id']
	except:
		return redirect(url_for('login'))

	cur = g.conn.execute('SELECT * FROM SIGNUP WHERE user_id = %s', user_id)
	ifsigned = []
	for i in cur:
		ifsigned.append(i)
	if len(ifsigned) != 0:
		return redirect(url_for('review'))

	cur.close()

	cur = g.conn.execute('SELECT D.product_id, D.product_name, U.username FROM Users U, DEVS_PRODUCTS D WHERE D.user_id = U.user_id')
	
	product_id = []
	product_name = []
	developer_name = []

	for i in cur:
		product_id.append(i[0])
		product_name.append(i[1])
		developer_name.append(i[2])

	cur.close()

	seq = range(0, len(product_id))

	return render_template('register_product.html', seq = seq, product_id = product_id, product_name = product_name, developer_name = developer_name)

@app.route('/register_product', methods = ['POST'])
def register_product_accessDB():

	product_selected = request.form['product_selected']
	user_id = session['user_id']

	cur = g.conn.execute('INSERT INTO SIGNUP VALUES (%s, %s, 3)', user_id, product_selected)
	cur.close()

	cur = g.conn.execute('UPDATE USERS SET if_firstrun = false WHERE user_id = %s', user_id)
	cur.close()

	return redirect(url_for('review'))
##
@app.route('/followup', methods = ['GET'])
def follow_up_return():
	return redirect(url_for('review'))
##
@app.route('/followup', methods = ['POST'])
def follow_up():
	upvotes = int(request.form['upvote'])
	downvotes = int(request.form['downvote'])
	post_id = request.form['postid']
	section_id = request.form['sectionid']
	section_name = request.form['sectionname']
	product_id = request.form['productid']
	post_title = request.form['posttitle']
	post_content = request.form['postcontent']

	try:
		newfollowup_content = request.form['requestcontent']
		cur = g.conn.execute('INSERT INTO FOLLOWUPS_NEW VALUES (DEFAULT, %s, %s, %s, %s)', post_id, section_id, product_id, newfollowup_content)
		cur.close()
	except:
		pass

	ifdevanswered = False
	ifnotice = False

	cur = g.conn.execute('SELECT followup_content FROM FOLLOWUPS_NEW WHERE product_id = %s AND section_id = %s AND post_id = %s', product_id, section_id, post_id)
	follow_ups = []
	for i in cur:
		follow_ups.append(i[0])
	follow_up_seq = range(0, len(follow_ups))

	return render_template('follow_up.html', post_id = post_id, section_name = section_name, product_id = product_id, upvotes = upvotes, downvotes = downvotes, post_title = post_title, post_content = post_content, ifdevanswered = ifdevanswered, ifnotice = ifnotice, follow_up_seq = follow_up_seq, follow_ups = follow_ups)

##
@app.route('/control_panel', methods = ['GET'])
def control_panel():

	try:
		user_id = session['user_id']
	except:
		return redirect(url_for('login'))

	if_dev = session['if_dev']
	if if_dev == False:
		return redirect(url_for('index'))

	cur = g.conn.execute('SELECT D.product_name FROM DEVS_PRODUCTS D WHERE D.user_id = %s', user_id)
	product_name = ''
	for i in cur:
		product_name = i[0]
	cur.close()

	if product_name == '':
		return redirect(url_for('add_product'))

	return render_template('control_panel.html', product_name = product_name, user_id = user_id)
##
@app.route('/add_product', methods = ['GET'])
def add_product():

	return render_template('add_product_dev.html')

##
@app.route('/add_product', methods = ['POST'])
def add_product_accessDB():
	product_name = request.form['new_productname']
	if_upvote_allowed = bool(request.form['ifupvote'])
	if_downvote_allowed = bool(request.form['ifdownvote'])
	try:
		max_votes = int(request.form['ifmaxvote'])
	except:
		max_votes = -1
	if_user_generated_feature_request_allowed = bool(request.form['ifuserpostnewfeature'])
	if_followup_allowed = bool(request.form['iffollowup'])
	user_id = session['user_id']

	cur = g.conn.execute('INSERT INTO DEVS_PRODUCTS VALUES (%s, DEFAULT, %s, %s, %s, %s, %s, %s)', user_id, product_name, if_upvote_allowed, if_downvote_allowed, max_votes, if_followup_allowed, if_user_generated_feature_request_allowed)
	cur.close()

	return redirect(url_for('control_panel'))
##
@app.route('/control_panel/manage_feature', methods = ['GET'])
def manage_feature():
	return render_template('manage_feature.html')
##
@app.route('/control_panel/manage_section', methods = ['GET'])
def manage_section():
	return render_template('manage_section.html')
##
@app.route('/control_panel/analysis', methods = ['GET'])
def analyze():
	return render_template('analysis.html')
##
@app.route('/control_panel/sentiment_analysis_catalog', methods = ['GET'])
def sentiment_analysis_catalog():
	return render_template('sentiment_analysis_catalog.html')

##
@app.route('/control_panel/sentiment_analysis_result', methods = ['GET'])
def sentiment_analysis_result():
	return render_template('sentiment_analysis_result.html')
##
if __name__ == "__main__":
	import click

	@click.command()
	@click.option('--debug', is_flag=True)
	@click.option('--threaded', is_flag=True)
	@click.argument('HOST', default='0.0.0.0')
	@click.argument('PORT', default=5000, type=int)
	def run(debug, threaded, host, port):
		HOST, PORT = host, port
		print "Server Now Running on %s:%d" % (HOST, PORT)
		app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)

	run()

