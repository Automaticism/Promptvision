# PromptVision
Promptvision is a web application that allows users to view and browse images. It allows quickly browsing through generations and changing directories in the "web" app. It's running locally using Flask. 

## Installation

### Clone

Clone the repository using git:
```git clone https://github.com/Automaticism/GalleryViewerSD.git```

### Setup
Install the required dependencies using pip:
```pip install -r requirements.txt```

### Usage
Run the application:
```python app.py --imagedir <image folder>```
Replace <image folder> with the path to the folder containing your images.

```
python .\gallery.py --imagedir "F:\stable-diffusion-webui\outputs\txt2img-images\2023-03-21\rpg females"
```

**Note**: on launch it will extract exif data from all images and initialize metadata for all images. It will also create thumbnails. Everything will be placed in a metadata folder in the current working directory. Under this a folder for the <image folder> will be created.

![image](https://user-images.githubusercontent.com/20763070/226762754-72c1254f-890d-4768-ad93-6fa1d3e7f3ac.png)

### URL routes
The following URL routes are available:
- ```/```: Redirects to the image_viewer route with a randomly selected image.
- ```/img/<image_name>```: Goes to image by name e.g. "00250-13343234.png" in your <image folder>
- ``/img/<index>```: Goes to image by index in <image folder>. `0` is the first image.
