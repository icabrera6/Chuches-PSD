document.addEventListener("DOMContentLoaded", function() {
    // Obtener el elemento input de la búsqueda en la navbar
    const searchInput = document.querySelector('.navbar-search input');
    if (searchInput) {
      searchInput.addEventListener('keyup', function() {
        const filter = searchInput.value.toLowerCase();
        // Seleccionar todos los productos en la sección correspondiente
        document.querySelectorAll('.products .product').forEach(function(product) {
          const productNameElem = product.querySelector('h3');
          if (productNameElem) {
            const productName = productNameElem.textContent.toLowerCase();
            // Mostrar el producto si su nombre incluye el filtro, de lo contrario ocultarlo
            product.style.display = productName.includes(filter) ? "block" : "none";
          }
        });
      });
    }
  });


document.addEventListener("DOMContentLoaded", function(){
  setTimeout(function(){
    const flashContainer = document.querySelector('.flash-messages');
    if(flashContainer){
      flashContainer.style.opacity = '0';
      // Elimina el contenedor después de la transición (1 seg extra)
      setTimeout(() => flashContainer.remove(), 1000);
    }
  }, 3000); // 3000 ms = 3 seg; puedes ajustarlo a 5000 si prefieres 5 seg
});


document.addEventListener('DOMContentLoaded', function(){
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
  });