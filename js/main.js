// Hero Carousel Configuration
document.addEventListener('DOMContentLoaded', function() {
    // Initialize carousel with custom interval
    var heroCarousel = new bootstrap.Carousel(document.getElementById('heroCarousel'), {
        interval: 60000, // 6 seconds
        pause: false,
        wrap: true
    });
    
    // Optional: Add animation to captions
    document.querySelectorAll('#heroCarousel .carousel-item').forEach((item, index) => {
        item.addEventListener('slide.bs.carousel', function() {
            const captions = this.querySelector('.carousel-caption');
            captions.style.opacity = '0';
            captions.style.transform = 'translateY(20px)';
            
            setTimeout(() => {
                captions.style.opacity = '1';
                captions.style.transform = 'translateY(0)';
                captions.style.transition = 'all 0.5s ease';
            }, 50);
        });
    });
});