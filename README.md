
# Warehouse Management System (Flask + MongoDB)

## 📌 Overview
This repository presents a **web-based Warehouse Management System** built using **Flask** (Python web framework) and **MongoDB** (NoSQL database). The system is designed to streamline **product management, supplier/retailer workflows, order tracking, and payment handling** across multiple roles (Admin, Supplier, Retailer).

## 🎯 Project Goals
- Provide a **centralized warehouse management system**
- Allow **Admins** to oversee products, stock, and orders  
- Enable **Suppliers** to add/manage products and receive payments  
- Allow **Retailers** to browse products, manage carts, and place orders  
- Secure authentication system with **hashed passwords and role-based access**

## 🧠 Methodology
### Application Design
- Developed with **Flask** as the web framework  
- **MongoDB** used for persistent storage (users, products, orders, payments)  
- **Jinja2 Templates** for rendering HTML views  

### Features Implemented
- **Authentication & Authorization**
  - User registration and login (Admin, Supplier, Retailer roles)
  - Passwords stored securely with hashing
- **Admin Module**
  - Manage products, orders, and payments
  - Monitor stock levels
- **Supplier Module**
  - Add/manage supplied products
  - Track supplier orders and payments
- **Retailer Module**
  - Browse products, manage cart, and place orders
  - View order/payment history

## ⚙️ Tools and Technologies
- **Languages:** Python (Flask), HTML (Jinja templates)  
- **Database:** MongoDB (`pymongo`)  
- **Libraries:** Flask, Flask-Cors, Werkzeug, Jinja2, dnspython  
- **Environment:** Localhost / VSCode  

## 📊 Key Functionalities
| Role       | Capabilities                                  |
|------------|-----------------------------------------------|
| **Admin**  | Manage users, products, stock, orders, payments |
| **Supplier** | Add products, view supplier orders, payments   |
| **Retailer** | Browse products, cart, orders, payments        |

## 🧪 Results
- Fully functional **role-based Warehouse Management System**  
- Integrated **MongoDB backend** with secure session handling  
- Modular and extendable architecture for future enhancements  

## 👨‍💻 Team Members
- Sai Bhavani Prasad Potukuchi - 700754838  
