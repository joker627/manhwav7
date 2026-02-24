import { loadAllComponents } from "./ui/components.js";

document.addEventListener('DOMContentLoaded', async () => {
	try {
		await loadAllComponents();
	} finally {
		// remove loading class to reveal any interactive content
		document.documentElement.classList.remove('is-loading');
	}
});

