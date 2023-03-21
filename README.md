# PromptVision
PromptVision is a web application that allows users to view and browse images. The main script for running the image viewer application initializes metadata for the images and reads EXIF data from images. If the metadata already exists, it is read from disk. Otherwise, metadata is initialized by calling the ```metadata_initialization``` function. Similarly, if the EXIF data has been previously read and saved to disk, it is read from disk, otherwise, EXIF data is read by calling ```mp_bulk_exif_read``` function. The application is then started by calling the run method of the Flask object.

## Installation
### Requirements
- Python 3.6+
- Flask
- Pillow
- pandas
- piexif
- colorlog

## Clone

Clone the repository using git:
```git clone https://github.com/Automaticism/GalleryViewerSD.git```

## Setup
Install the required dependencies using pip:
```pip install -r requirements.txt```
Run the application:
```python app.py --imagedir <image folder>```
Replace <image folder> with the path to the folder containing your images.

## Usage
### URL routes
The following URL routes are available:
- ```/```: Redirects to the image_viewer route with a randomly selected image.
- ```/image_viewer/<image_name>```: Defines the URL route for image viewing with image_name as a parameter. Retrieves the list of all available images, sets the index of the selected image by name or by digit, ensures that the index is within the valid range of indices, and sets the image_src and image_alt variables. Creates a list of dictionaries for each thumbnail image, including its URL, alt text, and whether or not it is the current image. Retrieves the EXIF data for the current image, tries to convert the "Sampler settings" key in exif_data to a dictionary, and renders the image_template.html template with the appropriate variables.

## Functions
The following functions are available:
- ```metadata_initialization()```: Initializes metadata for all images in the image directory and saves it to a CSV file.
- ```mp_bulk_exif_read()```: Reads the EXIF data for all images in the image directory and saves it to disk.
- ```get_image_names_in_image_dir()```: Returns a list of filenames for all the images in the image directory, filtered by valid image extensions.
- ```get_num_images()```: Get the number of images in the image directory.
- ```get_selected_image_by_index(image_id)```: Return the image at the given index in the image directory.
- ```get_selected_image_index_by_name(image_name)```: Return the index of the image with the given name.
- ```get_random_image()```: Return a random image from the image directory.
- ```get_thumbnail_from_image(image_name)```: Get the thumbnail of an image.
- ```is_valid_image_extension(filename)```: Return True if the given file name has a valid image extension.
- ```fetch_thumbnails(limit, offset)```: Fetch a list of image thumbnails.
- ```dir_path(string)```: Validate and return a directory path.
- ```image_data(image_name)```: Returns the image data for the specified image name.
- ```image_data_thumbnails(image_name)```: Get the thumbnail data for the given image.
- ```browse()```: Changes the image folder to the specified folder path.
- ```index()```: Redirect to the image_viewer route with a randomly selected image.
