document.addEventListener("DOMContentLoaded", function() {
    // Buscar en la barra de búsqueda
    const searchInput = document.querySelector('.navbar-search input');
    if (searchInput) {
        searchInput.addEventListener('keyup', function() {
            const filter = searchInput.value.toLowerCase();
            const products = document.querySelectorAll('.product-card');
            
            products.forEach(function(product) {
                const productName = product.querySelector('.product-name').textContent.toLowerCase();
                if (productName.includes(filter)) {
                    product.style.display = "block"; // Mostrar el producto si coincide
                } else {
                    product.style.display = "none"; // Ocultar el producto si no coincide
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