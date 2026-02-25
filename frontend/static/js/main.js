import { loadAllComponents } from "./ui/components.js";
import { createCarousel } from "./ui/carousel.js";

document.addEventListener('DOMContentLoaded', async () => {
	try {
		await loadAllComponents();
		createCarousel('#hero', {
			sliderSelector: '.hero-slider',
			slideSelector: '.img-portada',
			autoplayInterval: 3000,   // Cambia cada 3 segundos
			pauseOnHover: true
		});

	} finally {
		document.documentElement.classList.remove('is-loading');
	}
});

