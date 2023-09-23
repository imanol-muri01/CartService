import os
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
import requests
basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'cart.sqlite')
db = SQLAlchemy(app)

# Cart Model
class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    totalprice = db.Column(db.REAL, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    done = db.Column(db.Boolean, default=False)

# Endpoint 1: Get all in cart
@app.route('/cart/<int:user_id>', methods=['GET'])
def get_cart(user_id):
    cart = Cart.query.all()
    products_list = [{"name": products.name, "price": products.totalprice, "quantity": products.quantity, "done" :products.done} for products in cart]
    return jsonify({"cart": products_list})

# Endpoint 2: Add product to cart
@app.route('/cart/<int:user_id>/add/<int:product_id>', methods=['POST'])
def add_product(user_id, product_id):
    #get the product
    response = requests.get(f'http://127.0.0.1:5000/products/{product_id}')
    data = response.json()

    ##check it needs to be updated
    add_product_cart = Cart.query.get(product_id)
    if add_product_cart:
        if (add_product_cart.quantity == data['quantity']):
            return jsonify({"error": "No more product."}), 404
        else:
            add_product_cart.quantity = add_product_cart.quantity+1
            add_product_cart.totalprice = add_product_cart.totalprice+data['price']
            db.session.commit()
            return jsonify({"message": "Product added", "product": {"id": add_product_cart.id,"name": add_product_cart.name, "price": add_product_cart.totalprice, "quantity": add_product_cart.quantity, "done" :add_product_cart.done}}), 201
    else:
        add_product_cart = Cart(id=data['id'], name=data['name'], totalprice=data['price'], quantity=1, done=data['done'])
        db.session.add(add_product_cart)
        db.session.commit()
        return jsonify({"message": "Product added", "product": {"id": add_product_cart.id,"name": add_product_cart.name, "price": add_product_cart.totalprice, "quantity": add_product_cart.quantity, "done" :add_product_cart.done}}), 201



# Endpoint 3: Delete something in the cart
@app.route('/cart/<int:user_id>/remove/<int:product_id>', methods=['DELETE'])
def remove_product(user_id, product_id):

    ##check it needs to be updated
    add_product_cart = Cart.query.get(product_id)
    if add_product_cart:
        if add_product_cart.quantity > 0:
            add_product_cart.totalprice = add_product_cart.totalprice-(add_product_cart.totalprice/add_product_cart.quantity)
            add_product_cart.quantity = add_product_cart.quantity-1
            db.session.commit()
            return jsonify({"message": "Product added", "product": {"id": add_product_cart.id,"name": add_product_cart.name, "price": add_product_cart.totalprice, "quantity": add_product_cart.quantity, "done" :add_product_cart.done}}), 201
        else:
            db.session.delete(product_id)
            db.session.commit()
    else:
        return jsonify({"error": "Product does not exist."}), 404


if __name__ == '__main__':
    db.create_all()
    app.run(debug=True, port = 5001)