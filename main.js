let currentSlide = 0;
let totalHours = 72;
let currentFolder = '';
let currentFormat = 'png';

function initializeSlideshow() {
    const folder = document.getElementById('folderSelect').value;

    if (!folder) {
        showError('Please select a date to start the slideshow');
        return;
    }

    currentFolder = folder;
    currentSlide  = 0;
    
    const slideshowContainer = document.querySelector('.slideshow-container');
    slideshowContainer.innerHTML = `
        <div class="slide active">
            <img id="mainImage" src="" alt="" />
            <div class="filename" id="filenameDisplay"></div>
        </div>
    `;

    // Load the first image
    loadCurrentImage();
    updateSlideCounter();
    updateNavigationButtons();
}

function loadCurrentImage() {
    const img = document.getElementById('mainImage');
    const filenameDisplay = document.getElementById('filenameDisplay');
    
    if (!img || totalHours === 0) return;
    
    const filename = `SO2_col_mass_${(currentSlide).toString().padStart(3, '0')}.${currentFormat}`;
    const imagePath = `${currentFolder}/${filename}`;
    
    img.src = imagePath;
    img.alt = filename;
    filenameDisplay.textContent = filename;
    
    img.onerror = function() {
        this.style.display = 'none';
        filenameDisplay.innerHTML = `<span class="error">Image not found: ${filename}</span>`;
    };
    
    img.onload = function() {
        this.style.display = 'block';
        filenameDisplay.innerHTML = filename;
    };
}

function showError(message) {
    const slideshowContainer = document.querySelector('.slideshow-container');
    slideshowContainer.innerHTML = `
        <div class="slide active">
            <div class="error">${message}</div>
        </div>
    `;
    totalHours = 0;
    updateSlideCounter();
    updateNavigationButtons();
}

function changeSlide(direction) {
    if (totalHours === 0) return;
    
    currentSlide += direction;
    
    if (currentSlide > totalHours) {
        currentSlide = 0;
    } else if (currentSlide < 0) {
        currentSlide = totalHours;
    }
    
    loadCurrentImage();
    updateSlideCounter();
    updateNavigationButtons();
}

function updateSlideCounter() {
    const counter = document.getElementById('slideCounter');
    if (totalHours > 0) {
        counter.textContent = `${currentSlide} / ${totalHours}`;
    } else {
        counter.textContent = '0 / 0';
    }
}

function updateNavigationButtons() {
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    
    if (totalHours === 0) {
        prevBtn.disabled = true;
        nextBtn.disabled = true;
    } else {
        prevBtn.disabled = false;
        nextBtn.disabled = false;
    }
}

// Event listeners
document.getElementById('folderSelect').addEventListener('change', initializeSlideshow);
window.addEventListener('load', initializeSlideshow);

// Keyboard navigation
document.addEventListener('keydown', function(event) {
    if (event.key === 'ArrowLeft') {
        changeSlide(-6);
    } else if (event.key === 'ArrowRight') {
        changeSlide(6);
    }
});
