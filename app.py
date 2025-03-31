from flask import Flask, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)

# Configuración de la base de datos y subida de archivos
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///store.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'imgs')
app.secret_key = 'supersecretkey'

db = SQLAlchemy(app)

# Asegurarse de que el directorio de imágenes exista
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

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

# Crear las tablas antes del primer request
@app.before_first_request
def create_tables():
    db.create_all()

# Endpoints básicos
@app.route('/')
def goto_inicio():
    return jsonify({"message": "Bienvenido a Chuches PSD"}), 200

@app.route('/inicio')
def inicio():
    return jsonify({"message": "Chuches PSD"}), 200

# Registro de usuario
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        return jsonify({"error": "Email y contraseña son requeridos"}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "El usuario ya existe"}), 400
    user = User(email=email, password=password)
    db.session.add(user)
    db.session.commit()
    return jsonify({"message": "Usuario registrado exitosamente"}), 201

# Login de usuario
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    user = User.query.filter_by(email=email, password=password).first()
    if not user:
        return jsonify({"error": "Usuario inválido"}), 401
    # Se guarda el id del usuario en la sesión (aunque no se implementa autenticación avanzada)
    session['user_id'] = user.id
    return jsonify({"message": "Inicio de sesión exitoso"}), 200

# Gestión de categorías
@app.route('/categorias', methods=['GET', 'POST'])
def categorias():
    if request.method == 'GET':
        categories = Category.query.all()
        result = [{"id": cat.id, "nombre": cat.nombre} for cat in categories]
        return jsonify(result), 200
    elif request.method == 'POST':
        data = request.get_json()
        nombre = data.get('nombre')
        if not nombre:
            return jsonify({"error": "Introduce el nombre de la categoría"}), 400
        category = Category(nombre=nombre)
        db.session.add(category)
        db.session.commit()
        return jsonify({"id": category.id, "nombre": category.nombre}), 201

# Gestión de productos
@app.route('/productos', methods=['GET', 'POST'])
def productos():
    if request.method == 'GET':
        # Se puede filtrar por category_id pasando ?category_id=valor
        category_id = request.args.get('category_id')
        if category_id:
            products = Product.query.filter_by(category_id=category_id).all()
        else:
            products = Product.query.all()
        result = []
        for p in products:
            result.append({
                "id": p.id,
                "nombre": p.nombre,
                "descripcion": p.descripcion,
                "precio": p.precio,
                "stock": p.stock,
                "image_path": p.image_path,
                "category": {"id": p.category.id, "nombre": p.category.nombre}
            })
        return jsonify(result), 200

    elif request.method == 'POST':
        # Se espera que el request sea form-data, para poder incluir el archivo de imagen
        nombre = request.form.get('nombre')
        descripcion = request.form.get('descripcion')
        precio = request.form.get('precio')
        stock = request.form.get('stock')
        category_id = request.form.get('category_id')

        if not all([nombre, descripcion, precio, stock, category_id]):
            return jsonify({"error": "Todos los campos (nombre, descripcion, precio, stock, category_id) son requeridos"}), 400

        try:
            precio = float(precio)
            stock = int(stock)
            category_id = int(category_id)
        except ValueError:
            return jsonify({"error": "precio debe ser numérico y stock/category_id deben ser enteros"}), 400

        # Manejo del archivo de imagen
        imagen = request.files.get('imagen')
        image_path = None
        if imagen:
            filename = secure_filename(imagen.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            imagen.save(file_path)
            # Guardamos la ruta relativa
            image_path = os.path.join('static', 'imgs', filename)

        # Verificar que la categoría exista
        category = Category.query.get(category_id)
        if not category:
            return jsonify({"error": "Categoría no encontrada"}), 404

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
        return jsonify({
            "id": product.id,
            "nombre": product.nombre,
            "descripcion": product.descripcion,
            "precio": product.precio,
            "stock": product.stock,
            "image_path": product.image_path,
            "category": {"id": category.id, "nombre": category.nombre}
        }), 201

# Carrito de compra (almacenado en la sesión)
@app.route('/carrito', methods=['GET', 'POST', 'PUT'])
def carrito():
    # Inicializar carrito si no existe
    if 'cart' not in session:
        session['cart'] = {}

    cart = session['cart']

    if request.method == 'GET':
        return jsonify(cart), 200

    elif request.method in ['POST', 'PUT']:
        data = request.get_json()
        product_id = data.get('product_id')
        quantity = data.get('quantity')

        if product_id is None or quantity is None:
            return jsonify({"error": "product_id y quantity son requeridos"}), 400

        try:
            quantity = int(quantity)
        except ValueError:
            return jsonify({"error": "quantity debe ser un entero"}), 400

        # Convertir product_id a string para usarlo como key
        product_key = str(product_id)
        if quantity == 0:
            # Eliminar el producto del carrito
            if product_key in cart:
                del cart[product_key]
        else:
            cart[product_key] = quantity
        session['cart'] = cart
        return jsonify(cart), 200

# Proceso de compra
@app.route('/compra', methods=['POST'])
def compra():
    if 'cart' not in session or not session['cart']:
        return jsonify({"error": "El carrito está vacío"}), 400

    cart = session['cart']
    total = 0.0

    # Verificar disponibilidad y calcular total
    for prod_id, quantity in cart.items():
        product = Product.query.get(int(prod_id))
        if not product:
            return jsonify({"error": f"Producto con id {prod_id} no encontrado"}), 404
        if product.stock < quantity:
            return jsonify({"error": f"Stock insuficiente para el producto {product.nombre}"}), 400
        total += product.precio * quantity

    # Si todo está correcto, se deduce el stock y se confirma la compra
    for prod_id, quantity in cart.items():
        product = Product.query.get(int(prod_id))
        product.stock -= quantity

    db.session.commit()
    # Limpiar el carrito
    session['cart'] = {}
    return jsonify({"message": "Compra realizada con éxito", "total": total}), 200

if __name__ == '__main__':
    app.run(debug=True)
