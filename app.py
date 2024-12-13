from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta

app = Flask(__name__)

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database Model
class Material(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(100), unique=True, nullable=False)  # รหัสไม่ซ้ำ
    quantity = db.Column(db.Integer, nullable=False)
    expiry_date = db.Column(db.String(100), nullable=False)

# Temporary command for creating database tables
@app.cli.command('create_tables')
def create_tables():
    """Create all database tables."""
    with app.app_context():
        db.create_all()
    print("Tables created successfully!")

# Routes
@app.route('/')
def index():
    today = datetime.now()
    near_expiry_count = Material.query.filter(
        db.func.date(Material.expiry_date) <= (today + timedelta(days=30)).date()
    ).count()
    return render_template('index.html', near_expiry_count=near_expiry_count)

@app.route('/add_material', methods=['GET', 'POST'])
def add_material():
    error = None  # ตัวแปรเก็บข้อความข้อผิดพลาด
    if request.method == 'POST':
        name = request.form['name']
        code = request.form['code']
        quantity = int(request.form['quantity'])
        expiry_date = request.form['expiry_date']

        # ตรวจสอบว่ามีรหัสซ้ำหรือไม่
        existing_material = Material.query.filter_by(code=code).first()
        if existing_material:
            error = "รหัสวัสดุนี้มีอยู่ในระบบแล้ว กรุณาใช้รหัสใหม่"
        else:
            # เพิ่มวัสดุใหม่
            new_material = Material(name=name, code=code, quantity=quantity, expiry_date=expiry_date)
            db.session.add(new_material)
            db.session.commit()
            return redirect(url_for('manage_material'))
    return render_template('add_material.html', error=error)

@app.route('/manage_material', methods=['GET'])
def manage_material():
    search_query = request.args.get('search', '').lower()
    status_filter = request.args.get('status', 'all')
    today = datetime.now()

    materials = Material.query

    if search_query:
        materials = materials.filter(
            db.or_(
                Material.name.ilike(f"%{search_query}%"),
                Material.code.ilike(f"%{search_query}%")
            )
        )

    if status_filter == 'expired':
        materials = materials.filter(
            db.func.date(Material.expiry_date) < today.date()
        )
    elif status_filter == 'active':
        materials = materials.filter(
            db.func.date(Material.expiry_date) >= today.date()
        )

    materials = materials.all()
    return render_template('manage.html', inventory=materials)

@app.route('/edit_material/<int:id>', methods=['GET', 'POST'])
def edit_material(id):
    material = Material.query.get_or_404(id)
    if request.method == 'POST':
        material.name = request.form['name']
        material.quantity = int(request.form['quantity'])
        material.expiry_date = request.form['expiry_date']
        db.session.commit()
        return redirect(url_for('manage_material'))
    return render_template('edit_material.html', material=material)

@app.route('/delete_material/<int:id>', methods=['POST'])
def delete_material(id):
    material = Material.query.get_or_404(id)
    db.session.delete(material)
    db.session.commit()
    return redirect(url_for('manage_material'))

@app.route('/near_expiry')
def near_expiry():
    today = datetime.now()
    near_expiry_materials = Material.query.filter(
        db.func.date(Material.expiry_date) <= (today + timedelta(days=30)).date()
    ).all()
    return render_template('near_expiry.html', materials=near_expiry_materials, datetime=datetime)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)



