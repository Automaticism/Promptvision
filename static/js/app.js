
/* Add key bindings for left and right arrow keys */
function keyhandler(event) {
    var key = event.keyCode;
    if (key == 37) {
        document.getElementById('previous').click();
        console.log("previous");
    }
    else if (key == 39) {
        document.getElementById('next').click();
        console.log("next");
    }
    else if (event.key === 'f') {
        event.preventDefault();
        document.querySelector('.favorite-toggle').click();
    }
    else {
        const numPressed = parseInt(event.key);
        if (numPressed >= 0 && numPressed <= 5) {
            event.preventDefault();
            const rating = numPressed;
            const image_name = document.getElementById('active-image').alt;
            const xhr = new XMLHttpRequest();
            xhr.open('PUT', '/set-rating');
            xhr.setRequestHeader('Content-Type', 'application/json');
            const starIcons = document.querySelectorAll('.rating-icon');
            xhr.onreadystatechange = function () {
                if (this.readyState === XMLHttpRequest.DONE && this.status === 200) {
                    const response = JSON.parse(this.responseText);
                    // Update the star icons to reflect the new rating
                    starIcons.forEach((icon, index) => {
                        if (index < response.rating) {
                            icon.textContent = 'star';
                        } else {
                            icon.textContent = 'star_border';
                        }
                    });
                }
            };
            xhr.send(JSON.stringify({ rating: rating, image_name: image_name }));
        } else if ((event.ctrlKey || event.metaKey) && event.key === "s") {
            // Prevent the default behavior of the key combination
            event.preventDefault();
            // Trigger the "submit" event on the "Save" form
            document.getElementById('save-form').submit();
        } else {
            return false;
        }
    }
    return true;
}

document.addEventListener('keydown', function (event) {
    keyhandler(event);

});

document.addEventListener('keyup', function (event) {
});

document.addEventListener("keydown", function (event) {
    switch (event.key) {
        case "ArrowUp":
        case "ArrowDown":
        case "ArrowLeft":
        case "ArrowRight":
            event.preventDefault();
            break;
        default:
            break;
    }
});

function lazyLoadThumbnails() {
    console.log("lazyLoadingThumbnails")
    const container = document.getElementById('thumbnails');
    const thumbnailContainerWidth = window.innerWidth * 0.2;
    const maxThumbnailsPerRow = Math.floor(thumbnailContainerWidth / 50);
    const maxThumbnailsPerColumn = Math.floor(container.clientHeight / 65);
    let numImages;
    let limit;
    let offset;
    const img = document.getElementById('active-image');
    const imgsrc = img.getAttribute('alt');
    const imgage_url = img.getAttribute('src')
    const urlParams = imgage_url.split("?")[1];

    // Fetch the number of images using AJAX
    fetch('/numimages')
        .then(response => response.json())
        .then(data => {
            numImages = data.num_images;
            limit = Math.min(maxThumbnailsPerRow * maxThumbnailsPerColumn, numImages); // Limit to the number of available images
            offset = limit; // Set offset to `limit` to fetch more thumbnails after the initial set

            // Fetch some initial thumbnails using AJAX
            fetch(`/thumbnails?limit=${limit}&offset=0&imgsrc=${imgsrc}`)
                .then(response => response.text())
                .then(html => {
                    //console.log(urlParams)
                    //console.log(html)
                    if (html.indexOf(urlParams) !== -1) {
                        console.log('The substring was found in the HTML.');
                        //console.log(html.indexOf(urlParams))

                        // locate the <img> tag within the html string
                        const imgStartIndex = html.indexOf('<a href="/img?' + urlParams);
                        const imgEndIndex = html.indexOf('/a>', imgStartIndex) + 3;
                        const imgTag = html.substring(imgStartIndex, imgEndIndex);
                        //console.log(imgTag)
                        // add "active-thumbnail" class to the <img> tag
                        const modifiedImgTag = imgTag.replace('<img ', '<img class="active-thumbnail" ');
                        //console.log(modifiedImgTag)
                        // replace the original <img> tag with the modified version in the html string
                        const modifiedHtml = html.substring(0, imgStartIndex) + modifiedImgTag + html.substring(imgEndIndex);

                        container.insertAdjacentHTML('beforeend', `<div class="thumbnail">${modifiedHtml}</div>`);
                    } else {
                        console.log('The substring was not found in the HTML.');
                        container.insertAdjacentHTML('beforeend', `<div class="thumbnail">${html}</div>`);
                    }
                });
        });
    // Load more thumbnails when user scrolls near the end of the container
    container.addEventListener('scroll', loadMoreThumbnails);
}

function loadMoreThumbnails() {
    const container = document.getElementById('thumbnails');
    container.removeEventListener('scroll', loadMoreThumbnails);
    const thumbnailContainerWidth = window.innerWidth * 0.2;
    const maxThumbnailsPerRow = Math.floor(thumbnailContainerWidth / 50);
    const maxThumbnailsPerColumn = Math.floor(container.clientHeight / 65);
    let numImages;
    let offset;
    const img = document.getElementById('active-image');
    const imgsrc = img.getAttribute('alt');
    const imgage_url = img.getAttribute('src');
    const urlParams = imgage_url.split("?")[1];
    // Fetch the number of images using AJAX
    fetch('/numimages')
        .then(response => response.json())
        .then(data => {
            numImages = data.num_images;
            limit = Math.min(maxThumbnailsPerRow * maxThumbnailsPerColumn, numImages); // Limit to the number of available images
            offset = limit; // Set offset to `limit` to fetch more thumbnails after the initial set
            console.log("Should be loading more thumbnails");
            if (offset >= numImages) {
                // All thumbnails have been loaded, so return early
                return;
            }

            if (container.getBoundingClientRect().top < window.innerHeight) {
                // Fetch more thumbnails using AJAX
                fetch(`/thumbnails?limit=${numImages}&offset=${offset}&imgsrc=${imgsrc}`)
                    .then(response => response.text())
                    .then(html => {
                        if (html.indexOf(urlParams) !== -1) {
                            console.log('The substring was found in the HTML.');
                            console.log(html.indexOf(urlParams));

                            // locate the <img> tag within the html string
                            const imgStartIndex = html.indexOf('<a href="/img?' + urlParams);
                            const imgEndIndex = html.indexOf('/a>', imgStartIndex) + 3;
                            const imgTag = html.substring(imgStartIndex, imgEndIndex);
                            
                            // add "active-thumbnail" class to the <img> tag
                            const modifiedImgTag = imgTag.replace('<img ', '<img class="active-thumbnail" ');

                            // replace the original <img> tag with the modified version in the html string
                            const modifiedHtml = html.substring(0, imgStartIndex) + modifiedImgTag + html.substring(imgEndIndex);

                            container.insertAdjacentHTML('beforeend', `<div class="thumbnail">${modifiedHtml}</div>`);
                        } else {
                            console.log('The substring was not found in the HTML.');
                            container.insertAdjacentHTML('beforeend', `<div class="thumbnail">${html}</div>`);
                        }
                        offset += numImages;
                        console.log(`offset: ${offset}, numImages: ${numImages}, container top: ${container.getBoundingClientRect().top}, window height: ${window.innerHeight}`);
                    });
            }
        });
} 


function clearThumbnails() {
    const container = document.getElementById('thumbnails');
    container.innerHTML = '';
}

const favoriteForms = document.querySelectorAll('.favorite-toggle');

favoriteForms.forEach(form => {
    form.addEventListener('click', event => {
        event.preventDefault();
        const image_name = document.getElementById('active-image').alt;
        console.log(image_name)
        const xhr = new XMLHttpRequest();
        xhr.open('PUT', `/toggle`);
        xhr.setRequestHeader('Content-Type', 'application/json');
        xhr.onreadystatechange = function () {
            if (this.readyState === XMLHttpRequest.DONE && this.status === 200) {
                //console.log(this)
                const newFavorite = JSON.parse(this.responseText);
                const formMethod = newFavorite ? "PUT" : "POST"; // Define form method based on current state
                const currentForm = event.target.closest('form'); // Get the current form being processed
                const formMethodInput = currentForm.querySelector('[name="_method"]');
                if (formMethodInput) {
                    formMethodInput.value = formMethod;
                }
                currentForm.querySelector('.favorite-toggle').innerHTML = newFavorite ? '<span class="material-icons">favorite</span>' : '<span class="material-icons">favorite_border</span>'; // Update button label with heart icon
            }
        };
        xhr.send(JSON.stringify({ image_name: image_name }));
    });
});

const starRating = document.getElementById('star-rating');
const starIcons = starRating.querySelectorAll('.material-icons');

// Add click and double-click event listener to each star icon
starIcons.forEach((starIcon) => {
    starIcon.addEventListener('click', () => {
        const rating = starIcon.getAttribute('data-rating');
        const image_name = document.getElementById('active-image').alt;
        const xhr = new XMLHttpRequest();
        xhr.open('PUT', '/set-rating');
        xhr.setRequestHeader('Content-Type', 'application/json');
        xhr.onreadystatechange = function () {
            if (this.readyState === XMLHttpRequest.DONE && this.status === 200) {
                console.log('Rating set!');
            }
        };
        xhr.send(JSON.stringify({ rating: rating, image_name: image_name }));
        // Update the star icons to reflect the new rating
        starIcons.forEach((icon) => {
            if (icon.getAttribute('data-rating') <= rating) {
                icon.textContent = 'star';
            } else {
                icon.textContent = 'star_border';
            }
        });
    });

    starIcon.addEventListener('dblclick', () => {
        // Reset the rating to 0 if any of the stars are double-clicked
        starIcons.forEach((icon) => {
            icon.textContent = 'star_border';
        });
        const rating = 0;
        const image_name = document.getElementById('active-image').alt;
        const xhr = new XMLHttpRequest();
        xhr.open('PUT', '/set-rating');
        xhr.setRequestHeader('Content-Type', 'application/json');
        xhr.onreadystatechange = function () {
            if (this.readyState === XMLHttpRequest.DONE && this.status === 200) {
                console.log('Rating reset!');
            }
        };
        xhr.send(JSON.stringify({ rating: rating, image_name: image_name }));
    });
});

// Tag form
const addTagsForm = document.querySelector('#tag-form');
addTagsForm.addEventListener('submit', event => {
    event.preventDefault();

    const image_name = document.getElementById('active-image').alt;
    const tags = document.getElementById('tagsinput').value.trim().split(/\s*,\s*/);

    console.log('image_name:', image_name);
    console.log('tags:', tags);

    const xhr = new XMLHttpRequest();
    xhr.open('PUT', `/add-tags`);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.onreadystatechange = function () {
        if (this.readyState === XMLHttpRequest.DONE && this.status === 200) {
            console.log("Tags added");
            // Get updated metadata for image
            const xhr2 = new XMLHttpRequest();
            xhr2.open('GET', `/get-metadata?image_name=${image_name}`);
            xhr2.onreadystatechange = function () {
                if (this.readyState === XMLHttpRequest.DONE && this.status === 200) {
                    const metadata = JSON.parse(this.responseText);
                    // Update the tags list in the HTML
                    const tagsList = document.querySelector('#tags-list');
                    tagsList.innerHTML = '';
                    metadata.Tags.forEach(tag => {
                        const tagItem = document.createElement('li');
                        tagItem.textContent = tag;
                        tagItem.classList.add('tag-item');
                        tagItem.addEventListener('click', function () {
                            removeTag(image_name, tag);
                        });
                        tagsList.appendChild(tagItem);
                    });
                    addClickListenersToTags();
                }
            };
            xhr2.send();
        }
    };
    xhr.send(JSON.stringify({ tags: tags, image_name: image_name }));
});

// Function to remove tag from image
function removeTag(image_name, tag) {
    const xhr = new XMLHttpRequest();
    xhr.open('PUT', `/remove-tags`);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.onreadystatechange = function () {
        if (this.readyState === XMLHttpRequest.DONE && this.status === 200) {
            console.log("Tag removed");
            // Get updated metadata for image
            const xhr2 = new XMLHttpRequest();
            xhr2.open('GET', `/get-metadata?image_name=${image_name}`);
            xhr2.onreadystatechange = function () {
                if (this.readyState === XMLHttpRequest.DONE && this.status === 200) {
                    const metadata = JSON.parse(this.responseText);
                    // Update the tags list in the HTML
                    const tagsList = document.querySelector('#tags-list');
                    tagsList.innerHTML = '';
                    metadata.Tags.forEach(tag => {
                        const tagItem = document.createElement('li');
                        tagItem.textContent = tag;
                        tagItem.classList.add('tag-item');
                        tagItem.addEventListener('click', function () {
                            removeTag(image_name, tag);
                        });
                        tagsList.appendChild(tagItem);
                    });
                    addClickListenersToTags();
                }
            };
            xhr2.send();
        }
    };
    xhr.send(JSON.stringify({ tag: tag, image_name: image_name }));
}

// Function to add click event listeners to each tag item to remove tags
function addClickListenersToTags() {
    const tagItems = document.querySelectorAll('.tag-item');
    tagItems.forEach(tagItem => {
        const tag = tagItem.textContent;
        tagItem.addEventListener('click', function () {
            const image_name = document.getElementById('active-image').alt;
            removeTag(image_name, tag);
        });
    });
}

// Call addClickListenersToTags to add event listeners to tags when the page loads
addClickListenersToTags();


// Category form
const categoryForm = document.querySelector('#category-form');
categoryForm.addEventListener('submit', (event) => {
    event.preventDefault();
    const image_name = document.getElementById('active-image').alt;
    const categories = document.getElementById('category').value.trim().split(',').map(category => category.trim());
    console.log(categories)
    const xhr = new XMLHttpRequest();
    xhr.open('PUT', `/assign-category`);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.onreadystatechange = function () {
        if (this.readyState === XMLHttpRequest.DONE && this.status === 200) {
            console.log('Category assigned!');
            // Get updated metadata for image
            const xhr2 = new XMLHttpRequest();
            xhr2.open('GET', `/get-metadata?image_name=${image_name}`);
            xhr2.onreadystatechange = function () {
                if (this.readyState === XMLHttpRequest.DONE && this.status === 200) {
                    const metadata = JSON.parse(this.responseText);
                    console.log(metadata)
                    // Update the category in the HTML
                    const categoryList = document.querySelector('#category-list');
                    categoryList.innerHTML = '';
                    metadata.Categorization.forEach(category => {
                        const categoryItem = document.createElement('li');
                        categoryItem.textContent = category;
                        categoryList.appendChild(categoryItem);
                        categoryItem.addEventListener('click', function () {
                            removeCategory(image_name, category);
                        });
                    });
                }
            };
            xhr2.send();
        }
    };
    xhr.send(JSON.stringify({ categories: categories, image_name: image_name }));
});

// Function to remove category from image
function removeCategory(image_name, category) {
    const xhr = new XMLHttpRequest();
    xhr.open('PUT', `/remove-category`);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.onreadystatechange = function () {
        if (this.readyState === XMLHttpRequest.DONE && this.status === 200) {
            console.log("Category removed");
            // Get updated metadata for image
            const xhr2 = new XMLHttpRequest();
            xhr2.open('GET', `/get-metadata?image_name=${image_name}`);
            xhr2.onreadystatechange = function () {
                if (this.readyState === XMLHttpRequest.DONE && this.status === 200) {
                    const metadata = JSON.parse(this.responseText);
                    // Update the category list in the HTML
                    const categoryList = document.querySelector('#category-list');
                    categoryList.innerHTML = '';
                    metadata.Categorization.forEach(category => {
                        const categoryItem = document.createElement('li');
                        categoryItem.textContent = category;
                        categoryList.appendChild(categoryItem);
                        categoryItem.addEventListener('click', function () {
                            removeCategory(image_name, category);
                        });
                    });
                }
            };
            xhr2.send();
        }
    };
    xhr.send(JSON.stringify({ category: category, image_name: image_name }));
}

// Call addClickListenersToCategories to add event listeners to categories when the page loads
function addClickListenersToCategories() {
    const categoryItems = document.querySelectorAll('.category-item');
    categoryItems.forEach(categoryItem => {
        const category = categoryItem.textContent;
        categoryItem.addEventListener('click', function () {
            const image_name = document.getElementById('active-image').alt;
            removeCategory(image_name, category);
        });
    });
}
addClickListenersToCategories();


// Send a PUT request using AJAX to save the data
function saveData() {
    var xhr = new XMLHttpRequest();
    xhr.open('PUT', '/save');
    xhr.onload = function () {
        if (xhr.status === 200) {
            // Handle successful response
        } else {
            // Handle error response
        }
    };
    xhr.send();
}

// Send an autosave request every 5 minutes
setInterval(function () {
    var xhr = new XMLHttpRequest();
    xhr.open('PUT', '/save');
    xhr.onload = function () {
        if (xhr.status === 200) {
            console.log('Autosave successful');
        } else {
            console.log('Autosave failed');
        }
    };
    xhr.send();
}, 300000); // 5 minutes in milliseconds

// Listen for click event on the "Save" button
document.getElementById('save-form').addEventListener('submit', function (event) {
    // Prevent the default form submission behavior
    event.preventDefault();
    // Save the data using AJAX
    saveData();
});

// Listen for submit event on the "resetfilter" form
document.getElementById('resetfilter').addEventListener('submit', function (event) {
    // Prevent the default form submission behavior
    event.preventDefault();
    
    // Send a POST request to reset the filter
    fetch('/resetfilter', {
      method: 'POST',
    })
    .then(response => {
      // Check if the response was successful
      if (response.ok) {
        // Redirect to the new URL
        window.location.href = response.url;
      } else {
        // Handle error response
        console.error('Error resetting filter');
      }
    })
    .catch(error => {
      // Handle network errors
      console.error('Network error:', error);
    });
  });
  

$(document).ready(function () {
    $("#filter-form").submit(function (event) { // Submit the filter form via AJAX when the "Filter" button is clicked
        event.preventDefault();
        var formData = $(this).serialize();
        $.ajax({
            url: "/filter_images",
            type: "POST",
            data: formData,
            dataType: "json",
            success: function (response) {
                console.log(response)
                window.location.replace(response); // redirect to the image viewer with a filtered image
            },
            error: function (jqXHR, textStatus, errorThrown) { // handle http errors
                console.log(response)
                alert(textStatus + ": " + errorThrown);
            }
        });
    });
});

function setThemeCookieXHR(theme) {
    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/set_theme_cookie');
    xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4 && xhr.status === 200) {
            var response = JSON.parse(xhr.responseText);
            // Update any data in the frontend that needs to be updated
        }
    };
    xhr.send('theme=' + encodeURIComponent(theme));
}

function setThemeCookieDOM(theme) {
    document.cookie = "theme=" + encodeURIComponent(theme) + "; path=/";
    console.log('Setting theme cookie to:', theme);
}

function setStyle(style) {
    console.log('Setting style to:', style);
    var link = document.querySelector('link[href*="/css/"]');
    link.href = link.href.replace(/\/css\/\w+\.css/, '/css/' + style + '.css');
    setThemeCookieDOM(style); // Set theme cookie with new value
}

function getCookie(name) {
    var cookies = document.cookie.split(';');
    for (var i = 0; i < cookies.length; i++) {
        var cookie = cookies[i].trim();
        if (cookie.indexOf(name + '=') === 0) {
            return decodeURIComponent(cookie.substring(name.length + 1));
        }
    }
    return null;
}

function setThemeFromCookie() {
    var theme = getCookie('theme');
    console.log('Setting theme cookie to:', theme);
    if (theme) {
        setStyle(theme);
        setThemeCookieXHR(theme); // Update cookie on server side
    }
}

function navigate(direction) {
    const img = document.getElementById('active-image');
    const imgsrc = img.getAttribute('alt');
    var imageName = encodeURIComponent(imgsrc);
    var url = "/imagedirection?direction=" + direction + "&image_name=" + imageName;
    location.href = url;
}

// Call setThemeFromCookie() on page load
window.addEventListener('load', setThemeFromCookie);

// Call setThemeFromCookie() whenever the theme selector is changed
document.getElementById('default-style').addEventListener('click', setThemeFromCookie);
document.getElementById('dark-style').addEventListener('click', setThemeFromCookie);
document.getElementById('light-style').addEventListener('click', setThemeFromCookie);

// Load initial thumbnails
lazyLoadThumbnails();

const filterbar = document.querySelector('.filterbar');
const filterbtn = document.querySelector('.filterbtn');

filterbtn.addEventListener('click', () => {
    filterbar.classList.toggle('open');
});