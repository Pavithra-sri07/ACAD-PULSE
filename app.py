from flask import Flask, render_template_string, request, redirect, session, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from PIL import Image
import uuid
import re

app = Flask(__name__)
app.secret_key = 'acad_pulse_universal_2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///acadpulse.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
db = SQLAlchemy(app)

# =========================
# Database Models
# =========================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(20), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), default='student')
    department = db.Column(db.String(50))
    year = db.Column(db.String(20))
    section = db.Column(db.String(10))  # A / B / C
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Circular(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text)
    circular_type = db.Column(db.String(50), default='General')
    image_filename = db.Column(db.String(200))
    date = db.Column(db.DateTime, default=datetime.utcnow)


class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(20))
    feedback = db.Column(db.Text)
    rating = db.Column(db.Integer)
    date = db.Column(db.DateTime, default=datetime.utcnow)


class Accolade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    winner_name = db.Column(db.String(100))
    winner_image = db.Column(db.String(200))
    date = db.Column(db.DateTime, default=datetime.utcnow)


class RegistrationLink(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    link_title = db.Column(db.String(200), nullable=False)
    registration_url = db.Column(db.String(500), nullable=False)
    department = db.Column(db.String(50))
    expiry_date = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# =========================
# Helper functions
# =========================

def save_image(file):
    if file and file.filename:
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex[:8]}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        img = Image.open(file.stream)
        img.thumbnail((800, 600))
        img.save(filepath)
        return unique_filename
    return None


def is_valid_url(url):
    url_pattern = re.compile(
        r'^https?://(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
        r'localhost|'
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(?::\d+)?(?:/?|[/?]\S*)$',
        re.IGNORECASE
    )
    return url_pattern.match(url) is not None


def generate_student_id(dept, serial):
    codes = {
        'Computer Science': 'CS',
        'Computer Application': 'CA',
        'Maths': 'MT',
        'Physics': 'PH',
        'Chemistry': 'CH',
        'Biotechnology': 'BT',
        'Biochemistry': 'BC',
        'Microbiology': 'MB',
        'Tamil': 'TM',
        'English': 'EN',
        'BCom CA': 'BCA',
        'BCom CS': 'BCS',
        'BCom General': 'BCG',
        'BBA': 'BBA',
        'BBM': 'BBM',
        'IT': 'IT',
        'Data Science': 'DS',
        'AI & ML': 'AI'
    }
    return f"{codes.get(dept, 'STU')}{int(serial):03d}"


def init_db():
    with app.app_context():
        db.drop_all()
        db.create_all()
        admin = User(user_id='ADMIN001', full_name='College Admin', role='admin')
        admin.set_password('AdminPass2026')
        db.session.add(admin)
        db.session.commit()
        print("ACAD PULSE database initialized with default admin.")


# =========================
# HTML TEMPLATES
# =========================

LOGIN_TEMPLATE = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>ACAD PULSE | College Portal</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        *{margin:0;padding:0;box-sizing:border-box;font-family:Arial,sans-serif}
        body{
            background:linear-gradient(135deg,#667eea,#1e293b);
            min-height:100vh;
            display:flex;
            align-items:center;
            justify-content:center;
        }
        .login-card{
            background:white;
            padding:3rem 3rem 2.5rem;
            border-radius:20px;
            box-shadow:0 20px 40px rgba(15,23,42,0.35);
            width:100%;
            max-width:420px;
            text-align:center;
        }
        .main-title{
            color:#111827;
            margin-bottom:0.25rem;
            font-size:2.2rem;
            font-weight:700;
            letter-spacing:1px;
        }
        .subtitle{
            color:#6b7280;
            font-size:0.95rem;
            margin-bottom:1.4rem;
        }
        .form-group{
            margin-bottom:1.4rem;
            text-align:left;
        }
        .input-field{
            width:100%;
            padding:14px;
            border:2px solid #e5e7eb;
            border-radius:10px;
            font-size:15px;
            background:#f9fafb;
            color:#111827;
            transition:border-color 0.18s, box-shadow 0.18s, background 0.18s;
        }
        .input-field:focus{
            outline:none;
            border-color:#4f46e5;
            box-shadow:0 0 0 3px rgba(79,70,229,0.18);
            background:#ffffff;
        }
        .btn{
            width:100%;
            padding:14px;
            background:#2563eb;
            color:white;
            border:none;
            border-radius:10px;
            font-size:16px;
            font-weight:600;
            cursor:pointer;
            transition:background 0.2s;
            margin-top:0.5rem;
        }
        .btn:hover{
            background:#1d4ed8;
        }
        .alert{
            padding:12px 14px;
            margin:0 0 1rem 0;
            border-radius:10px;
            border-left:4px solid #ef4444;
            background:#fef2f2;
            color:#b91c1c;
            font-size:0.9rem;
            text-align:left;
        }
    </style>
</head>
<body>
<div class="login-card">
    <div class="main-title">ACAD PULSE</div>
    <div class="subtitle">College Academic Information & Updates Portal</div>

    {% with messages=get_flashed_messages() %}
    {% if messages %}
        {% for message in messages %}
            <div class="alert">{{ message }}</div>
        {% endfor %}
    {% endif %}
    {% endwith %}

    <form method="POST">
        <div class="form-group">
            <input type="text"
                   name="user_id"
                   class="input-field"
                   placeholder="Username"
                   required>
        </div>

        <div class="form-group">
            <input type="password"
                   name="password"
                   class="input-field"
                   placeholder="Enter your password"
                   required>
        </div>

        <button type="submit" class="btn">Login</button>
    </form>
</div>
</body>
</html>
'''

STUDENT_DASHBOARD = '''<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Student Dashboard | ACAD PULSE</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:Arial,sans-serif}
body{background:#f8fafc}
.navbar{
  background:white;
  padding:1.2rem 2rem;
  box-shadow:0 2px 10px rgba(15,23,42,0.08);
  position:sticky;top:0;z-index:100;
  display:flex;justify-content:space-between;align-items:center;
}
.nav-title{font-weight:700;font-size:1.1rem;color:#111827}
.nav-sub{font-size:0.75rem;color:#6b7280;text-transform:uppercase;letter-spacing:0.15em}
.nav-links a{
  color:#374151;text-decoration:none;
  padding:8px 16px;border-radius:999px;
  display:inline-block;margin-left:10px;
  font-size:0.9rem;font-weight:600;
}
.nav-links a:hover{background:#e5e7eb}
.container{max-width:1200px;margin:0 auto;padding:2rem 1.5rem 2.5rem}
.header{
  background:linear-gradient(135deg,#2563eb,#4f46e5);
  color:white;padding:2.5rem 2rem;border-radius:18px;
  margin-bottom:2.5rem;
}
.header h1{font-size:1.7rem;margin-bottom:0.4rem}
.header p{font-size:0.95rem;opacity:0.9}

.stats{
  display:grid;
  grid-template-columns:repeat(auto-fit,minmax(220px,1fr));
  gap:1.5rem;margin-bottom:2rem;
}
.stat-card{
  background:white;padding:1.8rem 1.6rem;border-radius:16px;
  text-align:center;box-shadow:0 10px 25px rgba(15,23,42,0.06);
}
.stat-number{font-size:2.4rem;font-weight:700;margin-bottom:0.4rem}
.blue{color:#2563eb}.green{color:#16a34a}
.orange{color:#ea580c}.purple{color:#7c3aed}
.stat-label{font-size:0.9rem;color:#4b5563}

.content-grid{
  display:grid;
  grid-template-columns:2fr 1.1fr;
  gap:1.6rem;
}
.card{
  background:white;padding:1.8rem 1.6rem;border-radius:16px;
  box-shadow:0 10px 25px rgba(15,23,42,0.06);
}
.card h3{margin-bottom:1.3rem;color:#111827;font-size:1.1rem}

.circular-item{
  background:#f1f5f9;padding:1.1rem;border-radius:12px;
  margin-bottom:1rem;border-left:4px solid #2563eb;
}
.circular-image{
  max-width:100%;height:180px;object-fit:cover;
  border-radius:8px;margin-bottom:0.6rem;
}
.type-badge{
  background:#2563eb;color:white;padding:3px 10px;
  border-radius:999px;font-size:0.76rem;font-weight:600;
}
.circular-item strong{display:block;margin-top:0.4rem}
.circular-item p{margin-top:0.35rem;color:#64748b;font-size:0.9rem}
.circular-item small{display:block;margin-top:0.3rem;color:#6b7280;font-size:0.8rem}

.ach-block{
  display:flex;align-items:center;
  padding:1.1rem;margin-bottom:1rem;
  background:#ecfdf5;border-radius:12px;
  border-left:4px solid #16a34a;
}
.achievement-winner-img{
  width:56px;height:56px;border-radius:50%;
  object-fit:cover;margin-right:0.9rem;border:2px solid #16a34a;
}
.ach-block strong{display:block}
.ach-block p{margin:0.35rem 0 0;color:#047857;font-size:0.9rem}

.reg-link-item{
  background:#eff6ff;padding:1.1rem;border-radius:12px;
  margin-bottom:1rem;border-left:4px solid #0284c7;
  display:flex;justify-content:space-between;align-items:center;gap:1rem;
}
.reg-link-item small{color:#6b7280;font-size:0.8rem}
.reg-link-btn{
  background:#0284c7;color:white;padding:9px 16px;border:none;
  border-radius:999px;cursor:pointer;font-weight:600;
  text-decoration:none;font-size:0.9rem;
}
.reg-link-btn:hover{background:#0369a1}

.no-data{text-align:center;padding:2.2rem;color:#9ca3af;font-size:0.9rem}

@media(max-width:900px){
  .content-grid{grid-template-columns:1fr}
}
@media(max-width:640px){
  .navbar{padding:0.9rem 1rem;flex-direction:column;align-items:flex-start;gap:0.4rem}
  .container{padding:1.5rem 1rem 2rem}
}
</style>
</head>
<body>
<nav class="navbar">
  <div>
    <div class="nav-title">ACAD PULSE</div>
    <div class="nav-sub">Student dashboard</div>
  </div>
  <div class="nav-links">
    <a href="/dashboard">Dashboard</a>
    <a href="/feedback">Feedback</a>
    <a href="/logout">Logout</a>
  </div>
</nav>

<div class="container">
  <div class="header">
    <h1>Welcome, {{ session.full_name }}</h1>
    <p>View latest circulars, achievements and registration links related to your college activities.</p>
  </div>

  <div class="stats">
    <div class="stat-card">
      <div class="stat-number blue">{{ circulars_count }}</div>
      <div class="stat-label">Circulars</div>
    </div>
    <div class="stat-card">
      <div class="stat-number green">{{ accolades_count }}</div>
      <div class="stat-label">Achievements</div>
    </div>
    <div class="stat-card">
      <div class="stat-number orange">{{ students_count }}</div>
      <div class="stat-label">Students</div>
    </div>
    <div class="stat-card">
      <div class="stat-number purple">{{ reg_links_count }}</div>
      <div class="stat-label">Active registration links</div>
    </div>
  </div>

  <div class="content-grid">
    <div class="card">
      <h3>📢 Latest Circulars</h3>
      {% if circulars %}
        {% for c in circulars %}
          <div class="circular-item">
            {% if c.image_filename %}
              <img src="/static/uploads/{{ c.image_filename }}" alt="{{ c.title }}" class="circular-image">
            {% endif %}
            <span class="type-badge">{{ c.circular_type }}</span>
            <strong>{{ c.title }}</strong>
            {% if c.content %}
              <p>{{ c.content[:120] }}{% if c.content|length > 120 %}...{% endif %}</p>
            {% endif %}
            <small>{{ c.date.strftime('%d/%m/%Y %H:%M') }}</small><br>
            <a href="/circular/{{ c.id }}" style="font-size:.8rem;color:#2563eb;text-decoration:none;">View full →</a>
          </div>
        {% endfor %}
      {% else %}
        <div class="no-data">No circulars posted yet.</div>
      {% endif %}
      <a href="/circulars" style="display:inline-block;margin-top:.6rem;font-size:.85rem;color:#2563eb;text-decoration:none;">View all →</a>
    </div>

    <div class="card">
      <h3>🏆 Achievements</h3>
      {% if accolades %}
        {% for a in accolades %}
          <div class="ach-block">
            {% if a.winner_image %}
              <img src="/static/uploads/{{ a.winner_image }}" alt="{{ a.winner_name }}" class="achievement-winner-img">
            {% endif %}
            <div>
              <strong>{{ a.title }}</strong>
              <p>{{ a.winner_name }}</p>
            </div>
          </div>
        {% endfor %}
      {% else %}
        <div class="no-data">No achievements posted yet.</div>
      {% endif %}
      <a href="/achievements" style="display:inline-block;margin-top:.6rem;font-size:.85rem;color:#2563eb;text-decoration:none;">View all →</a>
    </div>
  </div>

  <div class="card" style="margin-top:1.6rem">
    <h3>🔗 Registration Links</h3>
    {% if reg_links %}
      {% for link in reg_links %}
        <div class="reg-link-item">
          <div>
            <strong>{{ link.link_title }}</strong>
            {% if link.department %}
              <br><small>{{ link.department }}</small>
            {% endif %}
          </div>
          <a href="{{ link.registration_url }}" target="_blank" class="reg-link-btn">Register</a>
        </div>
      {% endfor %}
    {% else %}
      <div class="no-data">No registration links available.</div>
    {% endif %}
    <a href="/registration-links" style="display:inline-block;margin-top:.6rem;font-size:.85rem;color:#2563eb;text-decoration:none;">View all →</a>
  </div>
</div>
</body>
</html>
'''

FEEDBACK_TEMPLATE = '''<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Feedback | ACAD PULSE</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:Arial,sans-serif}
body{background:#f8fafc;display:flex;align-items:center;justify-content:center;min-height:100vh}
.card{
  background:white;padding:2rem 1.8rem;border-radius:16px;
  box-shadow:0 10px 25px rgba(15,23,42,0.08);max-width:480px;width:100%;
}
.card h1{font-size:1.4rem;margin-bottom:0.6rem;color:#111827}
.card p{font-size:0.9rem;color:#4b5563;margin-bottom:1.4rem}
textarea{
  width:100%;min-height:120px;border:1px solid #d1d5db;border-radius:10px;
  padding:10px 11px;font-size:0.9rem;resize:vertical;
}
.btn{
  padding:10px 16px;background:#2563eb;color:white;border:none;
  border-radius:8px;font-weight:600;cursor:pointer;font-size:0.9rem;
  margin-top:1rem;
}
.alert{
  padding:0.9rem 1rem;margin-bottom:1rem;border-radius:10px;
  border-left:4px solid #16a34a;background:#dcfce7;color:#166534;
  font-size:0.85rem;
}

/* 5‑star rating */
.rating-group{
  direction:rtl;display:inline-flex;gap:4px;margin:0.5rem 0 1.1rem;
}
.rating-group input{display:none}
.rating-group label{
  font-size:1.6rem;color:#d1d5db;cursor:pointer;
}
.rating-group input:checked ~ label,
.rating-group label:hover,
.rating-group label:hover ~ label{
  color:#facc15;
}
</style>
</head>
<body>
<div class="card">
  <h1>Feedback</h1>

  <p style="text-align:right; margin-top:-0.5rem;">
    <a href="/dashboard" style="font-size:0.85rem;color:#2563eb;text-decoration:none;">
      ← Back to Dashboard
    </a>
  </p>

  <p>Hi {{ session.full_name }}, share your suggestions to improve your institution and the ACAD PULSE portal.</p>

  {% with messages=get_flashed_messages() %}
  {% if messages %}
    {% for m in messages %}
      <div class="alert">{{ m }}</div>
    {% endfor %}
  {% endif %}
  {% endwith %}

  <form method="POST" action="/feedback-submit">
    <label>Your feedback</label>
    <textarea name="feedback" required></textarea>

    <label>Rate your experience</label>
    <div class="rating-group">
      <input type="radio" id="star5" name="rating" value="5" required>
      <label for="star5">★</label>
      <input type="radio" id="star4" name="rating" value="4">
      <label for="star4">★</label>
      <input type="radio" id="star3" name="rating" value="3">
      <label for="star3">★</label>
      <input type="radio" id="star2" name="rating" value="2">
      <label for="star2">★</label>
      <input type="radio" id="star1" name="rating" value="1">
      <label for="star1">★</label>
    </div>

    <button type="submit" class="btn">Submit feedback</button>
  </form>
</div>
</body>
</html>
'''

# =========================
# Student full list + detail pages
# =========================

STUDENT_CIRCULARS_PAGE = '''<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>All Circulars | ACAD PULSE</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:Arial,sans-serif}
body{background:#f8fafc}
.container{max-width:900px;margin:0 auto;padding:1.5rem}
h1{margin-bottom:1rem;color:#111827}
.circular-item{
  background:#f1f5f9;padding:1rem;border-radius:12px;
  margin-bottom:1rem;border-left:4px solid #2563eb;
}
.circular-item h3{margin:0 0 .3rem 0}
.circular-item small{color:#6b7280;font-size:.8rem}
.back{margin-bottom:1rem;display:inline-block;color:#2563eb;text-decoration:none;font-size:.9rem}
</style>
</head>
<body>
<div class="container">
  <a href="/dashboard" class="back">← Back to Dashboard</a>
  <h1>All Circulars</h1>
  {% if circulars %}
    {% for c in circulars %}
      <div class="circular-item">
        <h3>{{ c.title }} ({{ c.circular_type }})</h3>
        {% if c.content %}
          <p>{{ c.content }}</p>
        {% endif %}
        <small>{{ c.date.strftime('%d/%m/%Y %H:%M') }}</small><br>
        <a href="/circular/{{ c.id }}" style="font-size:.8rem;color:#2563eb;text-decoration:none;">Open full view →</a>
      </div>
    {% endfor %}
  {% else %}
    <p>No circulars found.</p>
  {% endif %}
</div>
</body>
</html>
'''

STUDENT_CIRCULAR_DETAIL_PAGE = '''<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>{{ circular.title }} | Circular | ACAD PULSE</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:Arial,sans-serif}
body{background:#0f172a;color:#e5e7eb}
.wrapper{
  max-width:900px;margin:0 auto;padding:1.5rem;
}
.back{margin-bottom:1rem;display:inline-block;color:#60a5fa;text-decoration:none;font-size:.9rem}
.card{
  background:#020617;border-radius:16px;padding:1.8rem;
  box-shadow:0 20px 40px rgba(0,0,0,0.6);
}
.badge{
  display:inline-block;padding:4px 10px;border-radius:999px;
  font-size:.75rem;font-weight:600;background:#1d4ed8;color:#e5e7eb;
}
h1{margin:.8rem 0 0.4rem 0;font-size:1.4rem}
.meta{font-size:.85rem;color:#9ca3af;margin-bottom:1rem}
.content{font-size:.95rem;line-height:1.6;white-space:pre-wrap}
.image-wrap{
  margin:1rem 0;border-radius:12px;overflow:hidden;
}
.image-wrap img{
  width:100%;max-height:480px;object-fit:contain;
  background:#020617;
}
</style>
</head>
<body>
<div class="wrapper">
  <a href="/circulars" class="back">← Back to all circulars</a>
  <div class="card">
    <span class="badge">{{ circular.circular_type }}</span>
    <h1>{{ circular.title }}</h1>
    <div class="meta">{{ circular.date.strftime('%d/%m/%Y %H:%M') }}</div>
    {% if circular.image_filename %}
    <div class="image-wrap">
      <img src="/static/uploads/{{ circular.image_filename }}" alt="{{ circular.title }}">
    </div>
    {% endif %}
    {% if circular.content %}
    <div class="content">{{ circular.content }}</div>
    {% endif %}
  </div>
</div>
</body>
</html>
'''

STUDENT_ACHIEVEMENTS_PAGE = '''<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>All Achievements | ACAD PULSE</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:Arial,sans-serif}
body{background:#f8fafc}
.container{max-width:900px;margin:0 auto;padding:1.5rem}
h1{margin-bottom:1rem;color:#111827}
.ach-block{
  display:flex;align-items:center;padding:1rem;margin-bottom:1rem;
  background:#ecfdf5;border-radius:12px;border-left:4px solid #16a34a;
}
.achievement-winner-img{
  width:56px;height:56px;border-radius:50%;
  object-fit:cover;margin-right:0.9rem;border:2px solid #16a34a;
}
.back{margin-bottom:1rem;display:inline-block;color:#2563eb;text-decoration:none;font-size:.9rem}
</style>
</head>
<body>
<div class="container">
  <a href="/dashboard" class="back">← Back to Dashboard</a>
  <h1>All Achievements</h1>
  {% if accolades %}
    {% for a in accolades %}
      <div class="ach-block">
        {% if a.winner_image %}
          <img src="/static/uploads/{{ a.winner_image }}" class="achievement-winner-img">
        {% endif %}
        <div>
          <strong>{{ a.title }}</strong>
          <p>{{ a.winner_name }}</p>
          <small>{{ a.date.strftime('%d/%m/%Y') }}</small>
        </div>
      </div>
    {% endfor %}
  {% else %}
    <p>No achievements found.</p>
  {% endif %}
</div>
</body>
</html>
'''

STUDENT_REG_LINKS_PAGE = '''<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>All Registration Links | ACAD PULSE</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:Arial,sans-serif}
body{background:#f8fafc}
.container{max-width:900px;margin:0 auto;padding:1.5rem}
h1{margin-bottom:1rem;color:#111827}
.reg-link-item{
  background:#eff6ff;padding:1rem;border-radius:12px;
  margin-bottom:1rem;border-left:4px solid #0284c7;
  display:flex;justify-content:space-between;align-items:center;gap:1rem;
}
.reg-link-btn{
  background:#0284c7;color:white;padding:8px 14px;border:none;
  border-radius:999px;cursor:pointer;font-weight:600;
  text-decoration:none;font-size:0.9rem;
}
.back{margin-bottom:1rem;display:inline-block;color:#2563eb;text-decoration:none;font-size:.9rem}
</style>
</head>
<body>
<div class="container">
  <a href="/dashboard" class="back">← Back to Dashboard</a>
  <h1>All Registration Links</h1>
  {% if reg_links %}
    {% for link in reg_links %}
      <div class="reg-link-item">
        <div>
          <strong>{{ link.link_title }}</strong>
          {% if link.department %}
            <br><small>{{ link.department }}</small>
          {% endif %}
        </div>
        <a href="{{ link.registration_url }}" target="_blank" class="reg-link-btn">Open</a>
      </div>
    {% endfor %}
  {% else %}
    <p>No registration links available.</p>
  {% endif %}
</div>
</body>
</html>
'''

# =========================
# ADMIN DASHBOARD
# =========================

ADMIN_DASHBOARD = '''<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Admin Dashboard | ACAD PULSE</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:Arial,sans-serif}
body{background:#f8fafc;min-height:100vh}
.sidebar{
  position:fixed;left:0;top:0;bottom:0;width:260px;
  background:#111827;color:white;padding:1.8rem 1.4rem;z-index:100;
}
.sidebar h2{margin-bottom:1.8rem;font-size:1rem;letter-spacing:0.18em;text-transform:uppercase}
.sidebar button{
  width:100%;padding:0.85rem 1rem;margin-bottom:0.7rem;
  background:#1f2937;border:none;color:#e5e7eb;border-radius:9px;
  font-size:0.9rem;cursor:pointer;text-align:left;font-weight:600;
}
.sidebar button.active{background:#2563eb;color:#f9fafb}
.sidebar button:hover{background:#111827}
.sidebar a{
  display:block;margin-top:2.4rem;padding:0.9rem 1rem;
  background:#ef4444;color:white;text-align:center;
  text-decoration:none;border-radius:9px;font-weight:600;font-size:0.9rem;
}

.main{margin-left:260px;padding:1.8rem}
.header{
  background:white;padding:1.9rem 1.7rem;border-radius:16px;
  margin-bottom:1.8rem;box-shadow:0 6px 18px rgba(15,23,42,0.06);
}
.header h1{color:#111827;margin-bottom:0.35rem;font-size:1.4rem}
.header p{color:#6b7280;font-size:0.9rem}

.stats-grid{
  display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));
  gap:1.3rem;margin-bottom:2rem;
}
.stat-card{
  background:linear-gradient(135deg,#2563eb,#4f46e5);
  color:white;padding:1.5rem 1.3rem;border-radius:14px;text-align:center;
}
.stat-card div:first-child{
  font-size:2rem;font-weight:700;margin-bottom:0.4rem;
}

.tab-content{
  display:none;background:white;padding:1.7rem 1.5rem;
  border-radius:16px;box-shadow:0 8px 22px rgba(15,23,42,0.06);
  margin-bottom:1.6rem;
}
.tab-content.active{display:block}
.tab-content h2{margin-bottom:1.2rem;color:#111827;font-size:1.2rem}
.tab-content h3{margin:1.2rem 0 0.8rem;color:#111827;font-size:1rem}

.form-group{margin-bottom:1rem}
input,select,textarea{
  width:100%;padding:10px 11px;border:1px solid #d1d5db;
  border-radius:8px;font-size:0.9rem;box-sizing:border-box;
}
textarea{height:110px;resize:vertical}
.btn{
  padding:10px 16px;background:#16a34a;color:white;border:none;
  border-radius:8px;font-weight:600;cursor:pointer;font-size:0.9rem;
}
.btn:hover{background:#15803d}
.delete-btn{
  background:#ef4444;color:white;border:none;
  padding:7px 11px;border-radius:7px;cursor:pointer;font-size:0.78rem;
}
.table{width:100%;border-collapse:collapse;margin-top:1rem;font-size:0.85rem}
.table th,.table td{padding:9px 8px;border-bottom:1px solid #e5e7eb;text-align:left}
.table th{background:#f9fafb;font-weight:600}
.type-badge{
  background:#2563eb;color:white;padding:3px 9px;
  border-radius:999px;font-size:0.7rem;font-weight:600;
}

.alert{
  padding:0.9rem 1rem;margin:1rem 0;
  border-radius:10px;border-left:4px solid;
  font-size:0.85rem;
}
.alert-success{background:#dcfce7;border-color:#16a34a;color:#166534}
.alert-error{background:#fee2e2;border-color:#ef4444;color:#b91c1c}

.circular-admin-image{
  max-width:70px;height:50px;object-fit:cover;border-radius:6px;
}
.feedback-row{
  background:#ecfdf5;border-left:3px solid #16a34a;
  padding:0.6rem;border-radius:7px;margin-bottom:0.3rem;
}
.grid-2{display:grid;grid-template-columns:1fr 1.1fr;gap:1.5rem}

/* image enlarge modal */
.enlargeable{cursor:pointer}
.modal-img-backdrop{
  display:none;position:fixed;inset:0;
  background:rgba(0,0,0,0.75);z-index:200;
  justify-content:center;align-items:center;
}
.modal-img-backdrop img{
  max-width:90vw;max-height:90vh;border-radius:10px;
  box-shadow:0 20px 40px rgba(0,0,0,0.5);
}
@media(max-width:900px){
  .sidebar{display:none}
  .main{margin-left:0;padding:1.3rem}
  .grid-2{grid-template-columns:1fr}
}
</style>
</head>
<body>
<div class="sidebar">
  <h2>ACAD PULSE ADMIN</h2>
  <button class="active" onclick="showTab('students')">Students</button>
  <button onclick="showTab('circulars')">Circulars</button>
  <button onclick="showTab('reglinks')">Registration Links</button>
  <button onclick="showTab('feedback')">Feedback</button>
  <button onclick="showTab('achievements')">Achievements</button>
  <button onclick="showTab('profile')">Profile</button>
  <a href="/logout">Logout</a>
</div>

<div class="main">
  <div class="header">
    <h1>Admin Dashboard</h1>
    <p>{{ session.full_name }}</p>
  </div>

  {% with messages=get_flashed_messages(with_categories=true) %}
  {% if messages %}
    {% for category, message in messages %}
      <div class="alert alert-{{ 'success' if category=='success' else 'error' }}">{{ message }}</div>
    {% endfor %}
  {% endif %}
  {% endwith %}

  <div class="stats-grid">
    <div class="stat-card">
      <div>{{ stats.students }}</div>
      <div>Students</div>
    </div>
    <div class="stat-card">
      <div>{{ stats.circulars }}</div>
      <div>Circulars</div>
    </div>
    <div class="stat-card">
      <div>{{ stats.reg_links }}</div>
      <div>Active links</div>
    </div>
    <div class="stat-card">
      <div>{{ stats.feedbacks }}</div>
      <div>Feedback entries</div>
    </div>
  </div>

  <!-- STUDENTS TAB -->
  <div id="students" class="tab-content active">
    <h2>👨‍🎓 Students</h2>
    <div class="grid-2">
      <div>
        <h3>Create student</h3>
        <form method="POST" action="/admin-create-student">
          <div class="form-group">
            <input name="full_name" placeholder="Full name *" required>
          </div>
          <div class="form-group">
            <select name="department" id="dept" required>
              <option value="">Select department *</option>

              <!-- UG -->
              <option value="Computer Science">Computer Science</option>
              <option value="Computer Application">Computer Application</option>
              <option value="Maths">Maths</option>
              <option value="Physics">Physics</option>
              <option value="Chemistry">Chemistry</option>
              <option value="Biotechnology">Biotechnology</option>
              <option value="Biochemistry">Biochemistry</option>
              <option value="Microbiology">Microbiology</option>
              <option value="Tamil">Tamil</option>
              <option value="English">English</option>
              <option value="BCom CA">BCom CA</option>
              <option value="BCom CS">BCom CS</option>
              <option value="BCom General">BCom General</option>
              <option value="BBA">BBA</option>
              <option value="BBM">BBM</option>
              <option value="IT">IT</option>
              <option value="Data Science">Data Science</option>
              <option value="AI & ML">AI & ML</option>

              <!-- PG -->
              <option value="MSc Computer Science">MSc Computer Science</option>
              <option value="MCA">MCA</option>
              <option value="MSc IT">MSc IT</option>
              <option value="MSc Maths">MSc Maths</option>
              <option value="MSc Physics">MSc Physics</option>
              <option value="MSc Chemistry">MSc Chemistry</option>
              <option value="MA English">MA English</option>
              <option value="MA Tamil">MA Tamil</option>
              <option value="MSc Microbiology">MSc Microbiology</option>
              <option value="MSc Biotechnology">MSc Biotechnology</option>
              <option value="MSc Biochemistry">MSc Biochemistry</option>
              <option value="MBA">MBA</option>
              <option value="MCom CA">MCom CA</option>
              <option value="MCom General">MCom General</option>
            </select>
          </div>

          <div class="form-group">
            <select name="section" required>
              <option value="">Select section *</option>
              <option value="A">A</option>
              <option value="B">B</option>
              <option value="C">C</option>
            </select>
          </div>

          <div class="form-group">
            <input name="year" placeholder="Year (I / II / III / PG I / II)">
          </div>
          <div class="form-group">
            <input name="serial" placeholder="Reg no. (001, 002 ...)" maxlength="3" required>
          </div>
          <div class="form-group">
            <input type="password" name="password" placeholder="Password *" required>
          </div>
          <button type="submit" class="btn">Create student</button>
        </form>
      </div>
      <div>
        <h3>Recent students ({{ stats.students }})</h3>
        <div style="max-height:380px;overflow:auto">
          <table class="table">
            <tr>
              <th>ID</th>
              <th>Name</th>
              <th>Department</th>
              <th>Section</th>
              <th>Action</th>
            </tr>
            {% for s in students %}
            <tr>
              <td><strong style="color:#2563eb">{{ s.user_id }}</strong></td>
              <td>{{ s.full_name }}</td>
              <td>{{ s.department or 'N/A' }}</td>
              <td>{{ s.section or 'N/A' }}</td>
              <td>
                <form method="POST" action="/admin-edit-student/{{ s.user_id }}" style="margin-bottom:4px;">
                  <input type="text" name="full_name" value="{{ s.full_name }}" placeholder="Name" required>
                  <input type="text" name="department" value="{{ s.department or '' }}" placeholder="Dept">
                  <input type="text" name="section" value="{{ s.section or '' }}" placeholder="Sec">
                  <input type="text" name="year" value="{{ s.year or '' }}" placeholder="Year">
                  <button type="submit" class="btn">Save</button>
                </form>
                <form method="POST" action="/admin-delete-student/{{ s.user_id }}" onsubmit="return confirm('Delete this student?');">
                  <button type="submit" class="delete-btn">Delete</button>
                </form>
              </td>
            </tr>
            {% endfor %}
          </table>
        </div>

        <div style="margin-top:1.6rem;">
          <h3>Reset student password</h3>
          <form method="POST" action="/admin-reset-student-password" style="max-width:360px;">
            <div class="form-group">
              <input name="student_id" placeholder="Student ID (e.g., CS001)" required>
            </div>
            <div class="form-group">
              <input type="password" name="new_password" placeholder="New password *" required>
            </div>
            <button type="submit" class="btn">Reset password</button>
          </form>
        </div>

      </div>
    </div>
  </div>

  <!-- CIRCULARS TAB -->
  <div id="circulars" class="tab-content">
    <h2>📢 Circulars</h2>
    <div class="grid-2">
      <div>
        <h3>Create circular</h3>
        <form method="POST" action="/admin-circular" enctype="multipart/form-data">
          <div class="form-group">
            <input name="title" placeholder="Title *" required>
          </div>
          <div class="form-group">
            <select name="circular_type">
              <option value="General">General</option>
              <option value="Exam">Exam</option>
              <option value="Event">Event</option>
            </select>
          </div>
          <div class="form-group">
            <textarea name="content" placeholder="Description"></textarea>
          </div>
          <div class="form-group">
            <label>Attach image (optional)</label>
            <input type="file" name="image" accept="image/*">
          </div>
          <button type="submit" class="btn">Post circular</button>
        </form>
      </div>
      <div>
        <h3>Recent circulars ({{ stats.circulars }})</h3>
        <table class="table">
          <tr>
            <th>Title</th><th>Type</th><th>Image</th><th>Date</th><th>Action</th>
          </tr>
          {% for c in circulars %}
          <tr>
            <td>{{ c.title }}</td>
            <td><span class="type-badge">{{ c.circular_type }}</span></td>
            <td>
              {% if c.image_filename %}
                <img src="/static/uploads/{{ c.image_filename }}" class="circular-admin-image enlargeable">
              {% else %}-{% endif %}
            </td>
            <td>{{ c.date.strftime('%d/%m/%Y') }}</td>
            <td>
              <form method="POST" action="/admin-edit-circular/{{ c.id }}" enctype="multipart/form-data">
                <input type="text" name="title" value="{{ c.title }}" required>
                <input type="text" name="circular_type" value="{{ c.circular_type }}" required>
                <textarea name="content" placeholder="Description">{{ c.content or '' }}</textarea>
                <input type="file" name="image" accept="image/*">
                <button type="submit" class="btn">Save</button>
              </form>
            </td>
          </tr>
          {% endfor %}
        </table>
      </div>
    </div>
  </div>

  <!-- REGISTRATION LINKS TAB -->
  <div id="reglinks" class="tab-content">
    <h2>🔗 Registration links</h2>
    <div class="grid-2">
      <div>
        <h3>Create link</h3>
        <form method="POST" action="/admin-reg-link">
          <div class="form-group">
            <input name="link_title" placeholder="Title *" required>
          </div>
          <div class="form-group">
            <input name="registration_url" placeholder="https://..." required>
          </div>
          <div class="form-group">
            <input name="department" placeholder="Department (optional)">
          </div>
          <div class="form-group">
            <label>Expiry (optional)</label>
            <input type="datetime-local" name="expiry_date">
          </div>
          <button type="submit" class="btn">Post link</button>
        </form>
      </div>
      <div>
        <h3>Active links ({{ stats.reg_links }})</h3>
        <table class="table">
          <tr>
            <th>Title</th><th>Dept</th><th>URL</th><th>Action</th>
          </tr>
          {% for l in reg_links %}
          <tr>
            <td>{{ l.link_title }}</td>
            <td>{{ l.department or '-' }}</td>
            <td><a href="{{ l.registration_url }}" target="_blank">open</a></td>
            <td>
              <form method="POST" action="/admin-edit-reg-link/{{ l.id }}">
                <input type="text" name="link_title" value="{{ l.link_title }}" required>
                <input type="text" name="registration_url" value="{{ l.registration_url }}" required>
                <input type="text" name="department" value="{{ l.department or '' }}">
                <input type="datetime-local" name="expiry_date">
                <button type="submit" class="btn">Save</button>
              </form>
              <form method="POST" action="/admin-deactivate-link/{{ l.id }}" style="margin-top:4px;">
                <button type="submit" class="delete-btn">Deactivate</button>
              </form>
            </td>
          </tr>
          {% endfor %}
        </table>
      </div>
    </div>
  </div>

  <!-- FEEDBACK TAB -->
  <div id="feedback" class="tab-content">
    <h2>📝 Student feedback</h2>
    <div>
      {% for f in feedbacks %}
        <div class="feedback-row">
          <strong>{{ f.user_id }} • {{ f.rating }}/5</strong>
          <div>{{ f.feedback }}</div>
          <small>{{ f.date.strftime('%d/%m/%Y %H:%M') }}</small>
        </div>
      {% else %}
        <p>No feedback yet.</p>
      {% endfor %}
    </div>
  </div>

  <!-- ACHIEVEMENTS TAB -->
  <div id="achievements" class="tab-content">
    <h2>🏆 Achievements</h2>
    <div class="grid-2">
      <div>
        <h3>Post achievement</h3>
        <form method="POST" action="/admin-achievement" enctype="multipart/form-data">
          <div class="form-group">
            <input name="title" placeholder="Title *" required>
          </div>
          <div class="form-group">
            <input name="winner_name" placeholder="Winner name *" required>
          </div>
          <div class="form-group">
            <label>Winner photo (optional)</label>
            <input type="file" name="winner_image" accept="image/*">
          </div>
          <button type="submit" class="btn">Post achievement</button>
        </form>
      </div>
      <div>
        <h3>Recent achievements</h3>
        <table class="table">
          <tr>
            <th>Title</th><th>Winner</th><th>Photo</th><th>Date</th><th>Action</th>
          </tr>
          {% for a in accolades %}
          <tr>
            <td>{{ a.title }}</td>
            <td>{{ a.winner_name }}</td>
            <td>
              {% if a.winner_image %}
                <img src="/static/uploads/{{ a.winner_image }}" class="circular-admin-image enlargeable">
              {% else %}-{% endif %}
            </td>
            <td>{{ a.date.strftime('%d/%m/%Y') }}</td>
            <td>
              <form method="POST" action="/admin-edit-achievement/{{ a.id }}" enctype="multipart/form-data">
                <input type="text" name="title" value="{{ a.title }}" required>
                <input type="text" name="winner_name" value="{{ a.winner_name }}" required>
                <input type="file" name="winner_image" accept="image/*">
                <button type="submit" class="btn">Save</button>
              </form>
            </td>
          </tr>
          {% endfor %}
        </table>
      </div>
    </div>
  </div>

  <!-- PROFILE TAB -->
  <div id="profile" class="tab-content">
    <h2>🔐 Profile</h2>
    <h3>Change password</h3>
    <form method="POST" action="/admin-change-password" style="max-width:360px;">
      <div class="form-group">
        <input type="password" name="current_password" placeholder="Current password *" required>
      </div>
      <div class="form-group">
        <input type="password" name="new_password" placeholder="New password *" required>
      </div>
      <div class="form-group">
        <input type="password" name="confirm_password" placeholder="Confirm new password *" required>
      </div>
      <button type="submit" class="btn">Update password</button>
    </form>
  </div>

</div>

<div class="modal-img-backdrop" id="imgModal">
  <img src="" alt="Preview">
</div>

<script>
function showTab(id){
  document.querySelectorAll('.tab-content').forEach(e=>e.classList.remove('active'));
  document.getElementById(id).classList.add('active');
  document.querySelectorAll('.sidebar button').forEach(b=>b.classList.remove('active'));
  event.target.classList.add('active');
}

// image click‑to‑enlarge
document.addEventListener('click', function(e){
  if(e.target.classList.contains('enlargeable')){
    var modal = document.getElementById('imgModal');
    modal.querySelector('img').src = e.target.src;
    modal.style.display = 'flex';
  } else if(e.target.id === 'imgModal'){
    e.target.style.display = 'none';
  }
});
</script>
</body>
</html>
'''

# =========================
# Routes
# =========================

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(
            user_id=request.form['user_id'].upper().strip()
        ).first()
        if user and user.check_password(request.form['password']):
            session['user_id'] = user.user_id
            session['full_name'] = user.full_name
            session['role'] = user.role
            return redirect('/admin' if user.role == 'admin' else '/dashboard')
        flash('Invalid username or password.')
    return render_template_string(LOGIN_TEMPLATE)


@app.route('/dashboard')
def dashboard():
    if session.get('role') != 'student':
        return redirect('/')
    return render_template_string(
        STUDENT_DASHBOARD,
        session=session,
        circulars=Circular.query.order_by(Circular.date.desc()).limit(5).all(),
        accolades=Accolade.query.order_by(Accolade.date.desc()).limit(5).all(),
        reg_links=RegistrationLink.query.filter_by(is_active=True)
                   .order_by(RegistrationLink.created_at.desc()).limit(5).all(),
        circulars_count=Circular.query.count(),
        accolades_count=Accolade.query.count(),
        students_count=User.query.filter_by(role='student').count(),
        reg_links_count=RegistrationLink.query.filter_by(is_active=True).count()
    )


@app.route('/circulars')
def all_circulars():
    if session.get('role') != 'student':
        return redirect('/')
    circulars = Circular.query.order_by(Circular.date.desc()).all()
    return render_template_string(STUDENT_CIRCULARS_PAGE, session=session, circulars=circulars)


@app.route('/circular/<int:circ_id>')
def circular_detail(circ_id):
    if session.get('role') != 'student':
        return redirect('/')
    circular = Circular.query.get_or_404(circ_id)
    return render_template_string(STUDENT_CIRCULAR_DETAIL_PAGE, session=session, circular=circular)


@app.route('/achievements')
def all_achievements():
    if session.get('role') != 'student':
        return redirect('/')
    accolades = Accolade.query.order_by(Accolade.date.desc()).all()
    return render_template_string(STUDENT_ACHIEVEMENTS_PAGE, session=session, accolades=accolades)


@app.route('/registration-links')
def all_reg_links():
    if session.get('role') != 'student':
        return redirect('/')
    reg_links = RegistrationLink.query.filter_by(is_active=True)\
                .order_by(RegistrationLink.created_at.desc()).all()
    return render_template_string(STUDENT_REG_LINKS_PAGE, session=session, reg_links=reg_links)


@app.route('/feedback')
def feedback():
    if session.get('role') != 'student':
        return redirect('/')
    return render_template_string(FEEDBACK_TEMPLATE, session=session)


@app.route('/feedback-submit', methods=['POST'])
def feedback_submit():
    if session.get('role') != 'student':
        return redirect('/')
    feedback_data = Feedback(
        user_id=session['user_id'],
        feedback=request.form['feedback'],
        rating=int(request.form['rating'])
    )
    db.session.add(feedback_data)
    db.session.commit()
    flash('Feedback submitted successfully.')
    return redirect('/feedback')


@app.route('/admin')
def admin():
    if session.get('role') != 'admin':
        return redirect('/')
    stats = {
        'students': User.query.filter_by(role='student').count(),
        'circulars': Circular.query.count(),
        'feedbacks': Feedback.query.count(),
        'reg_links': RegistrationLink.query.filter_by(is_active=True).count()
    }
    return render_template_string(
        ADMIN_DASHBOARD,
        session=session,
        stats=stats,
        students=User.query.filter_by(role='student')
                 .order_by(User.created_at.desc()).all(),
        circulars=Circular.query.order_by(Circular.date.desc()).limit(10).all(),
        feedbacks=Feedback.query.order_by(Feedback.date.desc()).limit(50).all(),
        accolades=Accolade.query.order_by(Accolade.date.desc()).limit(10).all(),
        reg_links=RegistrationLink.query.filter_by(is_active=True)
                   .order_by(RegistrationLink.created_at.desc()).limit(10).all()
    )


@app.route('/admin-create-student', methods=['POST'])
def create_student():
    if session.get('role') != 'admin':
        return redirect('/')
    sid = generate_student_id(request.form['department'], request.form['serial'])
    if not User.query.filter_by(user_id=sid).first():
        student = User(
            user_id=sid,
            full_name=request.form['full_name'],
            role='student',
            department=request.form['department'],
            year=request.form.get('year', ''),
            section=request.form.get('section')
        )
        student.set_password(request.form['password'])
        db.session.add(student)
        db.session.commit()
        flash(f'Student {sid} created successfully.', 'success')
    else:
        flash(f'ID {sid} already exists.', 'error')
    return redirect('/admin#students')


@app.route('/admin-edit-student/<user_id>', methods=['POST'])
def admin_edit_student(user_id):
    if session.get('role') != 'admin':
        return redirect('/')
    student = User.query.filter_by(user_id=user_id, role='student').first_or_404()
    student.full_name = request.form['full_name']
    student.department = request.form.get('department', '')
    student.section = request.form.get('section', '')
    student.year = request.form.get('year', '')
    db.session.commit()
    flash('Student updated successfully.', 'success')
    return redirect('/admin#students')


@app.route('/admin-delete-student/<user_id>', methods=['POST'])
def delete_student(user_id):
    if session.get('role') != 'admin':
        return redirect('/')
    student = User.query.filter_by(user_id=user_id, role='student').first()
    if student:
        db.session.delete(student)
        db.session.commit()
        flash('Student deleted successfully.', 'success')
    return redirect('/admin#students')


@app.route('/admin-circular', methods=['POST'])
def post_circular():
    if session.get('role') != 'admin':
        return redirect('/')
    image_filename = save_image(request.files.get('image')) if 'image' in request.files else None
    circular = Circular(
        title=request.form['title'],
        content=request.form['content'],
        circular_type=request.form['circular_type'],
        image_filename=image_filename
    )
    db.session.add(circular)
    db.session.commit()
    flash('Circular posted successfully.', 'success')
    return redirect('/admin#circulars')


@app.route('/admin-edit-circular/<int:circ_id>', methods=['POST'])
def admin_edit_circular(circ_id):
    if session.get('role') != 'admin':
        return redirect('/')
    circular = Circular.query.get_or_404(circ_id)
    circular.title = request.form['title']
    circular.content = request.form.get('content', '')
    circular.circular_type = request.form.get('circular_type', circular.circular_type)
    if 'image' in request.files and request.files['image'].filename:
        circular.image_filename = save_image(request.files['image'])
    db.session.commit()
    flash('Circular updated successfully.', 'success')
    return redirect('/admin#circulars')


@app.route('/admin-achievement', methods=['POST'])
def post_achievement():
    if session.get('role') != 'admin':
        return redirect('/')
    winner_image = save_image(request.files.get('winner_image')) if 'winner_image' in request.files else None
    db.session.add(
        Accolade(
            title=request.form['title'],
            winner_name=request.form['winner_name'],
            winner_image=winner_image
        )
    )
    db.session.commit()
    flash('Achievement posted successfully.', 'success')
    return redirect('/admin#achievements')


@app.route('/admin-edit-achievement/<int:acc_id>', methods=['POST'])
def admin_edit_achievement(acc_id):
    if session.get('role') != 'admin':
        return redirect('/')
    acc = Accolade.query.get_or_404(acc_id)
    acc.title = request.form['title']
    acc.winner_name = request.form['winner_name']
    if 'winner_image' in request.files and request.files['winner_image'].filename:
        acc.winner_image = save_image(request.files['winner_image'])
    db.session.commit()
    flash('Achievement updated successfully.', 'success')
    return redirect('/admin#achievements')


@app.route('/admin-reg-link', methods=['POST'])
def admin_reg_link():
    if session.get('role') != 'admin':
        return redirect('/')
    url = request.form['registration_url'].strip()
    if not is_valid_url(url):
        flash('Invalid URL format. Use https://...', 'error')
        return redirect('/admin#reglinks')

    raw_expiry = request.form.get('expiry_date', '').strip()
    expiry = None
    if raw_expiry:
        try:
            expiry = datetime.fromisoformat(raw_expiry)
        except ValueError:
            flash('Invalid expiry date format.', 'error')
            return redirect('/admin#reglinks')

    link = RegistrationLink(
        link_title=request.form['link_title'],
        registration_url=url,
        department=request.form.get('department', ''),
        expiry_date=expiry
    )
    db.session.add(link)
    db.session.commit()
    flash('Registration link posted successfully.', 'success')
    return redirect('/admin#reglinks')


@app.route('/admin-edit-reg-link/<int:link_id>', methods=['POST'])
def admin_edit_reg_link(link_id):
    if session.get('role') != 'admin':
        return redirect('/')
    link = RegistrationLink.query.get_or_404(link_id)
    url = request.form['registration_url'].strip()
    if not is_valid_url(url):
        flash('Invalid URL format. Use https://...', 'error')
        return redirect('/admin#reglinks')
    raw_expiry = request.form.get('expiry_date', '').strip()
    expiry = None
    if raw_expiry:
        try:
            expiry = datetime.fromisoformat(raw_expiry)
        except ValueError:
            flash('Invalid expiry date format.', 'error')
            return redirect('/admin#reglinks')
    link.link_title = request.form['link_title']
    link.registration_url = url
    link.department = request.form.get('department', '')
    link.expiry_date = expiry
    db.session.commit()
    flash('Registration link updated successfully.', 'success')
    return redirect('/admin#reglinks')


@app.route('/admin-deactivate-link/<int:link_id>', methods=['POST'])
def admin_deactivate_link(link_id):
    if session.get('role') != 'admin':
        return redirect('/')
    link = RegistrationLink.query.get_or_404(link_id)
    link.is_active = False
    db.session.commit()
    flash('Link deactivated successfully.', 'success')
    return redirect('/admin#reglinks')


@app.route('/admin-change-password', methods=['POST'])
def admin_change_password():
    if session.get('role') != 'admin':
        return redirect('/')
    user = User.query.filter_by(user_id=session['user_id']).first()
    if not user or not user.check_password(request.form['current_password']):
        flash('Current password is incorrect.', 'error')
        return redirect('/admin#profile')
    new = request.form['new_password']
    confirm = request.form['confirm_password']
    if new != confirm:
        flash('New password and confirm password do not match.', 'error')
        return redirect('/admin#profile')
    user.set_password(new)
    db.session.commit()
    flash('Password updated successfully.', 'success')
    return redirect('/admin#profile')


@app.route('/admin-reset-student-password', methods=['POST'])
def admin_reset_student_password():
    if session.get('role') != 'admin':
        return redirect('/')
    sid = request.form['student_id'].strip().upper()
    student = User.query.filter_by(user_id=sid, role='student').first()
    if not student:
        flash('Student ID not found.', 'error')
        return redirect('/admin#students')
    student.set_password(request.form['new_password'])
    db.session.commit()
    flash(f'Password reset for {sid} successfully.', 'success')
    return redirect('/admin#students')


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


@app.route('/static/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


if __name__ == '__main__':
    init_db()  # first run only; live DB irundha comment pannunga
    print("Run on: http://localhost:5000")
    app.run(debug=True, port=5000)
