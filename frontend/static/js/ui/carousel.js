export function createCarousel(containerSelector, options = {}) {
    const {
        sliderSelector = '.hero-slider',
        slideSelector = '.hero-slide',
        prevBtnSelector = '.hero-btn--prev',
        nextBtnSelector = '.hero-btn--next',
        dotsContainerId = 'hero-dots',
        autoplayInterval = 5000,
        transitionDuration = 0.65,
        pauseOnHover = true
    } = options;

    const container = document.querySelector(containerSelector);
    if (!container) {
        console.warn(`Contenedor "${containerSelector}" no encontrado.`);
        return null;
    }

    const slider = container.querySelector(sliderSelector);
    if (!slider) {
        console.warn(`Slider "${sliderSelector}" no encontrado.`);
        return null;
    }

    const slides = slider.querySelectorAll(slideSelector);
    if (!slides.length) {
        console.warn('No hay diapositivas en el carrusel.');
        return null;
    }

    let currentIndex = 0;
    let autoplayTimer = null;
    const totalSlides = slides.length;

    // ── Dots ──
    const dotsContainer = document.getElementById(dotsContainerId);
    let dots = [];

    if (dotsContainer) {
        for (let i = 0; i < totalSlides; i++) {
            const dot = document.createElement('button');
            dot.className = 'hero-dot' + (i === 0 ? ' active' : '');
            dot.setAttribute('aria-label', `Ir a la serie ${i + 1}`);
            dot.addEventListener('click', () => {
                stopAutoplay();
                goToSlide(i);
                startAutoplay();
            });
            dotsContainer.appendChild(dot);
            dots.push(dot);
        }
    }

    const updateDots = (index) => {
        dots.forEach((d, i) => d.classList.toggle('active', i === index));
    };

    // ── Ancho de cada slide ──
    const getSlideWidth = () => slides[0].offsetWidth;

    // ── Ir a un slide ──
    const goToSlide = (index, animate = true) => {
        if (index < 0) index = totalSlides - 1;
        if (index >= totalSlides) index = 0;

        const width = getSlideWidth();
        slider.style.transition = animate
            ? `transform ${transitionDuration}s cubic-bezier(0.4, 0, 0.2, 1)`
            : 'none';
        slider.style.transform = `translateX(-${index * width}px)`;
        currentIndex = index;
        updateDots(currentIndex);
    };

    const next = () => goToSlide(currentIndex + 1);
    const prev = () => goToSlide(currentIndex - 1);

    // ── Autoplay ──
    const startAutoplay = () => {
        if (autoplayInterval > 0) {
            stopAutoplay();
            autoplayTimer = setInterval(next, autoplayInterval);
        }
    };

    const stopAutoplay = () => {
        if (autoplayTimer) {
            clearInterval(autoplayTimer);
            autoplayTimer = null;
        }
    };

    // ── Botones de navegación ──
    const prevBtn = container.querySelector(prevBtnSelector);
    if (prevBtn) {
        prevBtn.addEventListener('click', (e) => {
            e.preventDefault();
            stopAutoplay();
            prev();
            startAutoplay();
        });
    }

    const nextBtn = container.querySelector(nextBtnSelector);
    if (nextBtn) {
        nextBtn.addEventListener('click', (e) => {
            e.preventDefault();
            stopAutoplay();
            next();
            startAutoplay();
        });
    }

    // ── Pausar al pasar el cursor ──
    if (pauseOnHover) {
        container.addEventListener('mouseenter', stopAutoplay);
        container.addEventListener('mouseleave', startAutoplay);
    }

    // ── Swipe táctil ──
    let touchStartX = 0;
    container.addEventListener('touchstart', (e) => {
        touchStartX = e.touches[0].clientX;
    }, { passive: true });
    container.addEventListener('touchend', (e) => {
        const delta = touchStartX - e.changedTouches[0].clientX;
        if (Math.abs(delta) > 40) {
            stopAutoplay();
            delta > 0 ? next() : prev();
            startAutoplay();
        }
    }, { passive: true });

    // ── Ajustar al redimensionar ──
    window.addEventListener('resize', () => goToSlide(currentIndex, false));

    // ── Iniciar ──
    startAutoplay();
    return { goToSlide, next, prev, stop: stopAutoplay, start: startAutoplay };
}