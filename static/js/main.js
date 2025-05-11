document.addEventListener("DOMContentLoaded", function() {
  // Buscar en la navbar
  const searchInput = document.querySelector('.navbar-search input');
  if (searchInput) {
    searchInput.addEventListener('keyup', function() {
      const filter = searchInput.value.toLowerCase();
      document.querySelectorAll('.products .product').forEach(function(product) {
        const productNameElem = product.querySelector('h3');
        if (productNameElem) {
          const productName = productNameElem.textContent.toLowerCase();
          product.style.display = productName.includes(filter) ? "block" : "none";
        }
      });
    });
  }

  // Ocultar mensajes flash después de 3 segundos
  setTimeout(function(){
    const flashContainer = document.querySelector('.flash-messages');
    if(flashContainer){
      flashContainer.style.opacity = '0';
      setTimeout(() => flashContainer.remove(), 1000);
    }
  }, 3000);

  // Control de cantidad en el carrito
  document.querySelectorAll('.quantity-form').forEach(function(form){
    const decrementBtn = form.querySelector('.decrement-btn');
    const incrementBtn = form.querySelector('.increment-btn');
    const quantityField = form.querySelector('input[name="quantity"]');
    const stock = parseInt(incrementBtn.getAttribute('data-stock'));
    
    decrementBtn.addEventListener('click', function(){
      let current = parseInt(quantityField.value);
      if(current > 1){
        quantityField.value = current - 1;
        form.submit();
      }
    });
    
    incrementBtn.addEventListener('click', function(){
      let current = parseInt(quantityField.value);
      if(current < stock){
        quantityField.value = current + 1;
        form.submit();
      }
    });
  });

  // Slider automático para los banners
  const slider = document.querySelector('.slider');
  if (slider) {
    let slides = slider.querySelectorAll('img');
    let currentSlide = 0;
    // Solo mostrar el primer banner inicialmente
    slides.forEach((slide, index) => {
      slide.style.display = index === 0 ? 'block' : 'none';
    });
    // Cambiar banner cada 10 segundos
    setInterval(function(){
      slides[currentSlide].style.display = 'none';
      currentSlide = (currentSlide + 1) % slides.length;
      slides[currentSlide].style.display = 'block';
    }, 10000);
  }
});