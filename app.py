from flask import Flask
from pymongo import MongoClient
from flask import Flask, request, jsonify
from pymongo import MongoClient
from werkzeug.security import generate_password_hash
from flask import Flask, request, render_template, redirect, url_for, session, jsonify
from werkzeug.security import check_password_hash
from bson import ObjectId  # Make sure to import ObjectId
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import request, session, redirect, url_for, flash
from datetime import datetime


import os



app = Flask(__name__)
app.secret_key = "crowdfunding" 
client = MongoClient("mongodb://localhost:27017/")  

db = client["The_Warehouse_Management"]
admin_collection=db["Admins"]
reatiler_collection=db["Retailer"]
supplier_collection=db["Suppliers"]
products_collection=db["products"]
orders_collection=db['Orders']
payments_collection=db['Payments']


@app.route('/register', methods=['GET', 'POST'])
def register_user():
    if request.method == 'POST':
        # Extract form data
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        company = request.form['company']
        address = request.form['address']
        zip_code = request.form['zip']
        role = request.form['role']
        
        # Hash the password
        hashed_password = generate_password_hash(password)
        
        # Create user data dictionary
        user_data = {
            "name": name,
            "email": email,
            "password": hashed_password,
            "company": company,
            "address": address,
            "zip": zip_code,
            'status':"verified",
            'cart':'[]'
        }

        # Check user role and insert into corresponding collection
        if role == 'retailer':
            # Insert into retailer collection
            reatiler_collection.insert_one(user_data)
            return redirect(url_for('login'))  # Redirect to login page or show a success message

        elif role == 'supplier':
            # Insert into supplier collection with 'verified' status
            supplier_collection.insert_one(user_data)
            return redirect(url_for('login'))  # Redirect to login page or show a success message

        else:
            return "Invalid role", 400  # Handle invalid role submission

    # If the request method is GET, render the registration page
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Extract form data
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        
        # Find user based on role
        user_data = None
        if role == 'admin':
            user_data = admin_collection.find_one({'email': email})
        elif role == 'retailer':
            user_data = reatiler_collection.find_one({'email': email})
        elif role == 'supplier':
            user_data = supplier_collection.find_one({'email': email})

        # Check if user exists and password matches
        if user_data and check_password_hash(user_data['password'], password):
            # Store user data in session
            session['email'] = user_data['email']
            session['name'] = user_data['name']
            session['role'] = role
            session['user_id'] = str(user_data['_id'])  # Store the user ID in session

            # Redirect based on the role
            if role == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif role == 'retailer':
                return redirect(url_for('retailer_dashboard'))
            elif role == 'supplier':
                return redirect(url_for('supplier_dashboard'))
        else:
            return "Invalid email or password", 400  # Handle incorrect credentials

    # If the request method is GET, render the login page
    return render_template('login.html')

# Admin dashboard
@app.route('/admin_dashboard')
def admin_dashboard():
    return render_template('admin_dashboard.html', name=session['name'])

# Retailer dashboard
@app.route('/retailer_dashboard')
def retailer_dashboard():
    # Ensure the user is logged in as retailer
    if 'role' not in session or session['role'] != 'retailer':
        return redirect(url_for('login'))
    return render_template('retailer_dashboard.html', name=session['name'])

@app.route('/supplier_dashboard')
def supplier_dashboard():
    return render_template('supplier_dashboard.html', name=session['name'])

@app.route('/create_product_supplier', methods=['GET', 'POST'])
def create_product_supplier():
    # Check if user is logged in
    if 'user_id' not in session:
        return redirect('/login')  # Redirect to login if not logged in

    if request.method == 'POST':
        product_name = request.form['product_name']
        description = request.form['description']
        product_type = request.form['product_type']
        price = request.form['price']
        quantity = request.form['quantity']

        # Get supplier details from session
        supplier_id = session.get('user_id')
        supplier_name = session.get('name')

        # Create product dictionary
        product = {
            'product_name': product_name,
            'description': description,
            'product_type': product_type,
            'price': price,
            'quantity': quantity,
            'distributor': 'supplier',  # Marking the distributor as 'supplier'
            'supplier_id': supplier_id,
            'supplier_name': supplier_name
        }

        # Insert product into the MongoDB collection
        products_collection.insert_one(product)

        return redirect('/supplier_dashboard')  # Redirect to supplier dashboard after creating the product

    return render_template('create_product_supplier.html')


@app.route('/admin_browse_products')
def admin_browse_products():
    # Retrieve all products where distributor is 'retailer'
    products = products_collection.find({"distributor": "supplier","quantity": {"$gt": 0}})
    
    # Prepare the products list to be sent to the template
    product_list = []
    for product in products:
        product_info = {
            "_id": product["_id"],
            "product_name": product["product_name"],
            "description": product["description"],
            "product_type": product["product_type"],
            "price": product["price"],
            "quantity": product["quantity"],
            "distributor": product["distributor"]
        }
        product_list.append(product_info)
    
    return render_template('admin_browse_products.html', products=product_list)



@app.route('/admin_add_cart', methods=['POST'])
def admin_add_cart():
    product_id = request.form.get('product_id')
    quantity = int(request.form.get('quantity')) 

    admin_email = session.get('email')
    admin = admin_collection.find_one({'email': admin_email})
    product = products_collection.find_one({'_id': ObjectId(product_id)})
    
    if not product:
        return "Product not found", 404  # Handle case where product is not found

    total_price = int(product['price']) * quantity

    # Create the product data to be added to the cart
    product_data = {
        'product_id': product['_id'],
        'product_name': product['product_name'],
        'quantity': quantity,
        'price': product['price'],
        'total_price': total_price  # Store the total price in the cart
    }

    # Check if the cart exists in the admin document, if not, initialize it as an empty list
    if 'cart' not in admin or not isinstance(admin['cart'], list):
        admin['cart'] = []

    # Check if the product is already in the cart
    product_in_cart = None
    for item in admin['cart']:
        if item['product_id'] == product['_id']:
            product_in_cart = item
            break

    if product_in_cart:
        # Update the quantity and total price for the existing product in the cart
        product_in_cart['quantity'] += quantity
        product_in_cart['total_price'] += total_price  # Add the new total price to the old one
    else:
        # If the product is not in the cart, append it as a new entry
        admin['cart'].append(product_data)

    # Update the admin document with the new cart
    admin_collection.update_one({'_id': admin['_id']}, {'$set': {'cart': admin['cart']}})

    return redirect(url_for('admin_browse_products'))

@app.route('/admin_view_cart', methods=['GET'])
def admin_view_cart():
    admin_email = session.get('email')
    
    # Get admin details from the collection
    admin = admin_collection.find_one({'email': admin_email})
    
    if not admin:
        return "Admin not found", 404  # Handle case where admin is not found

    # Check if the cart exists
    if 'cart' not in admin or not isinstance(admin['cart'], list) or len(admin['cart']) == 0:
        return render_template('admin_view_cart.html', cart=[], grand_total=0)

    # Fetch all product details for the products in the cart
    cart_items = admin['cart']
    detailed_cart_items = []
    grand_total = 0

    for item in cart_items:
        product = products_collection.find_one({'_id': ObjectId(item['product_id'])})
        
        if product:
            # Combine product details with the cart item details
            product_data = {
                'product_id': product['_id'],
                'product_name': product['product_name'],
                'quantity': item['quantity'],
                'price': product['price'],
                'total_price': item['total_price'],
                'description': product['description'],
                'product_type': product['product_type'],
            }

            detailed_cart_items.append(product_data)
            grand_total += item['total_price']

    return render_template('admin_view_cart.html', cart=detailed_cart_items, grand_total=grand_total,admin_email=admin_email)


@app.route('/admin_payment', methods=['GET','POST'])
def payment_page():
        # Get the base amount and email from the form
        mail = request.form.get('id')
        total_amount = float(request.form.get('total'))  # Convert to float for calculations
        
        # Calculate tax (8% of the total amount)
        tax = round(total_amount * 0.08, 2)
        
        # Calculate final amount
        final_amount = total_amount + tax
        
        # Send data to the HTML template
        return render_template(
            'admin_payment.html', 
            total_amount=total_amount, 
            tax=tax, 
            final_amount=final_amount, 
            mail=mail
        )


@app.route('/admin_process_payment', methods=['GET', 'POST'])
def admin_process_payment():

    cardholder_name = request.form.get('cardholder_name')
    card_number = request.form.get('card_number')
    cvv = request.form.get('cvv')
    expiry_date = request.form.get('expiry_date')
    email = request.form.get('mail')
    amount = float(request.form.get('amount'))
    admin = admin_collection.find_one({"email": email})
    cart_items = list(admin['cart'])
    current_datetime = datetime.now()
    date = current_datetime.strftime('%Y-%m-%d')
    time = current_datetime.strftime('%I:%M %p') 
    updated_cart_items = []
    for item in cart_items:
        product_id = item.get('product_id')
        product = products_collection.find_one({'_id': ObjectId(product_id)}) 
        
        if product:
            supplier_id = product.get('supplier_id') 

            updated_item = {
                **item, 
                "name": product.get('name'),
                "price": product.get('price'),
                "supplier_id": supplier_id, 
                "status": "ordered"
            }
            updated_cart_items.append(updated_item)

    order_data = {
        "user_email": email,
        "products": updated_cart_items, 
        "amount": amount,
        "status": "pending",
        "date": date,
        "time": time
    }
    order_id = orders_collection.insert_one(order_data).inserted_id

    payment_data = {
            "order_id": str(order_id),
            "user": cardholder_name,
            "email": email,
            "amount": amount,
            "card_number": card_number,
            "expiry_date": expiry_date,
            "cvv": cvv,
            "status": "completed",
            "date":date,
            "time":time
    }

    cart_items = list(admin['cart'])
    for item in cart_items:
        product_id = item['product_id']
        quantity_to_decrease = item['quantity']
        product = products_collection.find_one({"_id": ObjectId(product_id)})      
        if product:
                # Decrease the quantity by the amount in the cart
            new_quantity = int(product['quantity']) - int(quantity_to_decrease)
                
                # Ensure quantity doesn't go negative
            if new_quantity >= 0:
                products_collection.update_one(
                        {"_id": ObjectId(product_id)},
                        {"$set": {"quantity": new_quantity}}
                    )
            else:
                    return f"Not enough stock for {product['product_name']}"

    admin_collection.update_one({'email': email}, {'$set': {'cart': []}})
    payments_collection.insert_one(payment_data)
    return redirect(url_for('admin_dashboard'))

@app.route('/admin_view_orders', methods=['GET'])
def admin_view_orders():
    mail=session['email']
    orders = list(orders_collection.find({"user_email":mail}, {"products": 0}))  # Ignore `products` in query
    return render_template('admin_view_orders.html', orders=orders)

@app.route('/view_order_items/<order_id>', methods=['POST'])
def view_order_items(order_id):
    order = orders_collection.find_one({"_id": ObjectId(order_id)})
    products = order.get('products', [])
    return render_template('admin_view_order_items.html', products=products, order_id=order_id)


@app.route('/admin_payment_table', methods=['GET'])
def admin_payment_table():
    email = session.get('email')
    payments = payments_collection.find({"email": email})
    payments = list(payments)
    return render_template('admin_payment_table.html', payments=payments)



@app.route('/ret_payment_table', methods=['GET'])
def ret_payment_table():
    email = session.get('email')
    payments = payments_collection.find({"email": email})
    payments = list(payments)
    return render_template('retailer_payment_table.html', payments=payments)

@app.route('/admin_payment_table_rec', methods=['GET'])
def admin_payment_table_rec():
    email = session.get('email')
    payments = list(payments_collection.find({"email": {"$ne": "admin@gmail.com"}}))
    payments = list(payments)
    return render_template('admin_view_rec_payments.html', payments=payments)


@app.route('/sup_payment_table', methods=['GET'])
def sup_payment_table():
    payments = payments_collection.find({"email": "admin@gmail.com"})
    payments = list(payments)
    return render_template('supplier_view_payments.html', payments=payments)


@app.route('/supplier_view_orders', methods=['GET'])
def supplier_view_orders():
    supplier_id = session.get('user_id')
    all_products = []
    orders = list(orders_collection.find())
    for order in orders:
        for product in order['products']:
            if product['supplier_id'] == supplier_id:
                product_details = {
                    'order_id': order['_id'],
                    'product_id': product['product_id'],
                    'name': product['product_name'], 
                    'price': product['price'],
                    'quantity': product['quantity'],
                    'total_price': product['total_price'],
                    'status': product['status']
                }
                all_products.append(product_details)
    return render_template('supplier_orders.html', all_products=all_products)



@app.route('/update-product-status', methods=['POST'])
def update_product_status():
    order_id = request.form['order_id']
    product_id = request.form['product_id']
    status = request.form['status']
    total = request.form['status']
    units = request.form['quantity']
    order = orders_collection.find_one({'_id': ObjectId(order_id)})
    pro = products_collection.find_one({'_id': ObjectId(product_id)})
    name=pro['product_name']
    if order:
        for product in order['products']:
            if product['product_id'] == ObjectId(product_id):
                product['status'] = status
                if status == 'delivered':
                    product_details=products_collection.find_one({'product_name': name})
                    if product_details:
                        existing_product = products_collection.find_one({
                            'product_name': name,
                            'distributor': 'admin'
                        })
                        if existing_product:
                            quantity=int(existing_product['quantity'])+ int(units)

                            products_collection.update_one(
                                {'product_name': name, 'distributor': 'admin'},
                                {'$set': {'quantity': quantity}}
                            )
                        else  :
                            product_details['quantity'] = product['quantity']
                            product_details['supplier_name'] = 'admin'
                            product_details['distributor'] = 'admin'
                            product_details['supplier_id'] = ''
                            del product_details['_id']
                            products_collection.insert_one(product_details)
                break
        orders_collection.update_one({'_id': ObjectId(order_id)}, {'$set': {'products': order['products']}})
        flash('Product status updated successfully!')
    else:
        flash('Order not found!')

    return redirect(url_for('supplier_view_orders')) 

@app.route('/admin_view_stock')
def admin_view_stock():
    products = products_collection.find({"supplier_name": "admin"})
    products_list = list(products)
    return render_template('admin_view_stock.html', products=products_list)


@app.route('/update-price', methods=['POST'])
def update_price():
    product_id = request.form['update_price'] 
    new_price = request.form.get(f'new_price_{product_id}')
    if new_price:

        result = products_collection.update_one(
            {'_id': ObjectId(product_id)},  
            {'$set': {'price': float(new_price)}} 
        )
    return redirect(url_for('admin_view_stock')) 



@app.route('/retailer_browse_products')
def retailer_browse_products():
    products = products_collection.find({"supplier_name": "admin","quantity": {"$gt": 0}})
    
    product_list = []
    for product in products:
        product_info = {
            "_id": product["_id"],
            "product_name": product["product_name"],
            "description": product["description"],
            "product_type": product["product_type"],
            "price": product["price"],
            "quantity": product["quantity"],
            "distributor": product["distributor"]
        }
        product_list.append(product_info)
    
    return render_template('retailer_browse_products.html', products=product_list)


@app.route('/retailer_add_cart', methods=['POST'])
def retailer_add_cart():
    product_id = request.form.get('product_id')
    quantity = int(request.form.get('quantity')) 
    uid = session.get('user_id')
    retailer = reatiler_collection.find_one({'_id': ObjectId(uid)})
    product = products_collection.find_one({'_id': ObjectId(product_id)})
    
    if not product:
        return "Product not found", 404  # Handle case where product is not found

    total_price = int(product['price']) * quantity

    # Create the product data to be added to the cart
    product_data = {
        'product_id': product['_id'],
        'product_name': product['product_name'],
        'quantity': quantity,
        'price': product['price'],
        'total_price': total_price  # Store the total price in the cart
    }

    # Check if the cart exists in the admin document, if not, initialize it as an empty list
    if 'cart' not in retailer or not isinstance(retailer['cart'], list):
        retailer['cart'] = []

    # Check if the product is already in the cart
    product_in_cart = None
    for item in retailer['cart']:
        if item['product_id'] == product['_id']:
            product_in_cart = item
            break

    if product_in_cart:
        # Update the quantity and total price for the existing product in the cart
        product_in_cart['quantity'] += quantity
        product_in_cart['total_price'] += total_price  # Add the new total price to the old one
    else:
        # If the product is not in the cart, append it as a new entry
        retailer['cart'].append(product_data)

    # Update the admin document with the new cart
    reatiler_collection.update_one({'_id': ObjectId(uid)}, {'$set': {'cart': retailer['cart']}})

    return redirect(url_for('retailer_browse_products'))

@app.route('/retailer_view_cart', methods=['GET'])
def retailer_view_cart():
    uid = session.get('user_id')
    
    # Get admin details from the collection
    retailer = reatiler_collection.find_one({'_id': ObjectId(uid)})
    

    # Check if the cart exists
    if 'cart' not in retailer or not isinstance(retailer['cart'], list) or len(retailer['cart']) == 0:
        return render_template('retailer_view_cart.html', cart=[], grand_total=0)

    # Fetch all product details for the products in the cart
    cart_items = retailer['cart']
    detailed_cart_items = []
    grand_total = 0

    for item in cart_items:
        product = products_collection.find_one({'_id': ObjectId(item['product_id'])})
        
        if product:
            # Combine product details with the cart item details
            product_data = {
                'product_id': product['_id'],
                'product_name': product['product_name'],
                'quantity': item['quantity'],
                'price': product['price'],
                'total_price': item['total_price'],
                'description': product['description'],
                'product_type': product['product_type'],
            }

            detailed_cart_items.append(product_data)
            grand_total += item['total_price']

    return render_template('retailer_view_cart.html', cart=detailed_cart_items, grand_total=grand_total,uid=uid)



@app.route('/retailer_payment', methods=['GET','POST'])
def retailer_page():
        # Get the base amount and email from the form
        uid = request.form.get('id')
        total_amount = float(request.form.get('total'))  # Convert to float for calculations
        
        # Calculate tax (8% of the total amount)
        tax = round(total_amount * 0.08, 2)
        
        # Calculate final amount
        final_amount = total_amount + tax
        
        # Send data to the HTML template
        return render_template(
            'retailer_payment.html', 
            total_amount=total_amount, 
            tax=tax, 
            final_amount=final_amount, 
            uid=uid
        )


@app.route('/retailer_process_payment', methods=['GET', 'POST'])
def retailer_process_payment():
    cardholder_name = request.form.get('cardholder_name')
    card_number = request.form.get('card_number')
    cvv = request.form.get('cvv')
    expiry_date = request.form.get('expiry_date')
    uid = request.form.get('uid')
    amount = float(request.form.get('amount'))
    admin = reatiler_collection.find_one({"_id": ObjectId(uid)})
    email=admin['email']
    cart_items = list(admin['cart'])
    current_datetime = datetime.now()
    date = current_datetime.strftime('%Y-%m-%d')
    time = current_datetime.strftime('%I:%M %p') 
    updated_cart_items = []
    for item in cart_items:
        product_id = item.get('product_id')
        product = products_collection.find_one({'_id': ObjectId(product_id)}) 
        
        if product:
            supplier_name = product.get('supplier_name') 

            updated_item = {
                **item, 
                "name": product.get('name'),
                "price": product.get('price'),
                "supplier_id": supplier_name, 
                "status": "ordered"
            }
            updated_cart_items.append(updated_item)

    order_data = {
        "user_email": email,
        "products": updated_cart_items, 
        "amount": amount,
        "status": "pending",
        "date": date,
        "time": time
    }
    order_id = orders_collection.insert_one(order_data).inserted_id
    payment_data = {
            "order_id": str(order_id),
            "user": cardholder_name,
            "email": email,
            "amount": amount,
            "card_number": card_number,
            "expiry_date": expiry_date,
            "cvv": cvv,
            "status": "completed",
            "date":date,
            "time":time
    }
    cart_items = list(admin['cart'])
    for item in cart_items:
        product_id = item['product_id']
        quantity_to_decrease = item['quantity']
        product = products_collection.find_one({"_id": ObjectId(product_id)})      
        if product:
                # Decrease the quantity by the amount in the cart
            new_quantity = int(product['quantity']) - int(quantity_to_decrease)
                
                # Ensure quantity doesn't go negative
            if new_quantity >= 0:
                products_collection.update_one(
                        {"_id": ObjectId(product_id)},
                        {"$set": {"quantity": new_quantity}}
                    )
            else:
                    return f"Not enough stock for {product['product_name']}"

    reatiler_collection.update_one({'_id': ObjectId(uid)}, {'$set': {'cart': []}})
    payments_collection.insert_one(payment_data)
    return redirect(url_for('retailer_dashboard'))




@app.route('/retailer_view_orders', methods=['GET'])
def retailer_view_orders():
    mail=session['email']
    orders = list(orders_collection.find({"user_email":mail}, {"products": 0}))  # Ignore `products` in query
    return render_template('retailer_view_orders.html', orders=orders)

@app.route('/retailer_view_order_items/<order_id>', methods=['POST'])
def retailer_view_order_items(order_id):
    order = orders_collection.find_one({"_id": ObjectId(order_id)})
    products = order.get('products', [])
    return render_template('retailer_view_order_items.html', products=products, order_id=order_id)


@app.route('/retailer_payment_table', methods=['GET'])
def retailer_payment_table():
    email = session.get('email')
    payments = payments_collection.find({"email": email})
    payments = list(payments)
    return render_template('retailer_payment_table.html', payments=payments)



@app.route('/admin_view_sup_orders', methods=['GET'])
def admin_view_sup_orders():
    orders = list(orders_collection.find({"user_email": {"$ne": "admin@gmail.com"}}))
    print(orders)
    return render_template('admin_view_rec_orders.html', orders=orders)




@app.route('/admin_view_supp_orders/<order_id>', methods=['POST'])
def admin_view_supp_orders(order_id):
    oid=order_id
    all_products = []
    order = orders_collection.find_one({"_id":ObjectId(oid)})
    for product in order['products']:
        if product['supplier_id'] == 'admin':
            product_details = {
                'order_id': order['_id'],
                'product_id': product['product_id'],
                'name': product['product_name'], 
                'price': product['price'],
                'quantity': product['quantity'],
                'total_price': product['total_price'],
                'status': product['status']
                }
            all_products.append(product_details)

    return render_template('admin_orders.html', all_products=all_products)


@app.route('/admin-update-product-status', methods=['POST'])
def admin_update_product_status():
    order_id = request.form['order_id']
    product_id = request.form['product_id']
    status = request.form['status']

    order = orders_collection.find_one({'_id': ObjectId(order_id)})
    if order:
        for product in order['products']:
            if product['product_id'] == ObjectId(product_id):
                product['status'] = status
                break
        orders_collection.update_one({'_id': ObjectId(order_id)}, {'$set': {'products': order['products']}})
        flash('Product status updated successfully!')
    else:
        flash('Order not found!')

    return redirect(url_for('admin_view_sup_orders')) 


@app.route('/admin_delete_cart_item', methods=['POST'])
def admin_delete_cart_item():
    product_id = request.form.get('product_id')
    user = session['user_id']
    if user:
        # Find the user's cart in MongoDB and remove the product
        result = admin_collection.update_one(
            {"email": "admin@gmail.com"},  # Match the user by their ID
            {"$pull": {"cart": {"product_id": ObjectId(product_id)}}}  # Use $pull to remove the product from the cart
        )

    # Redirect back to the cart page
    return redirect(url_for('admin_view_cart'))



@app.route('/retailer_delete_cart_item', methods=['POST'])
def retailer_delete_cart_item():
    product_id = request.form.get('product_id')
    uid = session['user_id']
    user=reatiler_collection.find_one({"_id": ObjectId(uid)})
    if user:
        # Find the user's cart in MongoDB and remove the product
        result = reatiler_collection.update_one(
            {"_id": ObjectId(uid)},  # Match the user by their ID
            {"$pull": {"cart": {"product_id": ObjectId(product_id)}}}  # Use $pull to remove the product from the cart
        )

    # Redirect back to the cart page
    return redirect(url_for('retailer_view_cart'))
@app.route('/logout')
def logout():
    session.clear()


    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)


#flask --app app.py --debug run