from Application import app
from flask import render_template, request, url_for, flash, redirect, session, jsonify, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
from Application import db, users, issues, grid_fs
import base64
import codecs
import json

@app.route('/')
@app.route('/home')
def index():
    return render_template('index.html')

@app.route('/about_us')
def aboutus():
    return render_template('aboutus.html')

@app.route('/login', methods = ['GET', 'POST'])
def login():
    if session.get('name'):
        flash("Already Logged In", "info")
        return redirect('/')

    if request.method == "POST":
        if users.find_one({'email':request.form['email']}):
            if check_password_hash(users.find_one({'email':request.form['email']})['password'], request.form['password']):
                session['name'] = users.find_one({'email':request.form['email']})['name']
                session['email'] = request.form['email']
                return redirect("/")
            else:
                flash("Incorrect Password", "danger")
                return redirect("/login")
        else:
            flash("Email Not Found, Register Here", "danger")
            return redirect("/register")
    return render_template('login.html')    

@app.route('/register', methods = ['GET', 'POST'])
def register():
    if session.get('name'):
        flash("Already Registered", "info")
        return redirect('/')

    if request.method == "POST":
        if users.find_one({'email':request.form['email']}):
            flash("Email Already Exist's","danger")
            return redirect("/register")

        else:    
            password = generate_password_hash(request.form['password'])
            users.insert_one({'name':request.form['name'], 'phone_number':request.form['phonenumber'], 'email':request.form['email'], 'password':password})
            flash("You are Successfully Registered","success")
            return redirect("/login")

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('name',None)
    session.pop('email',None)
    return redirect('/')
    
@app.route('/addissue', methods = ["GET", "POST"])
def addissue():
    if session.get('name'):
        if request.method == "POST":
            if issues.find_one({'title':request.form['title'], 'location':request.form['location'], 'date':request.form['date'], 'details':request.form['details'], 'name':session.get('name'), 'email':session.get('email')}):
                flash("Issue Already Exist's","danger")
                return redirect("/issues")

            else:
                status = "Open"
                upvote = list()
                messages = list()
                with grid_fs.new_file(filename = request.files['image'].filename) as fp:
                    fp.write(request.files['image'])
                file_id = fp._id
                grid_fs_file = grid_fs.find_one({'filename':request.files['image'].filename})
                base64_data = codecs.encode(grid_fs_file.read(), 'base64')
                imagedata = base64_data.decode('utf-8')
                if grid_fs.find_one(file_id) is not None:
                    issues.insert_one({'title':request.form['title'], 'location':request.form['location'], 'date':request.form['date'], 'details':request.form['details'], 'name':session.get('name'), 'email':session.get('email'), 'status':status, 'upvote':upvote, 'messages':messages, 'imageid':file_id, 'imagedata':imagedata})
                    flash("Issue Added","success")
                    return redirect("/issues")
                else:
                    flash("Error in Adding Image","danger")
                    return redirect("/addissue")
        return render_template('addissue.html')
    else:
        return redirect('/login')    
    

@app.route('/issues')
def allissues():
    if session.get('name'):
        infos = list(issues.find({}))
        # grid_fs_file = grid_fs.find_one({'filename':'IMG_20200919_131639.jpg'})
        # print(grid_fs.find_one({'filename':'traffic.jpg'}))
        # base64_data = codecs.encode(grid_fs_file.read(), 'base64')
        # image = base64_data.decode('utf-8')
        # print(image)
        # infos[0]['image'] = image
        return render_template('issues.html', infos=infos)
    else:
        return redirect('/login')


@app.route('/editissue/<string:idx>', methods = ["GET", "POST"])
def editissue(idx=None):
    if session.get('name'):
        if request.method == 'POST':
            with grid_fs.new_file(filename = request.files['image'].filename) as fp:
                fp.write(request.files['image'])
            file_id = fp._id
            grid_fs_file = grid_fs.find_one({'filename':request.files['image'].filename})
            base64_data = codecs.encode(grid_fs_file.read(), 'base64')
            imagedata = base64_data.decode('utf-8')
            if grid_fs.find_one(file_id) is not None:
                issues.find_one_and_update({'_id':ObjectId(idx)},{"$set":{'title':request.form['title'], 'location':request.form['location'], 'date':request.form['date'], 'details':request.form['details'], 'name':session.get('name'), 'email':session.get('email'), 'imageid':file_id, 'imagedata':imagedata}})
                flash("Issue Updated","success")
                return redirect('/issues')
        else:
            data = issues.find({'_id':ObjectId(idx)})[0]
            return render_template('editissue.html', data= data)
    else:
        return redirect('/login')

@app.route('/deleteissue/<string:idx>')
def deleteissue(idx=None):
    if session.get('name'):
        issues.delete_one({'_id':ObjectId(idx)})
        flash("Issue Deleted","success")
        return redirect('/myissues')
    else:
        return redirect('/login')

@app.route('/myissues')
def myissue():
    if session.get('name'):
        infos = list(issues.find({'name':session.get('name'), 'email':session.get('email')}))
        return render_template('myissues.html', infos=infos)
    else:
        return redirect('/login')


@app.route('/issues/<string:idx>/messages')
def messages(idx = None):
    if session.get('name'):
        data = issues.find({'_id':ObjectId(idx)})[0]
        a = dict()
        a['id'] = idx
        a['title'] = data['title']
        a['messages'] = data['messages']
        return render_template('message.html', mess = a )
    else:
        return redirect('/login')

@app.route('/issues/<string:idx>/messages/add', methods=["POST", "GET"])
def addmessage(idx=None):
    if session.get('name'):
        if idx==None:
            return redirect('/issues')
        else:
            b ={'name':session.get('name'), 'comment':request.form['comment']}
            issues.update_one({'_id':ObjectId(idx)},{"$push":{'messages':b}},)
            return redirect('/issues/'+str(idx)+'/messages')
    else:
        return redirect('/login')

@app.route('/upvote/<string:idx>')
def upvote(idx=None):
    if session.get('name'):
        b = {'name':session.get('name'), 'email':session.get('email')}
        issues.update_one({'_id':ObjectId(idx)},{"$addToSet":{'upvote':b}})
        return redirect('/issues')
    else:
        return redirect('/login')

@app.route('/issues/<string:idx>/updatestatus', methods = ["POST", "GET"])
def status(idx=None):
    if session.get('name'):
        if request.method == "POST":
            issues.update_one({'_id':ObjectId(idx)},{"$set":{'status':request.form['status']}})
            print(issues.find({}))
            return redirect('/issues')
    else:
        return redirect('/login')



