from datetime import datetime
from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(128), nullable=False, default='')
    role = db.Column(db.String(20), nullable=False, default='staff')  # admin / staff
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active_user = db.Column(db.Boolean, default=True)

    invoices = db.relationship('Invoice', backref='created_by', lazy='dynamic')
    stock_logs = db.relationship('StockLog', backref='performed_by', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role == 'admin'

    def __repr__(self):
        return f'<User {self.username}>'


class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(100), default='')
    description = db.Column(db.Text, default='')
    unit = db.Column(db.String(30), default='Cái')
    price = db.Column(db.Float, nullable=False, default=0)   # Giá bán
    cost = db.Column(db.Float, nullable=False, default=0)    # Giá nhập
    quantity = db.Column(db.Integer, default=0)              # Tồn kho
    min_stock = db.Column(db.Integer, default=5)             # Mức tối thiểu
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    invoice_items = db.relationship('InvoiceItem', backref='product', lazy='dynamic')
    stock_logs = db.relationship('StockLog', backref='product', lazy='dynamic')

    @property
    def stock_status(self):
        if self.quantity == 0:
            return 'out'
        elif self.quantity <= self.min_stock:
            return 'low'
        return 'ok'

    @property
    def stock_badge(self):
        status = self.stock_status
        if status == 'out':
            return ('Hết hàng', 'danger')
        elif status == 'low':
            return ('Sắp hết', 'warning')
        return ('Còn hàng', 'success')

    def __repr__(self):
        return f'<Product {self.code}: {self.name}>'


class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    phone = db.Column(db.String(20), default='')
    email = db.Column(db.String(120), default='')
    address = db.Column(db.Text, default='')
    note = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    invoices = db.relationship('Invoice', backref='customer', lazy='dynamic')

    @property
    def total_spent(self):
        return sum(inv.total for inv in self.invoices if inv.status == 'paid')

    def __repr__(self):
        return f'<Customer {self.name}>'


class Invoice(db.Model):
    __tablename__ = 'invoices'
    id = db.Column(db.Integer, primary_key=True)
    invoice_no = db.Column(db.String(50), unique=True, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    total = db.Column(db.Float, default=0)
    discount = db.Column(db.Float, default=0)
    status = db.Column(db.String(20), default='paid')  # paid / cancelled
    note = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    items = db.relationship('InvoiceItem', backref='invoice', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Invoice {self.invoice_no}>'


class InvoiceItem(db.Model):
    __tablename__ = 'invoice_items'
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Float, nullable=False, default=0)
    subtotal = db.Column(db.Float, nullable=False, default=0)

    def __repr__(self):
        return f'<InvoiceItem invoice={self.invoice_id} product={self.product_id}>'


class StockLog(db.Model):
    __tablename__ = 'stock_logs'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    type = db.Column(db.String(10), nullable=False)   # 'in' / 'out'
    quantity = db.Column(db.Integer, nullable=False)
    before_qty = db.Column(db.Integer, default=0)
    after_qty = db.Column(db.Integer, default=0)
    note = db.Column(db.String(255), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<StockLog {self.type} {self.quantity} for product {self.product_id}>'
