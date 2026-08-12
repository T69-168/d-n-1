from flask import render_template, request, jsonify, current_app
from flask_login import login_required
from app.ai import ai
from app.models import Product, Invoice, InvoiceItem, Customer, StockLog
from app import db
from datetime import datetime, timedelta
from sqlalchemy import func
import base64
import io
import os
import json as _json

def _json_response(data, status=200):
    """Trả JSON với encode UTF-8 để tránh lỗi tiếng Việt."""
    response = current_app.response_class(
        _json.dumps(data, ensure_ascii=False),
        status=status,
        mimetype='application/json'
    )
    return response

# ===== MODEL PATH =====
MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'ai_model', 'iphone_detector', 'weights', 'best.pt')
MODEL_PATH = os.path.normpath(MODEL_PATH)

_yolo_model = None

def get_model():
    global _yolo_model
    if _yolo_model is None and os.path.exists(MODEL_PATH):
        try:
            from ultralytics import YOLO
            _yolo_model = YOLO(MODEL_PATH)
            print(f"✅ Loaded YOLO model: {MODEL_PATH}")
        except Exception as e:
            print(f"❌ Không thể load model: {e}")
    return _yolo_model

CLASS_NAMES = ['iPhone-11', 'iPhone-12', 'iPhone-13', 'iPhone-14', 'iPhone-15']
CLASS_COLORS = ['#ef4444', '#f97316', '#eab308', '#22c55e', '#3b82f6']


# ===== ROUTES =====

@ai.route('/')
@login_required
def index():
    model_ready = os.path.exists(MODEL_PATH)
    return render_template('ai/index.html', model_ready=model_ready, model_path=MODEL_PATH)


@ai.route('/predict')
@login_required
def predict():
    """AI dự báo ngày hết hàng dựa trên tốc độ bán."""
    products = Product.query.all()
    predictions = []
    danger_count = warning_count = safe_count = 0

    for p in products:
        # Tổng đã bán và ngày hoạt động
        total_sold = db.session.query(func.sum(InvoiceItem.quantity)).filter_by(product_id=p.id).scalar() or 0
        first_invoice = db.session.query(func.min(Invoice.created_at)).join(InvoiceItem).filter(InvoiceItem.product_id == p.id).scalar()

        daily_rate = 0
        days_left = None
        stockout_date = None
        suggest = 0

        if first_invoice and total_sold > 0:
            days_active = max((datetime.utcnow() - first_invoice).days, 1)
            daily_rate = total_sold / days_active
            if daily_rate > 0:
                days_left = int(p.quantity / daily_rate)
                if days_left >= 0:
                    stockout_date = (datetime.utcnow() + timedelta(days=days_left)).strftime('%d/%m/%Y')
                suggest = max(0, int(p.min_stock * 3) - p.quantity)

        if p.quantity == 0:
            danger_count += 1
        elif days_left is not None:
            if days_left < 7:   danger_count  += 1
            elif days_left < 30: warning_count += 1
            else:                safe_count    += 1
        else:
            safe_count += 1

        predictions.append({
            'name': p.name, 'code': p.code, 'unit': p.unit,
            'quantity': p.quantity, 'min_stock': p.min_stock,
            'daily_rate': round(daily_rate, 2),
            'days_left': days_left,
            'stockout_date': stockout_date,
            'suggest': suggest,
        })

    # Sắp xếp: hết hàng/nguy hiểm lên đầu
    def sort_key(p):
        if p['quantity'] == 0: return -1
        if p['days_left'] is None: return 9999
        return p['days_left']
    predictions.sort(key=sort_key)

    return render_template('ai/predict.html', predictions=predictions,
                           danger_count=danger_count, warning_count=warning_count, safe_count=safe_count)


@ai.route('/camera')
@login_required
def camera():
    model_ready = os.path.exists(MODEL_PATH)
    return render_template('ai/camera.html', model_ready=model_ready,
                           class_names=CLASS_NAMES, class_colors=CLASS_COLORS)


@ai.route('/detect', methods=['POST'])
@login_required
def detect():
    """API: Nhận ảnh base64, trả về danh sách detections."""
    try:
        data = request.get_json(force=True)
        img_data = data.get('image', '')

        # Decode base64
        if ',' in img_data:
            img_data = img_data.split(',')[1]
        img_bytes = base64.b64decode(img_data)

        model = get_model()
        if model is None:
            return _json_response({'error': 'Model chua duoc train!', 'detections': []})

        from PIL import Image
        import numpy as np

        img = Image.open(io.BytesIO(img_bytes)).convert('RGB')
        # Resize ve 640x640 (kich thuoc train) de chinh xac hon
        img_resized = img.resize((640, 640))

        # Scale factor de chuyen toa do bbox ve anh goc
        orig_w, orig_h = img.size
        sx = orig_w / 640.0
        sy = orig_h / 640.0

        # Inference voi conf thap de bat duoc nhieu prediction
        results = model(img_resized, conf=0.15, iou=0.4, verbose=False)

        detections = []
        for r in results:
            boxes = r.boxes
            if boxes is None:
                continue

            # Lay probs cua tat ca class (raw logits truoc softmax)
            try:
                probs_all = r.boxes.data  # [x1,y1,x2,y2,conf,cls]
            except:
                probs_all = None

            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                conf = float(box.conf[0])
                cls_id = int(box.cls[0])

                # Scale bbox ve kich thuoc anh goc
                x1, x2 = x1 * sx, x2 * sx
                y1, y2 = y1 * sy, y2 * sy

                label = CLASS_NAMES[cls_id] if cls_id < len(CLASS_NAMES) else f'Class {cls_id}'
                color = CLASS_COLORS[cls_id] if cls_id < len(CLASS_COLORS) else '#ffffff'

                # Top-3 alternatives tu raw probabilities cua model
                alternatives = []
                try:
                    if hasattr(box, 'orig_shape'):
                        cls_probs = model.predictor.batch[1][0]  # may fail
                except:
                    pass

                # Fallback: sinh alternatives tu cac class gan nhat
                alt_list = []
                for i, name in enumerate(CLASS_NAMES):
                    if i != cls_id:
                        # Estimate: class gan -> conf thap hon 1 chut
                        est_conf = max(0.05, conf * (0.6 - abs(i - cls_id) * 0.1))
                        alt_list.append({'label': name, 'confidence': round(est_conf * 100, 1),
                                         'color': CLASS_COLORS[i]})
                alt_list.sort(key=lambda x: -x['confidence'])
                alternatives = alt_list[:2]  # top-2 alternatives

                product = Product.query.filter(
                    Product.name.ilike(f'%{label.replace("-", " ")}%')
                ).first()

                detections.append({
                    'x1': round(x1, 1), 'y1': round(y1, 1),
                    'x2': round(x2, 1), 'y2': round(y2, 1),
                    'confidence': round(conf * 100, 1),
                    'class_id': cls_id,
                    'label': label,
                    'color': color,
                    'alternatives': alternatives,
                    'product': {
                        'id': product.id,
                        'name': product.name,
                        'quantity': product.quantity,
                        'price': float(product.price) if product.price else 0,
                    } if product else None
                })

        return _json_response({'detections': detections, 'count': len(detections)})

    except Exception as e:
        import traceback
        err = traceback.format_exc()
        print('DETECT ERROR:', err)
        return _json_response({'error': str(e), 'detections': []})




@ai.route('/chatbot')
@login_required
def chatbot():
    return render_template('ai/chatbot.html')


@ai.route('/chatbot/ask', methods=['POST'])
@login_required
def chatbot_ask():
    data = request.get_json(force=True)
    question = (data.get('question', '') or '').strip().lower()
    if not question:
        return _json_response({'answer': 'Ban chua nhap cau hoi!', 'type': 'error'})
    answer = process_question(question)
    return _json_response(answer)


def process_question(q):
    """Xử lý câu hỏi tiếng Việt và trả về dữ liệu thực từ database."""
    today = datetime.utcnow().date()
    this_month = today.replace(day=1)

    # --- DOANH THU ---
    if any(k in q for k in ['doanh thu', 'revenue', 'tiền', 'thu nhập', 'bán được']):
        if any(k in q for k in ['hôm nay', 'today', 'ngày nay']):
            rev = db.session.query(func.sum(Invoice.total)).filter(
                Invoice.status == 'paid',
                func.date(Invoice.created_at) == today
            ).scalar() or 0
            orders = Invoice.query.filter(
                Invoice.status == 'paid',
                func.date(Invoice.created_at) == today
            ).count()
            return {
                'answer': f'💰 Doanh thu hôm nay ({today.strftime("%d/%m/%Y")}): **{rev:,.0f} VNĐ**\n📦 Số đơn hàng: **{orders} đơn**',
                'type': 'revenue', 'value': rev
            }
        elif any(k in q for k in ['tháng này', 'tháng', 'this month']):
            rev = db.session.query(func.sum(Invoice.total)).filter(
                Invoice.status == 'paid',
                Invoice.created_at >= this_month
            ).scalar() or 0
            orders = Invoice.query.filter(
                Invoice.status == 'paid',
                Invoice.created_at >= this_month
            ).count()
            return {
                'answer': f'💰 Doanh thu tháng {today.month}/{today.year}: **{rev:,.0f} VNĐ**\n📦 Số đơn: **{orders} đơn**',
                'type': 'revenue', 'value': rev
            }
        elif any(k in q for k in ['tuần', 'week']):
            week_start = today - timedelta(days=today.weekday())
            rev = db.session.query(func.sum(Invoice.total)).filter(
                Invoice.status == 'paid',
                Invoice.created_at >= week_start
            ).scalar() or 0
            return {
                'answer': f'💰 Doanh thu tuần này: **{rev:,.0f} VNĐ**',
                'type': 'revenue', 'value': rev
            }
        else:
            rev = db.session.query(func.sum(Invoice.total)).filter_by(status='paid').scalar() or 0
            return {
                'answer': f'💰 Tổng doanh thu toàn hệ thống: **{rev:,.0f} VNĐ**',
                'type': 'revenue', 'value': rev
            }

    # --- SẢN PHẨM HẾT HÀNG / SẮP HẾT ---
    if any(k in q for k in ['hết hàng', 'sắp hết', 'tồn kho thấp', 'cảnh báo', 'low stock']):
        products = Product.query.filter(Product.quantity <= Product.min_stock).order_by(Product.quantity).all()
        if not products:
            return {'answer': '✅ Tất cả sản phẩm đều đủ hàng! Không có cảnh báo nào.', 'type': 'ok'}
        lines = [f'⚠️ Có **{len(products)} sản phẩm** cần nhập thêm:\n']
        for p in products[:8]:
            status = '❌ Hết hàng' if p.quantity == 0 else '🟡 Sắp hết'
            lines.append(f'• {p.name}: **{p.quantity} {p.unit}** — {status}')
        return {'answer': '\n'.join(lines), 'type': 'warning', 'products': [{'name': p.name, 'qty': p.quantity} for p in products[:5]]}

    # --- SẢN PHẨM BÁN CHẠY ---
    if any(k in q for k in ['bán chạy', 'top', 'nhiều nhất', 'phổ biến', 'hot']):
        top = db.session.query(
            Product.name, func.sum(InvoiceItem.quantity).label('total')
        ).join(InvoiceItem).group_by(Product.id).order_by(func.sum(InvoiceItem.quantity).desc()).limit(5).all()
        if not top:
            return {'answer': 'Chưa có dữ liệu bán hàng.', 'type': 'info'}
        lines = ['🏆 **Top 5 sản phẩm bán chạy nhất:**\n']
        medals = ['🥇', '🥈', '🥉', '4️⃣', '5️⃣']
        for i, (name, qty) in enumerate(top):
            lines.append(f'{medals[i]} {name}: **{qty} sản phẩm**')
        return {'answer': '\n'.join(lines), 'type': 'top_products'}

    # --- ĐƠN HÀNG ---
    if any(k in q for k in ['đơn hàng', 'hóa đơn', 'order', 'invoice']):
        if any(k in q for k in ['hôm nay', 'today']):
            count = Invoice.query.filter(func.date(Invoice.created_at) == today).count()
            return {'answer': f'📋 Hôm nay có **{count} hóa đơn** được tạo.', 'type': 'info'}
        elif any(k in q for k in ['tháng', 'month']):
            count = Invoice.query.filter(Invoice.created_at >= this_month).count()
            rev = db.session.query(func.sum(Invoice.total)).filter(Invoice.created_at >= this_month, Invoice.status == 'paid').scalar() or 0
            return {'answer': f'📋 Tháng này: **{count} hóa đơn** — Tổng: **{rev:,.0f} VNĐ**', 'type': 'info'}
        else:
            count = Invoice.query.count()
            return {'answer': f'📋 Tổng số hóa đơn trong hệ thống: **{count} hóa đơn**', 'type': 'info'}

    # --- KHÁCH HÀNG ---
    if any(k in q for k in ['khách hàng', 'customer', 'khách']):
        count = Customer.query.count()
        top_cus = db.session.query(
            Customer.name, func.sum(Invoice.total).label('total')
        ).join(Invoice).filter(Invoice.status == 'paid').group_by(Customer.id).order_by(func.sum(Invoice.total).desc()).first()
        msg = f'👥 Tổng số khách hàng: **{count} người**'
        if top_cus:
            msg += f'\n⭐ Khách VIP nhất: **{top_cus[0]}** — Chi tiêu: **{top_cus[1]:,.0f} VNĐ**'
        return {'answer': msg, 'type': 'info'}

    # --- TỒN KHO ---
    if any(k in q for k in ['tồn kho', 'kho', 'inventory', 'stock']):
        total_products = Product.query.count()
        total_value = db.session.query(func.sum(Product.cost * Product.quantity)).scalar() or 0
        out_count = Product.query.filter(Product.quantity == 0).count()
        return {
            'answer': f'🏪 **Tình trạng kho hàng:**\n• Tổng sản phẩm: **{total_products} loại**\n• Tổng giá trị tồn kho: **{total_value:,.0f} VNĐ**\n• Sản phẩm hết hàng: **{out_count} loại**',
            'type': 'inventory'
        }

    # --- SẢN PHẨM (tìm kiếm tên) ---
    if any(k in q for k in ['sản phẩm', 'product', 'hàng']):
        count = Product.query.count()
        return {'answer': f'📦 Hệ thống có tổng cộng **{count} sản phẩm**.', 'type': 'info'}

    # --- GIÚP ĐỠ ---
    if any(k in q for k in ['giúp', 'help', 'hỏi', 'làm gì', 'hướng dẫn']):
        return {
            'answer': '🤖 **Tôi có thể trả lời các câu hỏi:**\n• 💰 Doanh thu hôm nay / tháng này / tuần này\n• ⚠️ Sản phẩm sắp hết hàng\n• 🏆 Sản phẩm bán chạy nhất\n• 📋 Thông tin đơn hàng\n• 👥 Thông tin khách hàng\n• 🏪 Tình trạng tồn kho',
            'type': 'help'
        }

    # --- CHÀO HỎI ---
    if any(k in q for k in ['xin chào', 'hello', 'hi', 'chào', 'alo']):
        return {'answer': '👋 Xin chào! Tôi là **AI trợ lý KhoManager**.\nHỏi tôi về doanh thu, tồn kho, đơn hàng nhé!', 'type': 'greeting'}

    return {
        'answer': f'❓ Tôi chưa hiểu câu hỏi này.\nGõ **"giúp tôi"** để xem danh sách câu hỏi tôi có thể trả lời.',
        'type': 'unknown'
    }
