import os
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
import requests

#Configurations
basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'cart.sqlite')
db = SQLAlchemy(app)

# Cart Model
class Cart(db.Model):
    #user_id
    userid = db.Column(db.Integer, nullable=False)
    #This will serve a product_id. So adding and removing becomes more easier.
    id = db.Column(db.Integer, primary_key=True)
    #Product name.
    name = db.Column(db.String(100), nullable=False)
    #This serves as the price * the quantity collected.
    totalprice = db.Column(db.REAL, nullable=False)
    #This how many objects the user requested to add to their cart.
    quantity = db.Column(db.Integer, nullable=False)
    #This is to show done.
    done = db.Column(db.Boolean, default=False)

# Endpoint 1: Get all in cart
@app.route('/cart/<int:user_id>', methods=['GET'])
def get_cart(user_id):
    #Query for everything in the cart.
    cart = Cart.query.filter(Cart.userid == user_id)
    #Puts in single object format.
    products_list = [{"id":products.id, "name": products.name, "price": products.totalprice, "quantity": products.quantity, "done" :products.done} for products in cart]
    #returns JSON.
    return jsonify({"Cart": products_list})

# Endpoint 2: Add product to cart
@app.route('/cart/<int:user_id>/add/<int:product_id>', methods=['POST'])
def add_product(user_id, product_id):
    #get quantity from request
    datajson = request.json
    if 'rquantity' not in datajson:
        return jsonify({"error": "You need to specify the quantity."}), 400
    
    quantity_data = datajson['rquantity']
    #get the product from ProductService
    response = requests.get(f'https://productservice-guh0.onrender.com/products/{product_id}')
    data = response.json()

    #Check if objects already exists in cart
    add_product_cart = Cart.query.get(product_id)
    #If it does exist add to the object and update
    if add_product_cart:
        #If there are no more to choose from; as in everything in selected.
        if (quantity_data > (data['quantity'] - add_product_cart.quantity)):
            return jsonify({"error": "No more product to add."}), 400
        #If there is more to select from then add to cart
        else:
            #Add the quantity and adjust the the totalprice
            add_product_cart.quantity = add_product_cart.quantity+quantity_data
            add_product_cart.totalprice = data['price']*add_product_cart.quantity
            #Update table
            db.session.commit()
            #Return JSON
            return jsonify({"message": "Product(s) added to rest of items", "product": {"userId":add_product_cart.userid,"id": add_product_cart.id,"name": add_product_cart.name, "price": add_product_cart.totalprice, "quantity": add_product_cart.quantity, "done" :add_product_cart.done}}), 201
    #If the product doesn't currently exist in the cart jusr add object to cart.
    else:
        #if request exceeds actual number that is in cart
        if (quantity_data <= data['quantity']):
            #Make cart object with the same id from product_id. Make continuity easier.
            add_product_cart = Cart(userid = user_id, id=data['id'], name=data['name'], totalprice=data['price']*quantity_data, quantity=quantity_data, done=data['done'])
            #Add to db
            db.session.add(add_product_cart)
            db.session.commit()
            #Return JSON
            return jsonify({"message": "Product(s) added to cart", "product": {"userId":add_product_cart.userid,"id": add_product_cart.id,"name": add_product_cart.name, "price": add_product_cart.totalprice, "quantity": add_product_cart.quantity, "done" :add_product_cart.done}}), 201
        else:
            return jsonify({"error": "Request Exceeds actual quantity of product."}), 400

# Endpoint 3: Delete something in the cart
@app.route('/cart/<int:user_id>/remove/<int:product_id>', methods=['DELETE'])
def remove_product(user_id, product_id):
    #get quantity from request
    datajson = request.json
    if "rquantity" not in datajson:
        return jsonify({"error": "You need to specify the quantity amount."}), 400
    
    quantity_data = datajson['rquantity']
    #get the product from ProductService
    response = requests.get(f'https://productservice-guh0.onrender.com/products/{product_id}')
    data = response.json()

    #Check if object is in the cart
    remove_product_cart = Cart.query.get(product_id)
    #If the object is in the cart
    if remove_product_cart:
        #If the quantity if greater than zero remove
        if ((remove_product_cart.quantity - quantity_data)>=1):
            #remove and adjust price
            remove_product_cart.quantity = remove_product_cart.quantity-quantity_data
            remove_product_cart.totalprice = data['price'] * remove_product_cart.quantity
            #Update db
            db.session.commit()
            #return JSON
            return jsonify({"message": "Product removed", "product left": {"userId":remove_product_cart.userid,"id": remove_product_cart.id,"name": remove_product_cart.name, "price": remove_product_cart.totalprice, "quantity": remove_product_cart.quantity, "done" :remove_product_cart.done}}), 201
        #If product is 0
        elif((remove_product_cart.quantity - quantity_data) == 0):
            #Delete prodoct from db
            msg = jsonify({"message": "Product fully removed from cart.", "product": {"userId":remove_product_cart.userid,"id": remove_product_cart.id,"name": remove_product_cart.name, "done" :remove_product_cart.done}}), 201
            db.session.delete(remove_product_cart)
            db.session.commit()
            return msg
        else:
            return jsonify({"error": "Your request to remove is greater than actual item"}), 400
    #If the object is not in the cart the return error
    else:
        #Return JSON
        return jsonify({"error": "Product does not exist in the cart."}), 404


if __name__ == '__main__':
    #db.create_all()
    #Runs on port 5001. Only userful for local host.
    app.run(debug=True, port = 5001)
