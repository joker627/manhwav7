import { loadAllComponents } from "./ui/components.js";
import { createCarousel } from "./ui/carousel.js";

document.addEventListener('DOMContentLoaded', async () => {
	try {
		await loadAllComponents();
		createCarousel('#hero', {
			sliderSelector: '.hero-slider',
			slideSelector: '.hero-slide',
			autoplayInterval: 5000,
			pauseOnHover: true
		});

	} finally {
		document.documentElement.classList.remove('is-loading');
	}
});

