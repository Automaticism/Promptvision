# PromptvisionNG

[![Codacy Badge](https://app.codacy.com/project/badge/Grade/538da8df1fd74260bc4b783203ee9881)](https://app.codacy.com/gh/Automaticism/Promptvision/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_grade) ![Platform | MacOS, Windows, Linux](https://img.shields.io/badge/Platform-MacOS%2C%20Windows%2C%20Linux-blue) ![Written with Streamlit](https://img.shields.io/badge/Written%20with-Streamlit-red)

![Supports Automatic1111](https://img.shields.io/badge/Supports-Automatic1111-blue)
![Supports SD.next](https://img.shields.io/badge/Supports-SD.next-green)
![Supports ComfyUI](https://img.shields.io/badge/Supports-ComfyUI-yellow)
![Supports InvokeAI](https://img.shields.io/badge/Supports-InvokeAI-red)
![Supports NovelAI](https://img.shields.io/badge/Supports-NovelAI-purple)


An evolution of the previous Promptvision. View all your image generations in one place. Browse folder by folder. Filter by your favorite prompts. Regex search specific positive / negative prompts. Get your images scored by a specifically trained scoring model (ImageReward) which enables you to get third-party assessments of your generations.

Dive further into the weed with the ability to set favorite status & your personal ratings. All of the fields can then be used when filtering the images you want to watch. This also enables you to copy, move and delete images quickly.

Dive further into your prompt engineering analysis by going into the prompt explorer tab where you can run a few natural language processing algorithms on your specific fields such as your positive prompts. This can give you insight in what prompts that are most prevalent. You can also combine this with the former discussed filtering so that you can really gain a deeper understanding of your prompts and the end results.

![ng image viewer](https://github.com/Automaticism/Promptvision/assets/20763070/79cac5a4-7ef7-4bf4-8c35-87aa18bc8171)
![ng image explorer](https://github.com/Automaticism/Promptvision/assets/20763070/0998671a-e22d-4bfc-aa60-d2a6675d9f7b)
![ng prompt explorer](https://github.com/Automaticism/Promptvision/assets/20763070/70c66449-941c-4189-b083-46b6cf72193f)
![ng gallery view](https://github.com/Automaticism/Promptvision/assets/20763070/3cf84019-bead-4740-a446-e1b08499265d)
![ng settings view](https://github.com/Automaticism/Promptvision/assets/20763070/dc30882d-d110-451e-856b-5304a9312bc6)

## Features

- ImageReward score scoring of images
- Rating and favoriting images
- Filtering your images on all properties:
  - Prompts
  - Score
  - Personal rating
  - Favorite
  - Resolution
- Copying, moving and deletion of images
- Folder and subfolder navigation (will detect subfolders and enable you to view e.g. all images in a certain folder)

## Setup and installation

1. `git clone https://github.com/Automaticism/Promptvision.git`
2. `cd Promptvision`
3. `conda create -n promptvision`
4. `conda activate promptvision`
5. `pip install -r requirements.txt`
6. `streamlit run Promptvision.py`
7. `Optionally if you use "Calculate ImageReward score" the ImageReward score will be downloaded. This will look like the following in your console:`

- `2023-07-22 00:56:36.538 Created a temporary directory at /var/folders/l5/n6jwr6tn71s_pm5dh926hbdr0000gn/T/tmpqf7yjji1
 2023-07-22 00:56:36.538 Writing /var/folders/l5/n6jwr6tn71s_pm5dh926hbdr0000gn/T/tmpqf7yjji1/_remote_module_non_scriptable.py
 Downloading ImageReward.pt:   1%|▌                                             | 21.0M/1.79G [00:02<02:49, 10.4MB/s]
 `

## Application views

- `Promptvision.py` the entrypoint of the multi-page Streammlit app (used to launch the program, `streamlit run Promptvision.py`). This page also contains settings for the application. Set the directory which will be used as the main directory. (E.g. open your main image folder and it will index all images and subfolders. You can then browse every subfolder.)
- `Gallery.py` the gallery view of your images, select one image here and you can look closer in the `Image viewer.py` page
- `Prompt Explorer.py` is running some Natural Language Processing models generating some statistical information to give insight into prompts (This will be the focus for further development)
- `Image viewer.py` is the image viewer. Has typical option of navigating your images (next, previous), shows generational information (supports all the UIs via the <https://github.com/d3x-at/sd-parsers> module), enables you to set your personal rating and set favorite status, also enables you to view the ImageReward score. Rating & favorite can be used when you are filtering your images (e.g. filter all favorites and copy them to a new folder)

## Bugs and known issues

- This application is limited by Streamlit in some ways with how things are done the Streamlit way (and I am no Streamlit expert), you will get warnings such as:

> AttributeError: st.session_state has no attribute "df". Did you forget to initialize it? More info: <https://docs.streamlit.io/library/advanced-features/session-state#initialization>

These are typical and will disappear when you set directory and browse the different pages. If they persist and something is broken, create an issue for it.

- `score` might be 0.0 even after installing ImageReward model and having checked off the "Calculate ImageReward score", simply press "Reset cache" and it will recalc and most likely fix the problem

## Credits

- ImageReward <https://github.com/THUDM/ImageReward>
- Image select for streamlit <https://github.com/jrieke/streamlit-image-select>
- Streamlit
- Streamlit extras
- sd-parsers <https://github.com/d3x-at/sd-parsers>