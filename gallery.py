"""
Main script for running the image viewer application.

This script initializes metadata for the images and reads EXIF data from images.
If the metadata already exists, it is read from disk. Otherwise, metadata is initialized
by calling the `metadata_initialization` function. Similarly, if the EXIF data has
been previously read and saved to disk, it is read from disk, otherwise, EXIF data is
read by calling `mp_bulk_exif_read` function.

The application is then started by calling the `run` method of the `Flask` object.

Usage:
    python gallery.py --imagedir <image folder>
"""

import ast
from logging.handlers import RotatingFileHandler
import os
import sys
import traceback
from flask import Flask, url_for, render_template, send_from_directory,redirect, request, make_response, stream_template, jsonify, send_file
import logging
from jinja2 import Environment, FileSystemLoader
import random
from PIL import Image
import pandas as pd
import argparse
from pathlib import Path
from io import BytesIO
import hashlib
import base64
from datetime import datetime
from colorlog import ColoredFormatter
import multiprocessing
import time
import json
import re
import configparser
import piexif
import piexif.helper

# Increase the maximum pixel count limit
Image.MAX_IMAGE_PIXELS = None

app = Flask(__name__)

def dir_path(string):
    """Validate and return a directory path.

    Args:
        string (str): The directory path to validate.

    Returns:
        str: The validated directory path.

    Raises:
        NotADirectoryError: If the path is not a valid directory.

    """
    p = Path(string)
    if p.is_dir():
        return string
    else:
        raise NotADirectoryError(string)

def filter_images_in_image_folder_path():
    logger.debug(image_folder)
    filtered_images = []
    for f in image_folder.glob('**/*'):
        if f.is_file() and is_valid_image_extension(f.name):
            file_path = str(f)
            filtered_images.append(file_path)
    return filtered_images

def check_images_in_dataframe(image_list, df):
    """
    Checks whether all the images in image_list are in the DataFrame df.
    Assumes that the DataFrame is indexed by sha256 keys.
    """
    sha256_keys = [hashlib.sha256(image.encode()).hexdigest() for image in image_list]
    result = df.index.isin(sha256_keys)
    if sum(result) == len(image_list):
        logger.debug("check_images_in_dataframe: True")
        return True
    else:
        logger.debug("check_images_in_dataframe: False")
        return False

def remove_missing_sha256(dataframe, image_list):
    sha256_set = set(hashlib.sha256(image.encode()).hexdigest() for image in image_list)
    missing_sha256 = dataframe.index.difference(sha256_set)
    logger.debug(f"Length before drop: {len(dataframe)}")
    dataframe = dataframe.drop(missing_sha256)
    logger.debug(f"Length after drop: {len(dataframe)}")
    return dataframe

def my_type(value):
    return type(value).__name__

def get_args(argv=None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        argv (List[str], optional): List of arguments to parse. Defaults to None.

    Returns:
        argparse.Namespace: The parsed command-line arguments.

    """
    parser = argparse.ArgumentParser(
        description="Image viewer built with Flask.")
    parser.add_argument('--config', type=argparse.FileType('r'),
                        help='Path to configuration file')
    parser.add_argument('--imagedir', type=dir_path,
                        help='Path to image directory')
    parser.add_argument('--port', default=8000, type=int,
                        help='Port number for the web server')
    parser.add_argument('--log', dest='loglevel', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help='Set the logging level', default='ERROR')
    parser.add_argument('--cleanup', default=False, type=bool, help="Clean up metadata for deleted files.")
    parser.add_argument('--aesthetic', default=False, type=bool, help="Calculate Aesthetic score for images using method derived from https://github.com/AUTOMATIC1111/stable-diffusion-webui/discussions/1831")
    args, unknown = parser.parse_known_args(argv)

    if args.config:
        config = configparser.ConfigParser()
        config.read_file(args.config)
        if 'app' in config:
            app_config = config['app']
            if 'imagedir' in app_config:
                imagedir = Path(app_config['imagedir'])
                if imagedir.exists() and imagedir.is_dir():
                    args.imagedir = imagedir
                    print(f"Using imagedir from configuration file: {imagedir}")
                else:
                    print(f"Invalid imagedir specified in configuration file: {imagedir}")
                    sys.exit(1)
            if 'port' in app_config:
                args.port = app_config['port']
            if 'log' in app_config:
                args.log = app_config['log']

    return args

bulk_exif_data = {}
imgview_data = {}
view_mode = "all"
image_folder = ""
metadata_folder = ""
metadata_subdir = ""
thumbnail_folder = ""
thumbnails_sent = []
filtered_images = []
aesthetic_engine = None
args = get_args(sys.argv[1:])

logger = logging.getLogger(__name__)
formatter = ColoredFormatter(
    "%(log_color)s%(levelname)-8s%(asctime)s [%(levelname)s][%(funcName)s] line:%(lineno)d %(message)s",
    datefmt=None,
    reset=True,
    log_colors={
        'DEBUG':    'cyan',
        'INFO':     'green',
        'WARNING':  'yellow',
        'ERROR':    'red',
        'CRITICAL': 'red,bg_white',
    },
    secondary_log_colors={},
    style='%'
)

# Set up the root logger with a custom formatter and a console handler
#logging.basicConfig(level=logging.DEBUG, format='', datefmt='%Y-%m-%d %H:%M:%S')
logging.getLogger().setLevel(args.loglevel) # Add this line to set the root logger level to DEBUG
console_handler = logging.StreamHandler()
console_handler.setLevel(args.loglevel)
console_handler.setFormatter(formatter)
logging.getLogger().addHandler(console_handler)

def b64encode(data):
    """Encode binary data in base64.

    Args:
        data (bytes): The binary data to encode.

    Returns:
        str: The base64-encoded data.

    """
    return base64.b64encode(data).decode('utf-8')

def strip_chars(string, chars):
    for char in chars:
        string = string.replace(char, '')
    return string

app.jinja_env.filters['strip_chars'] = strip_chars
app.jinja_env.filters['json_loads'] = json.loads
app.jinja_env.globals['type'] = type
app.jinja_env.filters['my_type'] = my_type
app.jinja_env.filters['b64encode'] = b64encode

def get_thumbnail_from_image(image):
    """Get the thumbnail of an image.

    Args:
        image_name (str): The name of the image to get the thumbnail for.

    Returns:
        io.BytesIO: The thumbnail image.

    """
    thumbnail_folder = metadata_subdir / 'thumbnails'
    thumbnail_folder.mkdir(parents=True, exist_ok=True)

    thumbnail_name = Path(image).name[:-4] + '_thumbnail.jpg'
    thumbnail_path = thumbnail_folder / thumbnail_name
    logger.debug(f"Thumbnail folder: {thumbnail_folder} Thumbnail path:{thumbnail_path}")

    if not thumbnail_path.exists():
        image_file = image
        img = Image.open(image_file)
        if img.format == "PNG":
            img = img.convert("P")
            img = img.convert("RGB")
        ratio = img.width / img.height
        img.thumbnail((int(256 * ratio), 256), Image.LANCZOS)
        img.save(thumbnail_path, format='JPEG', quality=85)

    with open(thumbnail_path, 'rb') as f:
        return BytesIO(f.read())

# Define a sorting function to sort based on filename and parent folder
def sort_by_filename_and_parent_folder(image_path):
    # Get the parent folder and filename using pathlib
    path = Path(image_path)
    parent_folder = path.parent
    filename = path.name
    
    # Sort first by parent folder, then by filename
    return (parent_folder, filename)

def fetch_thumbnails(limit, offset, imgsrc):
    """Fetch a list of image thumbnails.

    Args:
        limit (int): The maximum number of thumbnails to fetch.
        offset (int): The offset of the first thumbnail to fetch.

    Returns:
        List[Dict[str, Any]]: A list of thumbnail responses and image source URLs.

    """
    logger.debug("limit: %d. offset: %d. imgsrc: %s" % (limit, offset, imgsrc))
    images = get_image_names_in_image_dir()
    if offset > len(images):
        offset = len(images) - limit
    if limit+offset > len(images):
        offset = len(images) - limit
    thumbnails = []
    sorted_image_paths = sorted(images[offset:offset+limit], key=sort_by_filename_and_parent_folder)
    for image in sorted_image_paths:
        thumbnail = (get_thumbnail_from_image(image))
        response = make_response(thumbnail)
        response.headers.set('Content-Type', 'image/jpeg')
        response.headers.set('Content-Disposition', 'inline', filename=image)
        thumbnails.append({"response": response, "image_src": url_for('image_viewer', image_name=image)})
    logger.debug(len(thumbnails))
    return thumbnails

# Route to display the filtered images
@app.route("/filter_images", methods=["POST"])
def filter_images():
    try:
        logger.debug("filtering")
        global imgview_data
        for key, value in request.form.items():
            logger.debug(f"{key}: {value}")
        # Retrieve user input from AJAX request
        try:
            search_query = request.form.get("search_query")
            favorites = request.form.get("favorites") if request.form.get("favorites") is not None else None
            rating_str = request.form.get("rating")
            rating = int(rating_str) if rating_str and rating_str.strip() else None
            tags = request.form.get("tags") if request.form.get("tags") is not None else None
            categories = request.form.get("categories") if request.form.get("categories") is not None else None
            logger.debug(f"search_query: {search_query} favorites: {favorites} rating: {rating} tags: {tags} categories: {categories}")
        except Exception as e:
            logger.error(str(e))
            return handle_value_error(e)

        # Filter the metadata dataframe based on user input
        filtered_df = imgview_data.copy()
        filtered_exif_df = bulk_exif_data.copy()
        logger.debug(filtered_df)
        if search_query:
            logger.debug("search_query")
            found_images = [(hashlib.sha256(elem.encode()).hexdigest(), elem) for elem in get_image_names_in_image_dir() if search_query in elem]
            logger.debug(filtered_exif_df)
            if found_images:
                found_hashes = [x[0] for x in found_images]
                filtered_df = filtered_df.loc[found_hashes]
            else:
                filtered_df = None
                
        if not filtered_df.empty:        
            if favorites in ['True', 'False']:
                favorites = ast.literal_eval(favorites)
                filtered_df = filtered_df[filtered_df["Favorites"] == favorites]
            if rating:
                logger.debug(f"rating is not None: {rating}")
                filtered_df["Rating"] = filtered_df["Rating"].astype(int)
                filtered_df = filtered_df[filtered_df["Rating"] >= rating]
            if tags:
                logger.debug(f"tags is not None: {tags}")
                logger.debug(filtered_df["Tags"].dtype)
                filtered_df["Tags"] = filtered_df["Tags"].apply(lambda x: [x] if not isinstance(x, list) else x)
            if categories:
                logger.debug(f"categories is not None: {categories}")
                filtered_df = filtered_df[filtered_df["Categorization"].apply(lambda x: any(categories in category for category in x))]


            # Retrieve list of filtered image filenames
            logger.debug(filtered_df)
            filtered_image_list = filtered_df.index.tolist()
            logger.debug(filtered_image_list)
            if len(filtered_image_list) > 0:
                global filtered_images
                filtered_images = [x for x in filtered_images if hashlib.sha256(x.encode()).hexdigest()  in filtered_image_list]
                if len(filtered_images) == 0:
                    filtered_images = sorted(filter_images_in_image_folder_path(), key=sort_by_filename_and_parent_folder)
                    logger.debug(f"Resetting filtered_images to the ones in your vieweing directory. You have {len(filtered_images)} in your viewing direcotry images.")
                    response = url_for('zen', message="No images found for your filter")
                else:
                    logger.debug(filtered_images)
                    response = url_for('image_viewer', image_name=get_random_image())
                    logger.debug(response)
            else:
                #filtered_images = filter_images_in_image_folder_path()
                filtered_images = sorted(filter_images_in_image_folder_path(), key=sort_by_filename_and_parent_folder)
                logger.debug(f"Resetting filtered_images to the ones in your vieweing directory. You have {len(filtered_images)} in your viewing direcotry images.")
                response = url_for('zen', message="No images found for your filter")
                logger.debug(response)
        else:
            #filtered_images = filter_images_in_image_folder_path()
            filtered_images = sorted(filter_images_in_image_folder_path(), key=sort_by_filename_and_parent_folder)
            logger.debug(f"Resetting filtered_images to the ones in your vieweing directory. You have {len(filtered_images)} in your viewing direcotry images.")
            response = url_for('zen', message="No images found for your filter")
            logger.debug(response)
        #return redirect(url_for('image_viewer', image_name=get_random_image()))
        return jsonify(response)
    except Exception as e:
        logger.error(traceback.format_exc())
        return bad_request_error(e)

@app.route('/')
def index(): 
    """Redirect to the image_viewer route with a randomly selected image.

    Returns:
        Response: Flask redirect response to the image_viewer route.
    """
    return redirect(url_for('image_viewer', image_name=get_random_image()))

@app.route('/numimages')
def get_num_images():
    """Get the number of images in the image directory.

    Returns:
        Response: Flask JSON response containing the number of images.
    """
    num_images = len(get_image_names_in_image_dir()) 
    return jsonify(num_images=num_images)

def image_data_thumbnails(image_name):
    """Get the thumbnail data for the given image.

    Args:
        image_name (str): The name of the image to get the thumbnail for.

    Returns:
        Response: Flask response containing the thumbnail data for the image.
    """
    logger.debug(image_folder)
    logger.debug(image_name)

    image_data = get_thumbnail_from_image(image_name)
    response = make_response(image_data)
    response.headers.set('Content-Type', 'image/jpeg')
    response.headers.set('Content-Disposition', 'inline', filename=image_name)
    response.headers.set('Cache-Control', 'public,max-age=1209600')
    return response

@app.route('/thumbnails')
def thumbnails():
    """Get a list of thumbnail images.

    Returns:
        Response: Flask response rendering the thumbnail partial template with the list of thumbnails.
    """
    limit = request.args.get('limit', 30, type=int)
    offset = request.args.get('offset', 0, type=int)
    imgsrc = request.args.get('imgsrc', None, type=str)
    logger.debug("imgsrc is: %s", imgsrc)
    if imgsrc == None:
        pass
    else:
        offset = get_image_index_by_name(imgsrc)
    if offset == None:
        offset = 0
    # Fetch thumbnail data from the server
    logger.debug("sending this to fetch_thumbnails limit: %d. offset: %d." % (limit, offset))
    thumbnails = fetch_thumbnails(limit=limit, offset=offset, imgsrc=imgsrc)
    thumbnails_sent.append((offset, limit))
    logger.debug(thumbnails_sent) # Ask ChatGPT about this way of doing it later.
    # Render the thumbnail partial using Jinja2 template
    return render_template('thumbnail_partial.html', thumbnails=thumbnails)

@app.route("/image")
def image_data():
    """
    Returns the image data for the specified image name.

    Args:
        image_name (str): The name of the image to return.

    Returns:
        flask.Response: The HTTP response containing the image data.
    """
    image_name = request.args.get("image_name")
    image_path = Path(image_name)
    if not image_path.exists():
        bad_request_error("File doesn't exist")
    user_agent = request.user_agent.string
    is_mac = 'mac' in user_agent.lower()
    logger.debug(f"is mac:{is_mac}")
    logger.debug(image_path.resolve())
    if is_mac:
        response = make_response(send_from_directory(str(image_path.parent), image_path.name))
    else:
        response = make_response(send_file(str(image_path)))
    response.headers.set('Content-Type', 'image/jpeg')
    response.headers.set('Content-Disposition', 'inline', filename=image_path.name)
    response.headers.set('Cache-Control', 'public,max-age=1209600')
    return response

@app.route("/imagedirection")
def image_direction():
    """
    Returns the image data for the specified image name.

    Args:
        image_name (str): The name of the image to return.
        direction (str): The direction of navigation. Can be either "next" or "prev".

    Returns:
        flask.Response: The HTTP response containing the image data.
    """
    image_name = request.args.get("image_name")
    logger.debug(image_name)
    image_path = Path(image_name)
    logger.debug(image_path)
    if not image_path.exists():
        bad_request_error("File doesn't exist")
    image_index = get_image_index_by_name(image_name)
    number_of_images = len(get_image_names_in_image_dir()) 
    # Determine the new index based on the direction parameter
    direction = request.args.get("direction")
    logger.debug(f"direction:{direction} number_of_images:{number_of_images} image_index:{image_index}")
    if direction == "next":
        new_index = (image_index + 1) % number_of_images
    elif direction == "prev":
        new_index = (image_index - 1) % number_of_images
    else:
        new_index = image_index

    # Get the new image name based on the new index
    image_name = get_selected_image_by_index(new_index)
    return redirect(url_for('image_viewer', image_name=image_name))

@app.route('/browse', methods=['POST'])
def browse():
    """
    Changes the image folder to the specified folder path.

    Returns:
        flask.Response: The HTTP response redirecting to the homepage.
    """
    if not request.form.get('folder_path'):
        return bad_request_error('folder_path is empty or not present in form data')
    incoming_image_folder_path = Path(request.form.get('folder_path'))
    logger.debug(f"Incodming image folder path: {incoming_image_folder_path}")
    global image_folder
    if image_folder == incoming_image_folder_path:
        logger.warning(f"We are already in this folder.")
        return zen("We are already in this folder.")
    image_folder = incoming_image_folder_path
    logger.debug(image_folder)
    global metadata_subdir
    metadata_subdir = metadata_folder / image_folder.name
    metadata_subdir.mkdir(parents=True, exist_ok=True)
    logger.debug(metadata_subdir)
    global thumbnail_folder
    thumbnail_folder = metadata_subdir / 'thumbnails'
    thumbnail_folder.mkdir(parents=True, exist_ok=True)
    logger.debug(thumbnail_folder)
    global filtered_images
    #filtered_images = [f.name for f in image_folder.iterdir() if f.is_file() and is_valid_image_extension(f.name)]
    #filtered_images = filter_images_in_image_folder_path()
    filtered_images = sorted(filter_images_in_image_folder_path(), key=sort_by_filename_and_parent_folder)
    logger.debug(f"filtered_images: {filtered_images}")
    start_time = time.time()
    
    global bulk_exif_data
    # Check if EXIF data already exists
    exif_df_path = metadata_subdir.joinpath("exif_df.csv")
    if exif_df_path.exists():
        bulk_exif_data = pd.read_csv(exif_df_path)
        bulk_exif_data.set_index('sha256', inplace=True)
        #bulk_exif_data['Sampler settings'] = pd.array(bulk_exif_data['Sampler settings'].tolist())
        logger.warning(len(bulk_exif_data))
    else:
        logger.debug("Creating bulk exif data")
        # Read EXIF data for images
        bulk_exif_data = mp_bulk_exif_read(filtered_images)
    
    global imgview_data
    # Check if metadata already exists
    metadata_path = metadata_subdir.joinpath("imgview_metadata.csv")
    if metadata_path.exists():
        imgview_data = pd.read_csv(metadata_path)
        imgview_data.set_index('sha256', inplace=True)
        logger.warning(len(imgview_data))
    else:
        logger.debug("Initializing imgview data")
        # Initialize metadata for images
        imgview_data = metadata_initialization()
    
    end_time = time.time()
    execution_time = end_time - start_time
    logger.debug("Changing directory took: {:.2f} seconds".format(execution_time))
    return redirect(url_for('image_viewer', image_name=get_random_image()))

@app.route("/zen/<message>", methods=['GET'])
def zen(message):
    return render_template("zen.html", message=message)

@app.route('/save', methods=['PUT'])
def save():
    """
    Saves the metadata to the csv
    """
    try:
        imgview_data.to_csv(metadata_subdir.joinpath("imgview_metadata.csv"), index=True, header=True)
        logger.debug("Saving metadata to disk")
        return jsonify("Saved"), 200
    except ValueError as e:
        logger.error(f"Error saving metadata: {str(e)}")
        return jsonify("Error saving metadata"), 500

@app.route('/resetfilter', methods=['POST'])
def reset_filter():
    """
    Resets filter
    """
    try:
        global filtered_images
        filtered_images = sorted(filter_images_in_image_folder_path(), key=sort_by_filename_and_parent_folder)
        logger.debug("Resetting filter")
        return redirect(url_for('image_viewer', image_name=get_random_image()))
    except ValueError as e:
        logger.error(f"Error resetting filter: {str(e)}")
        return handle_value_error("Error resetting filter")

@app.errorhandler(400)
def bad_request_error(error):
    """
    Returns a custom error page for 400 Bad Request errors.

    Args:
        error: The error message.

    Returns:
        flask.Response: The HTTP response containing the error page.
    """
    return render_template('400.html', error=error), 400

@app.errorhandler(ValueError)
def handle_value_error(error):
    return render_template('500.html', message='ValueError occurred. Please try again.', error=error), 500

# Define the URL route for image viewing with image_name as a parameter.
@app.route("/img")
def image_viewer():
    """
    Defines the URL route for image viewing with image_name as a parameter.
    Retrieves the list of all available images, sets the index of the selected image by name or by digit,
    ensures that the index is within the valid range of indices, and sets the image_src and image_alt variables.
    Creates a list of dictionaries for each thumbnail image, including its URL, alt text, and whether or not it is the current image.
    Retrieves the EXIF data for the current image, tries to convert the "Sampler settings" key in exif_data to a dictionary,
    and renders the image_template.html template with the appropriate variables.
    
    Args:
        image_name (str): The name of the selected image.

    Returns:
        render_template: A Flask template with the appropriate variables for viewing the selected image.
    """
    image_name = request.args.get("image_name")
    logger.debug(image_name)
    # Get a list of all images available in the image directory.
    image_list = get_image_names_in_image_dir()

    # Get the filter criteria from the request parameters
    filter_criteria = request.args.get('filter_criteria')

    # Filter the images based on the filter criteria
    if filter_criteria:
        images = filter_images(images, filter_criteria)

    # Check if the image_name parameter is a digit or not.
    # If it is a digit, set image_index to that integer value.
    # Otherwise, get the index of the selected image by name.
    if image_name.isdigit():
        image_index = int(image_name)
    else:
        image_index = get_image_index_by_name(image_name)

    # Ensure that image_index is within the valid range of image_list indices.
    if image_index == None:
        randomimg = get_random_image()
        image_index = get_image_index_by_name(randomimg)
        
    if image_index < 0:
        image_index = len(image_list) - 1
    if image_index >= len(image_list):
        image_index = 0

    # Set the image_src and image_alt variables.
    image_src = image_list[image_index]
    image_alt = image_src

    # Initialize exif_data with a default value.
    exif_data = [{
            'exif_key': "Initialized exif structure",
            'exif_info': "",
            }]
    metadata_found = False
    try:
        # Try to get the EXIF data for the current image.
        # Look up the image in a pre-computed dataframe of EXIF data.
        # Convert the dataframe to a dictionary.
        exif_data = bulk_exif_data.loc[hashlib.sha256(image_src.encode()).hexdigest()].to_dict()
        metadata_found = True

    except KeyError as e:
        # If the image is not found in the EXIF data, log a warning message.
        try:
            bulk_exif_data.loc[hashlib.sha256(image_src.encode()).hexdigest()] = read_exif_data(image_src).loc['exifdataindex']
            exif_data = bulk_exif_data.loc[hashlib.sha256(image_src.encode()).hexdigest()].to_dict()
            metadata_found = True
        except KeyError as e:
            logger.error(e)
            logger.warning(e)
            logger.warning(image_src)
            logger.warning(bulk_exif_data.index)
            exif_data =  {
            'Positive prompt': 'No data found',
            'Negative prompt': 'No data found',
            'Steps': 'No data found', 
            'Sampler': 'No data found', 
            'CFG scale': 'No data found', 
            'Seed': 'No data found', 
            'Size': 'No data found', 
            'Model hash': 'No data found', 
            'Model': 'No data found', 
            'Eta': 'No data found',
            'Hashes': 'No data found',
            'Postprocessing': 'No data found',
            'Extras': 'No data found'}
            metadata_found = False
    
    # Log the exif_data and image_src values.
    logger.debug("exif_data: %s" % exif_data)
    logger.debug("image_viewer: %s " % image_src)
    if metadata_found:
        logger.debug(f"metadata: {imgview_data.loc[hashlib.sha256(image_src.encode()).hexdigest()]}")
    
    global filtered_images
    metadata_for_filtered_images = {}

    for image_path in filtered_images:
        hash_value = hashlib.sha256(image_path.encode()).hexdigest()
        try:
            metadata_for_filtered_images[hash_value] = imgview_data.loc[hash_value].to_dict()
        except KeyError:
            logger.error(f"Metadata not found for image: {image_path}")
            metadata_for_filtered_images[hash_value] = {'Favorites': False,
                                                'Rating': 0,
                                                'Tags': [],
                                                'Categorization': [],
                                                'Reviewed': False,
                                                'Todelete': False}

            if args.aesthetic:
                metadata_for_filtered_images[hash_value]['Aesthetic_score'] = aesthetic_engine.score(image_src)

            imgview_data.loc[hashlib.sha256(image_src.encode()).hexdigest()] = metadata_for_filtered_images[hash_value]

    metadata = None
    try:
        metadata = imgview_data.loc[hashlib.sha256(image_src.encode()).hexdigest()]
        metadata.loc['Reviewed'] = True
        if len(metadata_for_filtered_images) != 1:
            metadata_for_filtered_images = metadata.to_dict()
        else:
            metadata_for_filtered_images[hashlib.sha256(image_src.encode()).hexdigest()] = metadata.to_dict()
    except KeyError:
        logger.error(f"Metadata not found for image: {image_src}")
        metadata_for_filtered_images[hash_value] = {'Favorites': False,
                                            'Rating': 0,
                                            'Tags': [],
                                            'Categorization': [],
                                            'Reviewed': False,
                                            'Todelete': False}

        if args.aesthetic:
            metadata_for_filtered_images[hash_value]['Aesthetic_score'] = aesthetic_engine.score(image_src)
        metadata = metadata_for_filtered_images[hashlib.sha256(image_src.encode()).hexdigest()]
        imgview_data.loc[hashlib.sha256(image_src.encode()).hexdigest()] = metadata

    # Render the image_template.html template with the appropriate variables.
    return render_template("image_template.html",
                           title='PromptViewer',
                           image_src=url_for('image_data', image_name=image_src),
                           image_alt=image_alt,
                           image_index=image_index,
                           exif_list=exif_data,
                           metadata = metadata,
                           maxindex=len(image_list),
                           complete_metadata=metadata_for_filtered_images)

def get_random_image():
    """
    Return a random image from the image directory.

    Returns:
        A string representing the file name of a random image from the image directory.
    """
    images = get_image_names_in_image_dir()
    logger.debug(images)
    image = random.sample(images, 1)[0]
    logging.debug(image)
    return image

@app.route('/set_theme_cookie', methods=['POST'])
def set_theme_cookie():
    theme = request.form.get('theme')
    logger.debug(theme)
    response = make_response(jsonify({'message': 'Cookie set'}))
    response.set_cookie('theme', theme)
    logger.debug(response)
    return response

# Define a route to handle the toggle request
@app.route("/toggle", methods=["PUT"])
def toggle():
    data = request.json
    image_name = data.get("image_name")
    logger.debug("Toggling favorite")
    logger.debug(image_name)
    # Find the row that matches the image name
    row = imgview_data.loc[hashlib.sha256(image_name.encode()).hexdigest()]
    # If no row is found, return an error message
    if row.empty:
        return bad_request_error("No image named {image_name} found")
    logger.debug(row)
    # Otherwise, get the current favorite value and flip it
    current_favorite = row["Favorites"]
    new_favorite = not current_favorite
    # Update the dataframe with the new value
    imgview_data.loc[hashlib.sha256(image_name.encode()).hexdigest(), "Favorites"] = new_favorite
    # Return a success message with the new value
    return jsonify(new_favorite)

@app.route("/set-rating", methods=["PUT"])
def set_rating():
    data = request.json
    rating = data.get("rating")
    image_name = data.get("image_name")
    logger.debug(rating)
    imgview_data.loc[hashlib.sha256(image_name.encode()).hexdigest(), "Rating"] = rating
    logger.debug(imgview_data.loc[hashlib.sha256(image_name.encode()).hexdigest(), "Rating"])
    # Return a success message with the new tags
    return jsonify(rating=rating)

@app.route("/add-tags", methods=["PUT"])
def add_tags():
    data = request.json
    tags = data.get("tags")
    logger.debug(tags)
    image_name = data.get("image_name")
    row = imgview_data.loc[hashlib.sha256(image_name.encode()).hexdigest()]
    # If no row is found, return an error message
    if row.empty:
        return bad_request_error(f"No image named {image_name} found")
    logger.debug(row)
    logger.debug(row.dtypes)
    # Otherwise, get the current tags list and append the new tags
    current_tags_str = row["Tags"]
    logger.debug(current_tags_str)
    current_tags_list = ast.literal_eval(current_tags_str)
    logger.debug(current_tags_list)
    incoming_tags = tags
    new_tags_list = current_tags_list + incoming_tags
    logger.debug(new_tags_list)
    imgview_data.loc[hashlib.sha256(image_name.encode()).hexdigest(), "Tags"] = str(new_tags_list)
    # Return a success message with the new tags
    return jsonify(tags=new_tags_list)

@app.route("/remove-tags", methods=["PUT"])
def remove_tags():
    data = request.json
    image_name = data.get("image_name")
    logger.debug("removing tags")
    tags_to_remove = data.get("tag")
    logger.debug(tags_to_remove)
    row = imgview_data.loc[hashlib.sha256(image_name.encode()).hexdigest()]
    # If no row is found, return an error message
    if row.empty:
        return bad_request_error(f"No image named {image_name} found")
    logger.debug(row)
    logger.debug(row.dtypes)
    # Otherwise, get the current tags list and remove the specified tags
    current_tags_str = row["Tags"]
    current_tags_list = ast.literal_eval(current_tags_str)
    logger.debug(current_tags_list)
    logger.debug(current_tags_str)
    logger.debug(tags_to_remove)
    new_tags_list = [tag for tag in current_tags_list if tag not in tags_to_remove]
    logger.debug(new_tags_list)
    imgview_data.loc[hashlib.sha256(image_name.encode()).hexdigest(), "Tags"] = str(new_tags_list)
    # Return a success message with the updated tags
    return jsonify(tags=new_tags_list)

@app.route("/assign-category", methods=["PUT"])
def assign_category():
    data = request.json
    image_name = data.get("image_name")
    category = data.get("categories")
    logger.debug(category)
    row = imgview_data.loc[hashlib.sha256(image_name.encode()).hexdigest()]
    # If no row is found, return an error message
    if row.empty:
        return bad_request_error(f"No image named {image_name} found")
    logger.debug(row)
    logger.debug(row.dtypes)
    # Otherwise, get the current tags list and append the new tags
    current_categories = row["Categorization"]
    current_categories_list = ast.literal_eval(current_categories)
    incomming_category = category
    logger.debug(type(incomming_category))
    logger.debug(type(current_categories_list))
    new_category_list = current_categories_list + incomming_category
    logger.debug(new_category_list)
     # Update the dataframe with the new value
    imgview_data.loc[hashlib.sha256(image_name.encode()).hexdigest(), "Categorization"] = str(new_category_list)
    # Return a success message with the new value
    return jsonify(category=new_category_list)

@app.route("/remove-category", methods=["PUT"])
def remove_categories():
    data = request.json
    image_name = data.get("image_name")
    logger.debug("removing tags")
    category_to_remove = data.get("category")
    logger.debug(category_to_remove)
    row = imgview_data.loc[hashlib.sha256(image_name.encode()).hexdigest()]
    # If no row is found, return an error message
    if row.empty:
        return bad_request_error(f"No image named {image_name} found")
    logger.debug(row)
    logger.debug(row.dtypes)
    # Otherwise, get the current tags list and remove the specified tags
    current_categories = row["Categorization"]
    current_categories_list = ast.literal_eval(current_categories)
    logger.debug(current_categories)
    logger.debug(current_categories_list)
    logger.debug(category_to_remove)
    new_category_list = [tag for tag in current_categories_list if tag not in category_to_remove]
    logger.debug(new_category_list)
    imgview_data.loc[hashlib.sha256(image_name.encode()).hexdigest(), "Categorization"] = str(new_category_list)
    # Return a success message with the updated tags
    return jsonify(tags=new_category_list)

def get_selected_image_by_index(image_id):
    """
    Return the image at the given index in the image directory.

    Args:
        image_id: An integer representing the index of the desired image.

    Returns:
        A string representing the file name of the image at the given index.
    """
    logging.debug("Getting the index of image: %s" % image_id)
    images = get_image_names_in_image_dir()
    logging.debug("------------")
    logging.debug(image_id)
    logging.debug(images)
    logging.debug(images[int(image_id)])
    logging.debug("------------")
    return images[int(image_id)]

@app.route('/get-metadata')
def get_metadata():
    image_name = request.args.get("image_name")
    metadata_dict = imgview_data.loc[hashlib.sha256(image_name.encode()).hexdigest()].to_dict()
    tags_str = metadata_dict['Tags'].strip('[]').replace("'", '').split(', ')
    metadata_dict['Tags'] = tags_str
    category_str = metadata_dict['Categorization'].strip('[]').replace("'", '').split(', ')
    metadata_dict['Categorization'] = category_str
    logger.debug(metadata_dict)
    # Convert the metadata dictionary to a JSON object and return it
    return json.dumps(metadata_dict)

@app.route("/get_image_by_name")
def get_selected_image_index_by_name():
    """
    Return the index of the image with the given name.

    Args:
        image_name: A string representing the name of the desired image.

    Returns:
        An integer representing the index of the image with the given name.
    """
    image_name = request.args.get("image_name")
    logging.debug("Getting the index of image: %s" % image_name)
    images = get_image_names_in_image_dir()
    logging.debug("------------")
    logging.debug(image_name)
    #logging.debug(images)
    logging.debug("------------")
    try:
        return int(images.index(image_name))
    except ValueError as e:
        logger.error(e)
        return None
    
def get_image_index_by_name(image_name):
    logger.debug(image_name)
    images = get_image_names_in_image_dir()
    if images[0][0] == "/":
        logger.debug("Found /")
        if image_name[0] == "/":
            pass
        else:
            image_name = "/" + image_name
    logging.debug("Getting the index of image: %s" % image_name)
    logging.debug(images)
    try:
        return int(images.index(image_name))
    except ValueError as e:
        logger.error(e)
        return None

def is_valid_image_extension(filename):
    """
    Return True if the given file name has a valid image extension.

    Args:
        filename: A string representing the file name to check.

    Returns:
        True if the file name has a valid image extension (i.e. .jpg, .jpeg, or .png), False otherwise.
    """
    if sys.platform == 'darwin' and filename.startswith('._'):
        return False
    return filename.endswith(".jpg") or filename.endswith(".jpeg") or filename.endswith(".png")

def get_image_names_in_image_dir():
    """
    Returns a list of filenames for all the images in the image directory.

    Debug messages are also logged to show the image folder and the number of images found.

    Returns:
    A list of filenames for all the images in the image directory, filtered by valid image extensions.
    """
    logger.debug(image_folder)
    #images = [f for f in os.listdir(image_folder) if os.path.isfile(os.path.join(image_folder, f)) and is_valid_image_extension(f)]
    #images = [os.path.join(image_folder, f) for f in images]
    logger.debug(len(filtered_images))
    return filtered_images

def metadata_initialization():
    """
    Initializes metadata for all images in the image directory and saves it to a CSV file.

    For each image in the image directory, the SHA256 hash of its path is computed as the key for its metadata in
    a dictionary. The metadata is initialized with default values for 'Favorites', 'Rating', 'Tags', and 'Categorization'.

    Debug messages are logged to show the metadata dataframe and its SHA256 index name.

    Returns:
    A Pandas DataFrame object containing the metadata for all images, saved to a CSV file.
    """
    # create an empty dictionary to store the metadata for each image
    metadata = {}
    for image in get_image_names_in_image_dir():
         # compute the SHA256 hash of the image path
        key = hashlib.sha256(image.encode()).hexdigest()
        
        # initialize the metadata for the image
        metadata[key] = {'Favorites': False,
                                            'Rating': 0,
                                            'Tags': [],
                                            'Categorization': [],
                                            'Reviewed': False,
                                            'Todelete': False}

        if args.aesthetic:
            metadata[key]['Aesthetic_score'] = aesthetic_engine.score(image)
    
    # create the dataframe from the metadata dictionary
    df = pd.DataFrame.from_dict(metadata, orient='index')
    logger.debug(df)
    df.index.name = "sha256"
    df.to_csv(metadata_subdir.joinpath("imgview_metadata.csv"), index=True, header=True)
    return df

def update_metadata():
    """
    Updates the existing metadata with initialized metadata for images not already in the dataframe.

    Reads in the metadata CSV file, creating a dataframe from it. Then, computes the set of SHA256 hashes for all images
    already in the dataframe, and loops through all images in the image directory. For each image, if its SHA256 hash is not
    already in the set of existing hashes, then its metadata is initialized and added to the metadata dictionary.
    Finally, a dataframe is created from the updated metadata dictionary and saved to the CSV file.

    Returns:
    A Pandas DataFrame object containing the updated metadata for all images, saved to a CSV file.
    """
    # read in the existing metadata CSV file
    metadata_df = pd.read_csv(metadata_subdir.joinpath("imgview_metadata.csv"), index_col='sha256')

    # create a set of SHA256 hashes for all images already in the dataframe
    existing_hashes = set(metadata_df.index)

    # create an empty dictionary to store the updated metadata for all images
    updated_metadata = {}

    for image in get_image_names_in_image_dir():
        # compute the SHA256 hash of the image path
        key = hashlib.sha256(image.encode()).hexdigest()

        # if the SHA256 hash is not already in the set of existing hashes, initialize the metadata for the image
        if key not in existing_hashes:
            updated_metadata[key] = {'Favorites': False,
                                     'Rating': 0,
                                     'Tags': [],
                                     'Categorization': []}

    # update the existing metadata dictionary with the initialized metadata for new images
    updated_metadata.update(metadata_df.to_dict('index'))

    # create the dataframe from the updated metadata dictionary
    updated_df = pd.DataFrame.from_dict(updated_metadata, orient='index')
    updated_df.index.name = "sha256"
    updated_df.to_csv(metadata_subdir.joinpath("imgview_metadata.csv"), index=True, header=True)

    return updated_df

def read_exif_data(image):
    """
    Extracts the EXIF data from an image file.

    Args:
        image (str): Name of the image file.

    Returns:
        pandas.DataFrame: A DataFrame row containing the extracted EXIF data.
    """
    logger.debug(image)
    #image = os.path.join(image_folder, image)
    img = Image.open(image)
    parsed_data = {
        'Positive prompt': 'No data found',
        'Negative prompt': 'No data found',
        'Steps': 'No data found', 
        'Sampler': 'No data found', 
        'CFG scale': 'No data found', 
        'Seed': 'No data found', 
        'Size': 'No data found', 
        'Model hash': 'No data found', 
        'Model': 'No data found', 
        'Eta': 'No data found',
        'Hashes': 'No data found',
        'Postprocessing': 'No data found',
        'Extras': 'No data found'
    }
    try:
        exif_data = img.info
        parameters = None
        if 'parameters' in exif_data:
            parameters = exif_data.get('parameters', '')
        elif 'exif' in exif_data:
            exif_info = piexif.load(exif_data['exif'])
            user_comment_info = exif_info.get('Exif', {}).get(piexif.ExifIFD.UserComment, b'')
            parameters = piexif.helper.UserComment.load(user_comment_info)
        logger.debug(f"-------\nexif_data:{exif_data}\nexif_data_type:{type(exif_data)}----------\n")
    except AttributeError as e:
        logger.warning(img)
        logger.warning(e)
        return pd.DataFrame(parsed_data, index=["exifdataindex"])

    logger.debug(parameters)
    logger.debug(type(parameters))
    if not parameters:
        logger.warning("No exif parameters found")
        return pd.DataFrame(parsed_data, index=["exifdataindex"])
    try:
        regex = r'(\w+(?:\s+\w+)*)\s*:\s*([\w.+@-]+(?:\s+[\w.+@-]+)*(?:\s*\([\w\s.+@-]*\))?)'
        param_lines = parameters.splitlines()
        first_line = None
        logger.debug(f"Length of  param_lines: {len(param_lines)}")
        if len(param_lines) > 2 and any("Negative prompt:" in s for s in param_lines):
            first_line = param_lines.pop(0)
        elif len(param_lines) == 2 and not any("Negative prompt:" in s for s in param_lines):
            first_line = param_lines.pop(0)
        if first_line:
            parsed_data['Positive prompt'] = first_line
        for key_value in param_lines:
            logger.debug(f"key_value:{key_value}")
            if 'Negative prompt:' in key_value:
                negative_prompt_values = key_value.split('Negative prompt: ')[1:]
                negative_prompt_value = negative_prompt_values[-1]
                parsed_data['Negative prompt'] = negative_prompt_value.strip()
            elif all(x in key_value for x in ['Steps:', 'Sampler:', 'CFG scale:', 'Seed:', 'Size:', 'Model:']):
                logger.debug(f"diff prompt: {key_value}")
                matches = re.findall(regex, key_value)
                for match in matches:
                    parsed_data[match[0]] = match[1]

        # Parse the "postprocessing" key
        postprocessing = exif_data.get('postprocessing', '')
        if postprocessing:
            parsed_data['Postprocessing'] = postprocessing

        # Parse the "extras" key
        extras = exif_data.get('extras', '')
        if extras:
            parsed_data['Extras'] = extras
    except KeyError as e:
        logger.warning(e)
        logger.debug(parsed_data)
        return pd.DataFrame(parsed_data, index=["exifdataindex"])

    logger.debug(parsed_data)
    return pd.DataFrame(parsed_data, index=["exifdataindex"]) 
    
def mp_bulk_exif_read(filtered_images):
    """
    Reads the EXIF data from all image files in parallel using multiprocessing.

    Returns:
        bulk_exif_data (dict): A dictionary containing the EXIF data for all image files.
    """
    pool = multiprocessing.Pool(multiprocessing.cpu_count())
    results = []
    for image in filtered_images:
        logger.debug(image)
        result = pool.apply_async(read_exif_data, args=(image,))
        results.append(result)

    pool.close()
    pool.join()

    logger.debug("pool joined")

    df = pd.DataFrame(columns=['Positive prompt', 'Negative prompt', 'Sampler settings',
                               'Steps', 'Sampler', 'CFG scale', 'Seed', 'Size', 'Model hash',
                               'Model', 'Eta', 'Hashes', 'Postprocessing', 'Extras',  'Denoising strength', 'ENSD', '0 Enabled',
                                '0 Module', '0 Model', '0 Weight', '0 Guidance Start', '0 Guidance End',
                                'Hires upscale', 'Hires steps', 'Hires upscaler'])
    df.index.name = "sha256"

    for result, image in zip(results, filtered_images):
        logger.debug(f"result: {result}, image: {image}")
        row = result.get()
        logger.debug(row.to_string())
        df.loc[hashlib.sha256(image.encode()).hexdigest()] = row.loc['exifdataindex']

    # create the output dataframe from the list of dictionaries
    #output_df = pd.DataFrame(dict_to_rows(bulk_exif_data), columns=['sha256', 'Positive prompt', 'Negative prompt', 'Sampler settings']).to_csv(metadata_subdir.joinpath("exif_df.csv"), index=False, header=True)
    df.to_csv(metadata_subdir.joinpath("exif_df.csv"), index=True, header=True)
    logger.debug(df)
    #bulk_exif_data = df.to_dict(orient='index')
    # convert the output dictionary to a pandas DataFrame
    return df

def dict_to_rows(inputdict):
    """Converts a dictionary of EXIF data to a list of dictionaries suitable for creating a pandas DataFrame.

    Args:
        inputdict (dict): A dictionary of EXIF data.

    Returns:
        list: A list of dictionaries suitable for creating a pandas DataFrame.

    """
    # create an empty list to store the dictionaries
    rows = []

    # loop through each sha256 hash in the input dictionary
    for sha256, dict_list in inputdict.items():
        # create an empty dictionary to store the values for each row
        row_dict = {'sha256': sha256}
        # loop through the list of dictionaries for the current sha256 hash
        for d in dict_list:
            # get the key and value from the current dictionary
            key = d['exif_key']
            logger.debug(key)
            value = d['exif_info']
            logger.debug(value)
            # add the value to the row dictionary if it's one of the three specific keys
            row_dict[key] = value
        # add the row dictionary to the list of dictionaries
        rows.append(row_dict)
    return rows


    
if __name__ == '__main__':
    if sys.platform.startswith('win'):
        # On Windows calling this function is necessary.
        multiprocessing.freeze_support()
    start_time = time.time()
    logger.debug(args)
    if args.aesthetic:
        import gallery_engine as ge
        aesthetic_engine = ge.aesthetic_engine()

    if args.imagedir:
        image_folder = Path(args.imagedir)
        logger.debug(f"Sat image_folder from args.imagedir: {image_folder}")
    else:
        #raise ValueError("No image folder defined. Please supply image folder. use --h to see help.")
        image_folder = Path("sampledir")
    
    metadata_folder = Path("metadata")
    metadata_folder.mkdir(parents=True, exist_ok=True)
    metadata_subdir = metadata_folder / (image_folder.parent.name + '_' + image_folder.name)
    metadata_subdir.mkdir(parents=True, exist_ok=True)
    thumbnail_folder = metadata_subdir / 'thumbnails'
    thumbnail_folder.mkdir(parents=True, exist_ok=True)
    #filtered_images = [f.name for f in image_folder.iterdir() if f.is_file() and is_valid_image_extension(f.name)]
    #filtered_images = filter_images_in_image_folder_path()
    filtered_images = sorted(filter_images_in_image_folder_path(), key=sort_by_filename_and_parent_folder)

    # Check if EXIF data already exists
    exif_df_path = metadata_subdir.joinpath("exif_df.csv")
    if exif_df_path.exists():
        bulk_exif_data = pd.read_csv(exif_df_path)
        bulk_exif_data.set_index('sha256', inplace=True)
        #bulk_exif_data['Sampler settings'] = pd.array(bulk_exif_data['Sampler settings'].tolist())
        logger.warning(len(bulk_exif_data))
        if check_images_in_dataframe(filtered_images, bulk_exif_data):
            pass
        else:
            bulk_exif_data = mp_bulk_exif_read(filtered_images)
    else:
        logger.debug("Creating bulk exif data")
        # Read EXIF data for images
        bulk_exif_data = mp_bulk_exif_read(filtered_images)
    
    # Check if metadata already exists
    metadata_path = metadata_subdir.joinpath("imgview_metadata.csv")
    if metadata_path.exists():
        imgview_data = pd.read_csv(metadata_path)
        imgview_data.set_index('sha256', inplace=True)
        logger.warning(len(imgview_data))
        if check_images_in_dataframe(filtered_images, imgview_data):
            pass
        else:
            imgview_data = update_metadata()
    else:
        logger.debug("Initializing imgview data")
        # Initialize metadata for images
        imgview_data = metadata_initialization()

    if args.cleanup:
        imgview_data = remove_missing_sha256(imgview_data, filtered_images)
        bulk_exif_data = remove_missing_sha256(bulk_exif_data, filtered_images)

    end_time = time.time()
    execution_time = end_time - start_time
    print("Preamble time: {:.2f} seconds".format(execution_time))

    # Start the application
    app.run(host="0.0.0.0", port=args.port, debug=True)