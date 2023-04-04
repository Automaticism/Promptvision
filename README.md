# PromptVision
Promptvision is a web application that allows users to view and browse images. It allows quickly browsing through generations and changing directories in the "web" app. It's running locally using Flask. 

![image](https://user-images.githubusercontent.com/20763070/229390468-bae0b93b-0ccc-4f11-b64b-4e443609a03d.png)

- [PromptVision](#promptvision)
  - [Executable](#executable)
  - [Installation](#installation)
      - [Conda](#conda)
        - [Using aesthetic score](#using-aesthetic-score)
  - [Usage](#usage)
  - [Keybinds](#keybinds)
  - [URL routes](#url-routes)

## Executable
Windows exeuctable can be found under releases: https://github.com/Automaticism/Promptvision/releases/

## Installation
Here are step-by-step instructions for opening a terminal, navigating to a folder, cloning a Git repository, creating and activating a virtual environment, installing the necessary dependencies, and running a Python script.

#### Conda
Open up any terminal program (CMD, Windows terminal, Bash, zsh, Powershell).
Use the cd command to navigate to the "Documents" folder. Type `cd Documents` and press enter.
Use the git clone command to clone the repository. Type `git clone [repository URL]` and press enter. Replace "[repository URL]" with the URL of the repository you want to clone. For example:
```
git clone https://github.com/Automaticism/Promptvision.git
```
Use the "cd" command to navigate to the cloned repository. Type cd repository and press enter. Replace "repository" with the name of the cloned repository.
Create a new conda environment and activate it with the following commands:
```
conda create --name myenv

conda activate myenv
```
These commands will create a new environment named "myenv" and activate it.

Install the necessary dependencies using the following command:
```
pip install -r requirements.txt
```
This command will install the dependencies listed in the "requirements.txt" file.

Finally, run the Python script with the following command, replacing "[your image folder]" with the name of the folder containing your images:

```
python gallery.py --imagedir "[your image folder]"
```
##### Using aesthetic score
Based on this: https://github.com/AUTOMATIC1111/stable-diffusion-webui/discussions/1831
See the code in [gallery_engine](gallery_engine.py).

Required extras, this assumes you have setup Nvidia CUDA version 11.8 in this case. Adjust `pytorch-cuda=<version>` according to what you have installed.
If you have any challenges look at https://pytorch.org/get-started/locally/ to see how you can install it to your specific system.

```
conda install pytorch torchvision torchaudio pytorch-cuda=11.8 -c pytorch -c nvidia
pip install ftfy regex tqdm
pip install git+https://github.com/openai/CLIP.git
```

```
python gallery.py --imagedir "[your image folder]" --aesthetic True
```

This will calculate aestehitc score for all your images. 

## Usage
Run the application:
```
python .\gallery.py --imagedir "F:\stable-diffusion-webui\outputs\txt2img-images\2023-03-21\rpg"
```

**Note**: on launch it will extract exif data from all images and initialize metadata for all images. It will also create thumbnails. Everything will be placed in a metadata folder in the current working directory. Under this a folder for the <image folder> will be created.

![image](https://user-images.githubusercontent.com/20763070/226762754-72c1254f-890d-4768-ad93-6fa1d3e7f3ac.png)

## Keybinds
- `s` for save
- `1 ... 5` for rating
- `f` for favorite
- `left` arrow key for previous, `right` arrow key for next

## URL routes
The following URL routes are available:
- `/`: Redirects to the image_viewer route with a randomly selected image.
- `/img/<image_name>`: Goes to image by name e.g. "00250-13343234.png" in your `<image folder>`.
- `/img/<index>`: Goes to image by index in `<image folder>`. `0` is the first image.
