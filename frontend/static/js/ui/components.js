
async function loadcomponent(Id, archivo) {
  const contenedor = document.getElementById(Id);
  const respuesta = await fetch(`components/${archivo}`);
  const contenido = await respuesta.text();
  contenedor.innerHTML = contenido;
  return true;
}
// Cargar cada sección de la página y devolver una Promise que resuelve cuando todo cargue
function loadAllComponents() {
  return Promise.all([
    loadcomponent("main-navbar", "navbar.html"),
    loadcomponent("main-hero", "hero.html"),
    loadcomponent("main-content", "lista-capitulos.html"),
    loadcomponent("main-footer", "footer.html")
  ]);
}

export { loadAllComponents, loadcomponent };