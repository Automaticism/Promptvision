
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
            xhr.open('PUT', `/set-rating/${image_name}`);
            xhr.setRequestHeader('Content-Type', 'application/json');
            xhr.onreadystatechange = function () {
                if (this.readyState === XMLHttpRequest.DONE && this.status === 200) {
                    console.log('Rating set!');
                    
                    // Update the star icons to reflect the new rating
                    starIcons.forEach((icon) => {
                        if (icon.getAttribute('data-rating') <= rating) {
                            icon.textContent = 'star';
                        } else {
                            icon.textContent = 'star_border';
                        }
                    });
                }
            };
            xhr.send(JSON.stringify({ rating: rating }));
        }  else if ((event.ctrlKey || event.metaKey) && event.key === "s") {
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
    const container = document.getElementById('thumbnails');
    const thumbnailContainerWidth = window.innerWidth * 0.2;
    const maxThumbnailsPerRow = Math.floor(thumbnailContainerWidth / 50);
    const maxThumbnailsPerColumn = Math.floor(container.clientHeight / 65);
    let numImages;
    const maxThumbnails = Math.min(maxThumbnailsPerRow * maxThumbnailsPerColumn, numImages); // Limit to the number of available images
    const limit = maxThumbnails;
    let offset = limit; // Set offset to `limit` to fetch more thumbnails after the initial set
    const img = document.getElementById('active-image');
    const imgsrc = img.getAttribute('src');

    // Fetch the number of images using AJAX
    fetch('/numimages')
        .then(response => response.json())
        .then(data => {
            numImages = data.num_images;
            const maxThumbnails = Math.min(maxThumbnailsPerRow * maxThumbnailsPerColumn, numImages); // Limit to the number of available images
            const limit = maxThumbnails;
            let offset = limit; // Set offset to `limit` to fetch more thumbnails after the initial set

            // Fetch some initial thumbnails using AJAX
            fetch(`/thumbnails?limit=${limit}&offset=0&imgsrc=${imgsrc}`)
                .then(response => response.text())
                .then(html => {
                    container.insertAdjacentHTML('beforeend', `<div class="thumbnail">${html}</div>`);
                });
        });

    function loadMoreThumbnails() {
        if (container.getBoundingClientRect().top < window.innerHeight && offset < numImages) {
            // Fetch more thumbnails using AJAX
            fetch(`/thumbnails?limit=${limit}&offset=${offset}&imgsrc=${imgsrc}`)
                .then(response => response.text())
                .then(html => {
                    container.insertAdjacentHTML('beforeend', `<div class="thumbnail">${html}</div>`);
                    offset += limit;
                });
        }
    }

    // Load more thumbnails when user scrolls near the end of the container
    window.addEventListener('scroll', loadMoreThumbnails);

    // Load more thumbnails when container is resized and becomes visible
    const resizeObserver = new ResizeObserver(() => {
        if (container.getBoundingClientRect().top < window.innerHeight && offset < numImages) {
            loadMoreThumbnails();
        }
    });
    resizeObserver.observe(container);
}

lazyLoadThumbnails();

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
        xhr.open('PUT', `/toggle/${image_name}`);
        xhr.setRequestHeader('Content-Type', 'application/json');
        xhr.onreadystatechange = function () {
            if (this.readyState === XMLHttpRequest.DONE && this.status === 200) {
                console.log(this)
                const newFavorite = JSON.parse(this.responseText);
                const formMethod = newFavorite ? "PUT" : "POST"; // Define form method based on current state
                const currentForm = event.target.closest('form'); // Get the current form being processed
                const formMethodInput = currentForm.querySelector('[name="_method"]');
                if (formMethodInput) {
                    formMethodInput.value = formMethod;
                }
                currentForm.querySelector('.favorite-toggle').innerHTML = newFavorite ? '<i class="material-icons">favorite</i>' : '<i class="material-icons">favorite_border</i>'; // Update button label with heart icon
            }
        };
        xhr.send();
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
        xhr.open('PUT', `/set-rating/${image_name}`);
        xhr.setRequestHeader('Content-Type', 'application/json');
        xhr.onreadystatechange = function () {
            if (this.readyState === XMLHttpRequest.DONE && this.status === 200) {
                console.log('Rating set!');
            }
        };
        xhr.send(JSON.stringify({ rating: rating }));
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
        xhr.open('PUT', `/set-rating/${image_name}`);
        xhr.setRequestHeader('Content-Type', 'application/json');
        xhr.onreadystatechange = function () {
            if (this.readyState === XMLHttpRequest.DONE && this.status === 200) {
                console.log('Rating reset!');
            }
        };
        xhr.send(JSON.stringify({ rating: rating }));
    });
});

// Tag form
const addTagsForm = document.querySelector('#tag-form');
addTagsForm.addEventListener('submit', event => {
    event.preventDefault();

    const image_name = document.getElementById('active-image').alt;
    const tags = document.getElementById('tags').value.trim().split(',');

    const xhr = new XMLHttpRequest();
    xhr.open('PUT', `/add-tags/${image_name}`);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.onreadystatechange = function () {
        if (this.readyState === XMLHttpRequest.DONE && this.status === 200) {
            console.log("Tags added");
            // Get updated metadata for image
            const xhr2 = new XMLHttpRequest();
            xhr2.open('GET', `/get-metadata/${image_name}`);
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
    xhr.send(JSON.stringify({ tags: tags }));
});

// Function to remove tag from image
function removeTag(image_name, tag) {
    const xhr = new XMLHttpRequest();
    xhr.open('PUT', `/remove-tags/${image_name}`);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.onreadystatechange = function () {
        if (this.readyState === XMLHttpRequest.DONE && this.status === 200) {
            console.log("Tag removed");
            // Get updated metadata for image
            const xhr2 = new XMLHttpRequest();
            xhr2.open('GET', `/get-metadata/${image_name}`);
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
    xhr.send(JSON.stringify({ tag: tag }));
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
    xhr.open('PUT', `/assign-category/${image_name}`);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.onreadystatechange = function () {
        if (this.readyState === XMLHttpRequest.DONE && this.status === 200) {
            console.log('Category assigned!');
            // Get updated metadata for image
            const xhr2 = new XMLHttpRequest();
            xhr2.open('GET', `/get-metadata/${image_name}`);
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
    xhr.send(JSON.stringify({ categories: categories }));
});

// Function to remove category from image
function removeCategory(image_name, category) {
    const xhr = new XMLHttpRequest();
    xhr.open('PUT', `/remove-category/${image_name}`);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.onreadystatechange = function () {
        if (this.readyState === XMLHttpRequest.DONE && this.status === 200) {
            console.log("Category removed");
            // Get updated metadata for image
            const xhr2 = new XMLHttpRequest();
            xhr2.open('GET', `/get-metadata/${image_name}`);
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
    xhr.send(JSON.stringify({ category: category }));
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
setInterval(function() {
    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/autosave');
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
            error: function(jqXHR, textStatus, errorThrown) { // handle http errors
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
    xhr.onreadystatechange = function() {
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
  
  // Call setThemeFromCookie() on page load
  window.addEventListener('load', setThemeFromCookie);
  
  // Call setThemeFromCookie() whenever the theme selector is changed
  document.getElementById('default-style').addEventListener('click', setThemeFromCookie);
  document.getElementById('dark-style').addEventListener('click', setThemeFromCookie);
  document.getElementById('light-style').addEventListener('click', setThemeFromCookie);

  $(document).ready(function() {
    $(".filterbar").hide();
    $("#filter-toggle").click(function() {
      $(".filterbar").slideToggle("fast");
    });
  });