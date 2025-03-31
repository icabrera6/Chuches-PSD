from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

# Configuración de la base de datos
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///store.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'supersecretkey'

db = SQLAlchemy(app)

# Modelos
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    precio = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    image_path = db.Column(db.String(200), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)

    category = db.relationship('Category', backref=db.backref('products', lazy=True))

@app.before_first_request
def create_tables():
    db.create_all()

# ---------------------------
# Rutas principales
# ---------------------------
@app.route('/')
def goto_inicio():
    # Podrías redirigir a /inicio o renderizar directamente un index.html
    return redirect(url_for('inicio'))

@app.route('/inicio')
def inicio():
    # Renderiza una plantilla HTML llamada inicio.html
    return render_template('inicio.html')

# ---------------------------
# Registro de usuarios
# ---------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Procesar datos del formulario
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            # Si falta algún campo, podrías renderizar de nuevo la plantilla con un mensaje de error
            return render_template('register.html', error="Email y contraseña son requeridos")

        # Verificar si ya existe el usuario
        if User.query.filter_by(email=email).first():
            return render_template('register.html', error="El usuario ya existe")

        # Crear el usuario
        user = User(email=email, password=password)
        db.session.add(user)
        db.session.commit()

        # Redirigir a la página de login, por ejemplo
        return redirect(url_for('login'))

    # Si es GET, renderizamos el formulario de registro
    return render_template('register.html')

# ---------------------------
# Login de usuarios
# ---------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email, password=password).first()
        if not user:
            # Credenciales inválidas
            return render_template('login.html', error="Credenciales inválidas")

        # Guardar el id del usuario en la sesión
        session['user_id'] = user.id
        # Redirigir a inicio (o a donde prefieras)
        return redirect(url_for('inicio'))

    # Si es GET, renderizamos el formulario de login
    return render_template('login.html')

# ---------------------------
# Gestión de categorías
# ---------------------------
@app.route('/categorias', methods=['GET', 'POST'])
def categorias():
    if request.method == 'POST':
        # Procesar formulario para crear categoría
        nombre = request.form.get('nombre')
        if not nombre:
            # Manejar error si hace falta
            return render_template('categorias.html', error="El nombre es requerido", categories=Category.query.all())

        category = Category(nombre=nombre)
        db.session.add(category)
        db.session.commit()
        return redirect(url_for('categorias'))

    # Si es GET, mostramos la lista de categorías
    all_categories = Category.query.all()
    return render_template('categorias.html', categories=all_categories)

# ---------------------------
# Gestión de productos
# ---------------------------
@app.route('/productos', methods=['GET', 'POST'])
def productos():
    if request.method == 'POST':
        # Procesar formulario para crear producto
        nombre = request.form.get('nombre')
        descripcion = request.form.get('descripcion')
        precio = request.form.get('precio')
        stock = request.form.get('stock')
        category_id = request.form.get('category_id')

        if not all([nombre, descripcion, precio, stock, category_id]):
            return render_template('productos.html',
                                   error="Todos los campos son requeridos",
                                   products=Product.query.all(),
                                   categories=Category.query.all())

        try:
            precio = float(precio)
            stock = int(stock)
            category_id = int(category_id)
        except ValueError:
            return render_template('productos.html',
                                   error="precio debe ser numérico y stock/category_id deben ser enteros",
                                   products=Product.query.all(),
                                   categories=Category.query.all())

        # Si quieres subir imagen
        imagen = request.files.get('imagen')
        image_path = None
        if imagen:
            filename = imagen.filename
            # Podrías usar secure_filename si quieres evitar problemas de seguridad
            # from werkzeug.utils import secure_filename
            # filename = secure_filename(imagen.filename)
            upload_folder = os.path.join('static', 'imgs')
            os.makedirs(upload_folder, exist_ok=True)
            file_path = os.path.join(upload_folder, filename)
            imagen.save(file_path)
            image_path = os.path.join('static', 'imgs', filename)

        category = Category.query.get(category_id)
        if not category:
            return render_template('productos.html',
                                   error="Categoría no encontrada",
                                   products=Product.query.all(),
                                   categories=Category.query.all())

        product = Product(
            nombre=nombre,
            descripcion=descripcion,
            precio=precio,
            stock=stock,
            image_path=image_path,
            category_id=category_id
        )
        db.session.add(product)
        db.session.commit()
        return redirect(url_for('productos'))

    # Si es GET, listamos productos
    products = Product.query.all()
    categories = Category.query.all()
    return render_template('productos.html', products=products, categories=categories)

# ---------------------------
# Carrito de compra (en la sesión)
# ---------------------------
@app.route('/carrito', methods=['GET', 'POST'])
def carrito():
    if 'cart' not in session:
        session['cart'] = {}

    if request.method == 'POST':
        # Procesar formulario para agregar/eliminar producto del carrito
        product_id = request.form.get('product_id')
        quantity = request.form.get('quantity')

        if not product_id or not quantity:
            return redirect(url_for('carrito'))

        try:
            quantity = int(quantity)
        except ValueError:
            return redirect(url_for('carrito'))

        cart = session['cart']
        if quantity == 0:
            cart.pop(product_id, None)  # Eliminar si existe
        else:
            cart[product_id] = quantity
        session['cart'] = cart
        return redirect(url_for('carrito'))

    # Si es GET, mostramos el carrito
    cart = session['cart']
    # Convertir la info del carrito a objetos (para mostrar nombre, precio, etc.)
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
                'subtotal': subtotal
            })
            total += subtotal

    return render_template('carrito.html', cart_items=cart_items, total=total)

# ---------------------------
# Proceso de compra
# ---------------------------
@app.route('/compra', methods=['POST'])
def compra():
    if 'cart' not in session or not session['cart']:
        # Carrito vacío
        return redirect(url_for('carrito'))

    cart = session['cart']
    total = 0.0

    # Verificar disponibilidad y calcular total
    for prod_id, quantity in cart.items():
        product = Product.query.get(int(prod_id))
        if not product:
            # Producto no existe
            return redirect(url_for('carrito'))
        if product.stock < quantity:
            # Stock insuficiente
            return redirect(url_for('carrito'))
        total += product.precio * quantity

    # Si todo está correcto, se descuenta el stock
    for prod_id, quantity in cart.items():
        product = Product.query.get(int(prod_id))
        product.stock -= quantity

    db.session.commit()
    # Limpiar el carrito
    session['cart'] = {}

    # Renderizar una página de confirmación de compra
    return render_template('compra_exito.html', total=total)

if __name__ == '__main__':
    app.run(debug=True)
