// Initialize range sliders
document.addEventListener('DOMContentLoaded', function() {
    // Property search range slider
    const rangeSlider = document.querySelector('.range-slider-ui');
    if (rangeSlider) {
        noUiSlider.create(rangeSlider, {
            start: [1000, 3000],
            connect: true,
            range: {
                'min': 0,
                'max': 5000
            },
            step: 100,
            tooltips: [true, true],
            format: {
                to: function(value) {
                    return '$' + Math.round(value);
                },
                from: function(value) {
                    return value.replace('$', '');
                }
            }
        });
        
        // Update hidden inputs when slider changes
        rangeSlider.noUiSlider.on('update', function(values, handle) {
            const minInput = document.querySelector('[data-range-slider-min]');
            const maxInput = document.querySelector('[data-range-slider-max]');
            
            if (handle === 0) {
                minInput.value = values[0].replace('$', '');
            } else {
                maxInput.value = values[1].replace('$', '');
            }
        });
    }
    
    // Initialize property image carousels
    document.querySelectorAll('.property-image-carousel').forEach(carousel => {
        const propertyId = carousel.dataset.propertyId;
        new Swiper(carousel, {
            loop: true,
            pagination: {
                el: `.swiper-pagination[data-property-id="${propertyId}"]`,
                clickable: true,
            },
            navigation: {
                nextEl: `.swiper-button-next[data-property-id="${propertyId}"]`,
                prevEl: `.swiper-button-prev[data-property-id="${propertyId}"]`,
            },
        });
    });
    
    // Favorite button toggle
    document.querySelectorAll('.favorite-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const propertyId = this.dataset.propertyId;
            const isFavorite = this.classList.contains('active');
            
            fetch(`/properties/${propertyId}/favorite/`, {
                method: isFavorite ? 'DELETE' : 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({}),
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.classList.toggle('active');
                    this.querySelector('i').classList.toggle('fi-heart-filled');
                    this.querySelector('i').classList.toggle('fi-heart');
                }
            });
        });
    });
});

// Helper function to get CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}