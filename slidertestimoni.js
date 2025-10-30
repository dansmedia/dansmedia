        document.addEventListener('DOMContentLoaded', function() {
            const sliderWrapper = document.querySelector('.slider-wrapper');
            const slides = document.querySelectorAll('.slide');
            const prevBtn = document.getElementById('prevBtn');
            const nextBtn = document.getElementById('nextBtn');
            const dotsContainer = document.getElementById('sliderDots');

            let currentIndex = 0;
            const totalSlides = slides.length;
            let slideInterval; // Untuk slider otomatis

            // Buat titik-titik indikator
            for (let i = 0; i < totalSlides; i++) {
                const dot = document.createElement('span');
                dot.classList.add('dot');
                dot.setAttribute('data-index', i);
                dotsContainer.appendChild(dot);
            }

            const dots = document.querySelectorAll('.dot');
            dots[0].classList.add('active'); // Aktifkan titik pertama

            function updateSlider() {
                // Geser slider-wrapper
                sliderWrapper.style.transform = `translateX(-${currentIndex * 100}%)`;
                
                // Perbarui titik aktif
                dots.forEach(dot => dot.classList.remove('active'));
                dots[currentIndex].classList.add('active');
            }

            function goToNextSlide() {
                currentIndex = (currentIndex + 1) % totalSlides;
                updateSlider();
            }

            function goToPrevSlide() {
                currentIndex = (currentIndex - 1 + totalSlides) % totalSlides;
                updateSlider();
            }

            function startAutoSlide() {
                // Ganti 5000 (5 detik) jika ingin lebih cepat atau lambat
                slideInterval = setInterval(goToNextSlide, 5000); 
            }

            function stopAutoSlide() {
                clearInterval(slideInterval);
            }

            // Event Listeners
            nextBtn.addEventListener('click', () => {
                goToNextSlide();
                stopAutoSlide(); // Hentikan slide otomatis jika tombol ditekan
            });

            prevBtn.addEventListener('click', () => {
                goToPrevSlide();
                stopAutoSlide(); // Hentikan slide otomatis jika tombol ditekan
            });

            dots.forEach(dot => {
                dot.addEventListener('click', (e) => {
                    currentIndex = parseInt(e.target.getAttribute('data-index'));
                    updateSlider();
                    stopAutoSlide(); // Hentikan slide otomatis jika titik ditekan
                });
            });

            // Mulai slide otomatis saat halaman dimuat
            startAutoSlide();
        });
