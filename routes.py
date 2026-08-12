from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.customers import customers
from app.models import Customer, Invoice
from app import db

@customers.route('/')
@login_required
def index():
    search = request.args.get('search', '').strip()
    page = request.args.get('page', 1, type=int)
    
    query = Customer.query
    if search:
        query = query.filter(
            db.or_(
                Customer.name.ilike(f'%{search}%'),
                Customer.phone.ilike(f'%{search}%'),
                Customer.email.ilike(f'%{search}%')
            )
        )
    
    customers_list = query.order_by(Customer.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    return render_template('customers/list.html', customers=customers_list, search=search)

@customers.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        address = request.form.get('address', '').strip()
        note = request.form.get('note', '').strip()

        if not name:
            flash('Tên khách hàng là bắt buộc!', 'danger')
        else:
            customer = Customer(name=name, phone=phone, email=email, address=address, note=note)
            db.session.add(customer)
            db.session.commit()
            flash(f'Đã thêm khách hàng "{name}" thành công!', 'success')
            return redirect(url_for('customers.index'))

    return render_template('customers/add.html')

@customers.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    customer = Customer.query.get_or_404(id)
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if not name:
            flash('Tên khách hàng là bắt buộc!', 'danger')
        else:
            customer.name = name
            customer.phone = request.form.get('phone', '').strip()
            customer.email = request.form.get('email', '').strip()
            customer.address = request.form.get('address', '').strip()
            customer.note = request.form.get('note', '').strip()
            db.session.commit()
            flash('Cập nhật thông tin khách hàng thành công!', 'success')
            return redirect(url_for('customers.index'))
    return render_template('customers/edit.html', customer=customer)

@customers.route('/view/<int:id>')
@login_required
def view(id):
    customer = Customer.query.get_or_404(id)
    invoices = Invoice.query.filter_by(customer_id=id).order_by(Invoice.created_at.desc()).all()
    return render_template('customers/view.html', customer=customer, invoices=invoices)

@customers.route('/api/list')
@login_required
def api_list():
    customers_list = Customer.query.order_by(Customer.name).all()
    return jsonify([{'id': c.id, 'name': c.name, 'phone': c.phone} for c in customers_list])
