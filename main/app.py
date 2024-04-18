from flask import Flask, request, jsonify
from models import db
import lib

UPLOAD_FOLDER = 'static/uploads/'
EDITED_FOLDER = 'static/edited/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///image_editing.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'your_secret_key'

db.init_app(app)
lib.init_app(app)

@app.route('/')
def index():
    return lib.index()

@app.route('/login', methods=['GET', 'POST'])
def login():
    return lib.login()

@app.route('/logout')
def logout():
    return lib.logout()

@app.route('/register', methods=['GET', 'POST'])
def register():
    return lib.register()

@app.route('/upload_image', methods=['GET', 'POST'])
def upload_image():
    return lib.upload_image()

@app.route('/edit_image', methods=['POST'])
def edit_image():
    return lib.edit_image()

@app.route('/download/<path:filename>', methods=['GET'])
def download(filename):
    return lib.download(filename)

app.route('/crop_image', methods=['GET', 'POST'])(lib.crop_image)

@app.route('/download_image', methods=['GET'])
def download_image():
    return lib.download_image()

@app.route('/watermark_image', methods=['GET', 'POST'])
def watermark_image():
    return lib.watermark_image()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', debug=True, port=5001)
