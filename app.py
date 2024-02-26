from flask import Flask, request, redirect, url_for, render_template, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from PIL import Image
import requests
import socket
#from geoip import geolite2
from ipwhois import IPWhois


# pip3 install maxminddb
# pip3 install maxminddb-geolite2
from geolite2 import geolite2

# Initialize Flask app and database
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SECRET_KEY'] = 'secret_key'
db = SQLAlchemy(app)

# database models definitions
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    photo = db.Column(db.String(100), nullable=False)
    ip_address = db.Column(db.String(20), nullable=False)
    geo_location = db.Column(db.String(100), nullable=False)
    website_url = db.Column(db.String(100), nullable=False)
    website_ip = db.Column(db.String(20), nullable=False)
    website_geo_location = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20), nullable=True)
    address = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(50), nullable=False)
    country = db.Column(db.String(50), nullable=False)
    is_suspicious = db.Column(db.Boolean, default=False)

# home page route
@app.route('/')
def index():
    return render_template('index.html')

# route to handle file upload
@app.route('/upload', methods=['POST'])
def upload():
    if 'photo' not in request.files:
        flash('No file part')
        return redirect(request.url)
    file = request.files['photo']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    if file and allowed_file(file.filename):  # check if the file is allowed
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Extract metadata from the image
        with Image.open(file_path) as img:
            image_format = img.format
            image_size = img.size
            exif_entries = img._getexif().items()

        print(f'image_format: {image_format}, image_size: {image_size}, exif_entries: {exif_entries}')

        # Get the user's IP address and geo-location
        user_ip = request.remote_addr
        user_country, user_timezone = get_geo_info('50.24.238.28')
        print(f'user_country: {user_country}, user_timezone: {user_timezone}')

#need to find image online has geolocation information and use t for testing.

        # Get the trading website's IP and geo-location
        trading_url = request.form['website_url']
        trading_ip = socket.gethostbyname(trading_url)   #'google.com'
        trading_country, trading_timezone = get_geo_info(trading_ip)

        print(f'trading_country:{trading_country}, trading_timezone : {trading_timezone}')

        # Compare the user-input location with the trading website's geo-location
        user_city = request.form['city']
        user_country_input = request.form['country']
        is_suspicious = (trading_country != user_country_input)

        # Create a new User record and save it to the database
        new_user = User(
            photo=file_path,
            ip_address=user_ip,
            geo_location=user_country + ', ' + user_timezone,
            website_url=trading_url,
            website_ip=trading_ip,
            website_geo_location=trading_country + ', ' + trading_timezone,
            phone_number=request.form['phone_number'],
            address=request.form['address'],
            city=request.form['city'],
            country=request.form['country'],
            is_suspicious=is_suspicious
        )
        db.session.add(new_user)
        db.session.commit()

        # # Show a message if there is a location mismatch
        # if is_suspicious:
        #     flash('The trading website’s location does not match the user input.')
        return redirect(url_for('index'))
    else:
        flash('Allowed file types are png, jpg, jpeg, gif')
        return redirect(request.url)

# upload functionality and IP/Geo-locations logic


UPLOAD_FOLDER = r'C:\Users\Kubra\PycharmProjects\pythonProject5\upload'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Utility function to check file extension
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Utility function to get IP and geo-location
def get_geo_info(ip_address):
    print('\n\n\n')
    print(f'ip_address {ip_address}')
    #ip_address = '50.24.238.28'



    ## Doesn't work, see
    # https://stackoverflow.com/questions/32575666/python-geoip-does-not-work-on-python3-4
    #match = geolite2.lookup(ip_address)
    #if match is not None:
    #    return match.country, match.timezone  # simplified
    #return None, None

    # Alternative,
    # https://stackoverflow.com/a/63328700
    reader = geolite2.reader()
    match = reader.get(ip_address)
    if match:
        print(f'match {match}')
        if 'country' in match:
            return match['country']['names']['en'], '' #for timezone information check another library
        #translate iso code to timezone.
        else:
            print(f'no country in match for {ip_address}')
            return '', '' #string method ''
    else:
        print(f'no match for {ip_address}')
        return '', ''


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
