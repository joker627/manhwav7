export function createCarousel(containerSelector, options = {}) {
    const {
        sliderSelector = '.hero-slider',
        slideSelector = 'img',
        prevBtnSelector = null,
        nextBtnSelector = null,
        autoplayInterval = 3000,
        transitionDuration = 0.5,
        pauseOnHover = true
    } = options;

    const container = document.querySelector(containerSelector);
    if (!container) {
        console.warn(`Contenedor "${containerSelector}" no encontrado.`);
        return null;
    }

    const slider = container.querySelector(sliderSelector);
    if (!slider) {
        console.warn(`Slider "${sliderSelector}" no encontrado dentro del contenedor.`);
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

    // Calcula el ancho actual de una diapositiva (útil para responsive)
    const getSlideWidth = () => slides[0].offsetWidth;

    // Función para mover el slider a un índice específico
    const goToSlide = (index, animate = true) => {
        if (index < 0) index = totalSlides - 1;
        if (index >= totalSlides) index = 0;

        const width = getSlideWidth();
        slider.style.transition = animate ? `transform ${transitionDuration}s ease` : 'none';
        slider.style.transform = `translateX(-${index * width}px)`;
        currentIndex = index;
    };

    // Funciones de navegación
    const next = () => goToSlide(currentIndex + 1);
    const prev = () => goToSlide(currentIndex - 1);

    // Control de autoplay
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

    // Configurar botones si se proporcionan
    if (prevBtnSelector) {
        const prevBtn = container.querySelector(prevBtnSelector);
        if (prevBtn) {
            prevBtn.addEventListener('click', (e) => {
                e.preventDefault();
                stopAutoplay();
                prev();
                startAutoplay();
            });
        }
    }

    if (nextBtnSelector) {
        const nextBtn = container.querySelector(nextBtnSelector);
        if (nextBtn) {
            nextBtn.addEventListener('click', (e) => {
                e.preventDefault();
                stopAutoplay();
                next();
                startAutoplay();
            });
        }
    }

    // Pausar al hacer hover (opcional)
    if (pauseOnHover) {
        container.addEventListener('mouseenter', stopAutoplay);
        container.addEventListener('mouseleave', startAutoplay);
    }

    // Ajustar al redimensionar la ventana
    const handleResize = () => goToSlide(currentIndex, false);
    window.addEventListener('resize', handleResize);

    // Iniciar autoplay
    startAutoplay();

    // Retornar una API para control externo (opcional)
    return {
        next,
        prev,
        goToSlide,
        startAutoplay,
        stopAutoplay,
        destroy: () => {
            stopAutoplay();
            window.removeEventListener('resize', handleResize);
            if (pauseOnHover) {
                container.removeEventListener('mouseenter', stopAutoplay);
                container.removeEventListener('mouseleave', startAutoplay);
            }
            // Aquí podrías eliminar otros eventos si es necesario
        }
    };
}