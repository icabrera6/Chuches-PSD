from flask import Flask, render_template, request, redirect, url_for, session, abort, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
import os

app = Flask(__name__)

# Configuración de la base de datos
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///store.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'supersecretkey'

db = SQLAlchemy(app)

# ---------------------------
# Modelos
# ---------------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    # Se guardan nombre y apellidos; se exige que el nombre (usuario) también sea único
    nombre = db.Column(db.String(100), unique=True, nullable=False)
    apellidos = db.Column(db.String(100), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_seller = db.Column(db.Boolean, default=False)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    precio = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    image_path = db.Column(db.String(200), nullable=False)  # Ruta de la imagen
    # Se asocia el producto con el vendedor que lo agregó
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    seller = db.relationship('User', backref=db.backref('products', lazy=True))

# ---------------------------
# Inicializar tablas
# ---------------------------
@app.before_request
def create_tables():
    db.create_all()

@app.before_request
def create_test_users():
    # Usuario solo admin
    if not User.query.filter_by(email='admin@example.com').first():
        user = User(
            email='admin@example.com',
            password='pass',  # Contraseña en texto plano
            nombre='Admin',
            apellidos='Test',
            is_admin=True,
            is_seller=False
        )
        db.session.add(user)

    # Usuario solo vendedor
    if not User.query.filter_by(email='seller@example.com').first():
        user = User(
            email='seller@example.com',
            password='pass',  # Contraseña en texto plano
            nombre='Seller',
            apellidos='Test',
            is_admin=False,
            is_seller=True
        )
        db.session.add(user)

    # Usuario comprador
    if not User.query.filter_by(email='comprador@example.com').first():
        user = User(
            email='comprador@example.com',
            password='pass',  # Contraseña en texto plano
            nombre='Comprador',
            apellidos='Test',
            is_admin=False,
            is_seller=False
        )
        db.session.add(user)

    db.session.commit()

# ---------------------------
# Helpers para roles y sesión
# ---------------------------
def get_current_user():
    user_id = session.get('user_id')
    if user_id:
        return User.query.get(user_id)
    return None

def is_seller():
    user = get_current_user()
    return user and user.is_seller

@app.context_processor
def inject_user():
    return dict(current_user=get_current_user())

# ---------------------------
# Rutas principales
# ---------------------------
@app.route('/')
def goto_inicio():
    return redirect(url_for('inicio'))

# La página de inicio muestra los productos directamente.
@app.route('/inicio', methods=['GET', 'POST'])
def inicio():
    # Si se envía el formulario de agregar producto (solo para vendedores)
    if request.method == 'POST':
        if not is_seller():
            abort(403)
        nombre = request.form.get('nombre')
        descripcion = request.form.get('descripcion')
        precio = request.form.get('precio')
        stock = request.form.get('stock')
        if not all([nombre, descripcion, precio, stock]):
            flash("Todos los campos son requeridos para agregar un producto.")
            return redirect(url_for('inicio'))
        try:
            precio = float(precio)
            stock = int(stock)
        except ValueError:
            flash("Precio debe ser numérico y stock debe ser entero.")
            return redirect(url_for('inicio'))
        imagen = request.files.get('imagen')
        image_path = None
        if imagen:
            filename = imagen.filename
            upload_folder = os.path.join('static', 'imgs')
            os.makedirs(upload_folder, exist_ok=True)
            file_path = os.path.join(upload_folder, filename)
            imagen.save(file_path)
            image_path = os.path.join('static', 'imgs', filename)
        current_user = get_current_user()
        product = Product(
            nombre=nombre,
            descripcion=descripcion,
            precio=precio,
            stock=stock,
            image_path=image_path,
            seller_id=current_user.id if current_user else None
        )
        db.session.add(product)
        db.session.commit()
        return redirect(url_for('inicio'))
    # GET: listar productos en la página de inicio
    products = Product.query.all()
    return render_template('inicio.html', products=products)

# ---------------------------
# Inventario del vendedor
# ---------------------------
@app.route('/inventario', methods=['GET', 'POST'])
def inventario():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        descripcion = request.form.get('descripcion')
        precio = request.form.get('precio')
        stock = request.form.get('stock')
        imagen = request.form.get('imagen')

        # Validar los datos del formulario
        if not (nombre and descripcion and precio and stock and imagen):
            flash("Todos los campos son obligatorios.", "error")
            return redirect(url_for('inventario'))

        try:
            precio = float(precio)
            stock = int(stock)
        except ValueError:
            flash("El precio debe ser un número y el stock un entero.", "error")
            return redirect(url_for('inventario'))

        # Concatenar la ruta de la carpeta imgs
        image_path = f"imgs/{imagen}"

        # Crear el producto y guardarlo en la base de datos
        nuevo_producto = Product(nombre=nombre, descripcion=descripcion, precio=precio, stock=stock, image_path=image_path)
        db.session.add(nuevo_producto)
        db.session.commit()

        flash("Producto agregado exitosamente.", "success")
        return redirect(url_for('inventario'))

    # Obtener todos los productos para mostrarlos en el inventario
    productos = Product.query.all()
    return render_template('inventario.html', products=productos)

# ---------------------------
# Registro de usuario
# ---------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        nombre = request.form.get('nombre')
        apellidos = request.form.get('apellidos')
        if not email or not password or not nombre or not apellidos:
            return render_template('register.html', error="Todos los campos son requeridos")
        # Se comprueba que ni el email ni el nombre ya existan
        if User.query.filter(or_(User.email == email, User.nombre == nombre)).first():
            return render_template('register.html', error="El email o el nombre de usuario ya existe")
        user = User(email=email, password=password, nombre=nombre, apellidos=apellidos)
        db.session.add(user)
        db.session.commit()
        return render_template('register_success.html', usuario=nombre)
    return render_template('register.html')

# ---------------------------
# Login de usuario
# ---------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Obtener los valores enviados desde el formulario
        login_value = request.form.get('login')  # Puede ser email o nombre de usuario
        password = request.form.get('password')  # Contraseña en texto plano

        # Buscar al usuario por email o nombre de usuario
        user = None
        if login_value and '@' in login_value:  # Si contiene '@', es un email
            user = User.query.filter_by(email=login_value, password=password).first()
        else:  # Si no, es un nombre de usuario
            user = User.query.filter_by(nombre=login_value, password=password).first()

        # Verificar si el usuario existe y las credenciales son correctas
        if user:
            session['user_id'] = user.id  # Guardar el ID del usuario en la sesión
            flash(f'Bienvenido, {user.nombre}!', 'success')
            return redirect(url_for('inicio'))
        else:
            flash('Credenciales incorrectas', 'error')
            return redirect(url_for('login'))

    # Si es una solicitud GET, renderizar el formulario de inicio de sesión
    return render_template('login.html')

# ---------------------------
# Logout
# ---------------------------
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('inicio'))

# ---------------------------
# Eliminar producto (solo para el vendedor que lo agregó)
# ---------------------------
@app.route('/producto/delete/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    current_user = get_current_user()
    if not current_user:
        abort(403)  # Solo usuarios autenticados pueden eliminar productos

    product = Product.query.get_or_404(product_id)

    # Permitir que los administradores eliminen cualquier producto
    if current_user.is_admin:
        db.session.delete(product)
        db.session.commit()
        flash("Producto eliminado exitosamente.", "success")
        return redirect(url_for('inventario'))

    # Permitir que los vendedores eliminen solo los productos que ellos agregaron
    if current_user.is_seller and product.seller_id == current_user.id:
        db.session.delete(product)
        db.session.commit()
        flash("Producto eliminado exitosamente.", "success")
        return redirect(url_for('inventario'))

    # Si no es administrador ni el vendedor que agregó el producto, denegar acceso
    abort(403)

# ---------------------------
# Carrito de compra (almacenado en sesión)
# ---------------------------
@app.route('/carrito', methods=['GET', 'POST'])
def carrito():
    if 'cart' not in session:
        session['cart'] = {}
    if request.method == 'POST':
        product_id = request.form.get('product_id')
        quantity = request.form.get('quantity')
        if not product_id or not quantity:
            return redirect(url_for('carrito'))
        try:
            quantity = int(quantity)
        except ValueError:
            return redirect(url_for('carrito'))
        product = Product.query.get(int(product_id))
        if not product:
            flash("El producto no existe.", "error")
            return redirect(url_for('carrito'))
        if quantity > product.stock:
            flash(f"No hay suficiente stock para {product.nombre}.", "error")
            return redirect(url_for('carrito'))
        cart = session['cart']
        if quantity <= 0:
            cart.pop(product_id, None)
        else:
            cart[product_id] = quantity
        session['cart'] = cart
        return redirect(url_for('carrito'))
    cart = session['cart']
    cart_items = []
    total = 0
    for prod_id, qty in cart.items():
        product = Product.query.get(int(prod_id))
        if product:
            subtotal = product.precio * qty
            cart_items.append({
                'id': product.id,
                'nombre': product.nombre,
                'cantidad': qty,
                'precio_unit': product.precio,
                'subtotal': subtotal,
                'stock': product.stock,
                'image_path': product.image_path  # Asegúrate de incluir la ruta de la imagen
            })
            total += subtotal
    return render_template('carrito.html', cart_items=cart_items, total=total)

# ---------------------------
# Proceso de compra
# ---------------------------
@app.route('/compra', methods=['POST'])
def compra():
    if 'cart' not in session or not session['cart']:
        flash("El carrito está vacío.", "error")
        return redirect(url_for('carrito'))
    cart = session['cart']
    total = 0.0

    for prod_id, quantity in cart.items():
        product = Product.query.get(int(prod_id))
        if not product:
            flash(f"El producto con ID {prod_id} no existe.", "error")
            return redirect(url_for('carrito'))
        if product.stock < quantity:
            flash(f"El producto {product.nombre} no tiene stock suficiente.", "error")
            return redirect(url_for('carrito'))
        total += product.precio * quantity

    for prod_id, quantity in cart.items():
        product = Product.query.get(int(prod_id))
        product.stock -= quantity
        if product.stock <= 0:
            db.session.delete(product)
    db.session.commit()
    session['cart'] = {}  # Limpiar el carrito después de la compra
    flash("Compra realizada con éxito.", "success")
    return redirect(url_for('compra_exito', total=total))

# ---------------------------
# Compra exitosa
# ---------------------------
@app.route('/compra_exito')
def compra_exito():
    total = request.args.get('total', 0)
    return render_template('compra_exito.html', total=total)

# ---------------------------
# Eliminar producto del carrito
# ---------------------------
@app.route('/delete_from_cart', methods=['POST'])
def delete_from_cart():
    if 'cart' not in session:
        session['cart'] = {}
    product_id = request.form.get('product_id')
    if product_id:
        cart = session['cart']
        cart.pop(product_id, None)
        session['cart'] = cart
        flash("Producto eliminado del carrito.", "success")
    return redirect(url_for('carrito'))

# ---------------------------
# Main
# ---------------------------
if __name__ == '__main__':
    app.run(debug=True)