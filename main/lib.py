from flask import Flask, render_template, request, session, redirect, url_for, jsonify, send_file, Response
from models import db, User, Session
from datetime import datetime
from werkzeug.utils import secure_filename
import os
import uuid
import cv2 # type: ignore
import base64
import requests # type: ignore
import numpy as np # type: ignore
from flask_cors import CORS # type: ignore

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'static/uploads/'
EDITED_FOLDER = 'static/edited/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def index():
    current_user = None
    username = None
    edited_images = []

    if 'user_id' in session:
        user_id = session['user_id']
        user = User.query.get(user_id)
        if user:
            current_user = user
            username = user.username
            edited_images = [f for f in os.listdir(EDITED_FOLDER) if f.startswith(f'edited_{user_id}_')]
            edited_images = [os.path.join(EDITED_FOLDER, img) for img in edited_images]

    return render_template('index.html', current_user=current_user, username=username, edited_images=edited_images)

def login():
    if 'user_id' in session:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username  
            user.last_login = datetime.utcnow()  
            db.session.commit()
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Invalid username or password')
    return render_template('login.html')

def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))

def register():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            error = 'Username already taken. Please choose a different username.'
        else:
            user = User(username=username)
            user.set_password(password)  
            db.session.add(user)
            db.session.commit()
            return redirect(url_for('login'))
    return render_template('register.html', error=error)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def upload_image():
    current_user = None
    username = session.get('username')  
    if 'user_id' in session:
        user_id = session['user_id']
        user = User.query.get(user_id)
        if user:
            current_user = user
    else:
        return redirect(url_for('login'))  
    
    if request.method == 'POST':
        if 'image' not in request.files:
            return 'No image provided', 400
        
        file = request.files['image']
        if file.filename == '':
            return 'No image selected', 400
        
        if file and allowed_file(file.filename):
            filename = str(uuid.uuid4()) + os.path.splitext(file.filename)[1]
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return render_template('edit_image.html', filename=filename, current_user=current_user, username=username)
        else:
            return 'Invalid file type', 400
    elif request.method == 'GET':
        return render_template('upload_image.html', current_user=current_user, username=username)

def edit_image():
    if 'user_id' not in session:
        return redirect(url_for('login')) 

    user_id = session['user_id']
    filename = request.form['filename']
    brightness = float(request.form['brightness']) / 100.0
    contrast = float(request.form['contrast']) / 100.0
    saturation = float(request.form['saturation']) / 100.0
    
    image_path = os.path.join(UPLOAD_FOLDER, filename)
    edited_image_path = os.path.join(EDITED_FOLDER, f'edited_{user_id}_{filename}')  
    
    image = cv2.imread(image_path)
    
    adjusted_image = cv2.convertScaleAbs(image, alpha=brightness, beta=0)
    adjusted_image = cv2.addWeighted(adjusted_image, 1 + contrast, adjusted_image, 0, 0)
    
    hsv = cv2.cvtColor(adjusted_image, cv2.COLOR_BGR2HSV)
    hsv[:, :, 1] = np.clip(hsv[:, :, 1] * saturation, 0, 255)
    adjusted_image = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
    
    os.makedirs(os.path.dirname(edited_image_path), exist_ok=True)
    cv2.imwrite(edited_image_path, adjusted_image)
    
    return jsonify({'edited_image_path': edited_image_path}), 200

def download(filename):
    filepath = os.path.join(EDITED_FOLDER, filename)
    
    return send_file(filepath, as_attachment=True)

def download_image():
    if 'user_id' not in session:
        return redirect(url_for('login')) 
    user_id = session['user_id']
    filename = request.args.get('filename')
    edited_image_path = os.path.join(EDITED_FOLDER, f'edited_{user_id}_{filename}')
    return send_file(edited_image_path, as_attachment=True)

def watermark_image():
    current_user = None
    username = session.get('username')  
    if 'user_id' in session:
        user_id = session['user_id']
        user = User.query.get(user_id)
        if user:
            current_user = user
    else:
        return redirect(url_for('login'))  

    if 'image' not in request.files or 'watermark' not in request.files:
        return render_template('watermark_upload.html', error='Please select both image and watermark files', current_user=current_user, username=username)

    image = request.files['image']
    watermark = request.files['watermark']

    if image.filename == '' or watermark.filename == '':
        return render_template('watermark_upload.html', error='Please select both image and watermark files', current_user=current_user, username=username)

    if image and allowed_file(image.filename) and watermark and allowed_file(watermark.filename):
        files = {
            'image': (image.filename, image.stream, 'image/jpeg'),  
            'watermark': (watermark.filename, watermark.stream, 'image/png')  
        }

        api_url = 'http://127.0.0.1:5002/add_watermark'
        response = requests.post(api_url, files=files)

        if response.status_code == 200:
            return Response(
                response.content,
                mimetype='image/jpeg',
                headers={
                    'Content-Disposition': f'attachment; filename=watermarked_image.jpg'
                }
            )
        else:
            return 'Failed to add watermark to image', 500
    else:
        return render_template('watermark_upload.html', error='Invalid file type', current_user=current_user, username=username)

def crop_image():
    if 'user_id' not in session:
        return redirect(url_for('login')) 

    if request.method == 'GET':
        return render_template('crop_image.html')
    
    elif request.method == 'POST':
        user_id = session['user_id']
        image_data = request.files.get('image')
        cropping_dimensions = request.json.get('cropping_dimensions')

        payload = {
            'cropping_dimensions': cropping_dimensions,
        }
        files = {
            'image': image_data
        }

        api_url = 'http://cropper.us-east-1.elasticbeanstalk.com/api/image/crop/'
        response = requests.post(api_url, data=payload, files=files)

        if response.status_code == 200:
            cropped_image_url = response.json().get('cropped_image_url')
            return render_template('crop_result.html', cropped_image_url=cropped_image_url)
        else:
            error_message = 'Failed to crop image. External API returned status code {}'.format(response.status_code)
            return render_template('crop_error.html', error=error_message), 500

def init_app(flask_app):
    global app
    app = flask_app
