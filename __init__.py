from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Vui lòng đăng nhập để tiếp tục.'
login_manager.login_message_category = 'warning'

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)

    from app.auth import auth as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.dashboard import dashboard as dashboard_bp
    app.register_blueprint(dashboard_bp)

    from app.products import products as products_bp
    app.register_blueprint(products_bp, url_prefix='/products')

    from app.warehouse import warehouse as warehouse_bp
    app.register_blueprint(warehouse_bp, url_prefix='/warehouse')

    from app.customers import customers as customers_bp
    app.register_blueprint(customers_bp, url_prefix='/customers')

    from app.reports import reports as reports_bp
    app.register_blueprint(reports_bp, url_prefix='/reports')

    from app.ai import ai as ai_bp
    app.register_blueprint(ai_bp, url_prefix='/ai')

    with app.app_context():
        db.create_all()
        _seed_data()

    return app

def _seed_data():
    from app.models import User, Product, Customer
    from werkzeug.security import generate_password_hash

    if User.query.count() == 0:
        admin = User(
            username='admin',
            email='admin@kho.com',
            password_hash=generate_password_hash('admin123'),
            role='admin',
            full_name='Quản trị viên'
        )
        staff = User(
            username='nhanvien',
            email='nhanvien@kho.com',
            password_hash=generate_password_hash('123456'),
            role='staff',
            full_name='Nhân Viên'
        )
        db.session.add_all([admin, staff])

    if Product.query.count() == 0:
        products = [
            Product(code='SP001', name='Laptop Dell XPS 15', category='Điện tử', price=25000000, cost=20000000, quantity=15, min_stock=5, unit='Cái'),
            Product(code='SP002', name='Chuột Logitech MX Master', category='Phụ kiện', price=1800000, cost=1200000, quantity=8, min_stock=10, unit='Cái'),
            Product(code='SP003', name='Bàn phím cơ Keychron K2', category='Phụ kiện', price=2200000, cost=1600000, quantity=12, min_stock=5, unit='Cái'),
            Product(code='SP004', name='Màn hình LG 27" 4K', category='Điện tử', price=12000000, cost=9000000, quantity=3, min_stock=5, unit='Cái'),
            Product(code='SP005', name='Tai nghe Sony WH-1000XM5', category='Âm thanh', price=8500000, cost=6500000, quantity=20, min_stock=5, unit='Cái'),
            Product(code='SP006', name='Ổ cứng SSD Samsung 1TB', category='Lưu trữ', price=2800000, cost=2000000, quantity=4, min_stock=10, unit='Cái'),
            Product(code='SP007', name='RAM Kingston 16GB DDR4', category='Linh kiện', price=1200000, cost=900000, quantity=25, min_stock=10, unit='Thanh'),
            Product(code='SP008', name='Webcam Logitech C920', category='Phụ kiện', price=1500000, cost=1100000, quantity=2, min_stock=5, unit='Cái'),
        ]
        db.session.add_all(products)

    if Customer.query.count() == 0:
        customers = [
            Customer(name='Nguyễn Văn An', phone='0901234567', email='an@gmail.com', address='123 Nguyễn Huệ, TP.HCM'),
            Customer(name='Trần Thị Bình', phone='0912345678', email='binh@gmail.com', address='456 Lê Lợi, Hà Nội'),
            Customer(name='Lê Văn Cường', phone='0923456789', email='cuong@gmail.com', address='789 Trần Phú, Đà Nẵng'),
        ]
        db.session.add_all(customers)

    db.session.commit()
