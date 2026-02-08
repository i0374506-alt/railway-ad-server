from flask import Flask, jsonify, request, render_template_string, redirect, url_for, send_from_directory
import json
import os
from werkzeug.utils import secure_filename
from functools import wraps

app = Flask(__name__)

# --- 설정 ---
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "ad-config.json")
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASS = os.environ.get("ADMIN_PASS", "1234")

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# --- 데이터 관리 ---
def load_config():
    default_config = {
        "top_banner": {"enabled": False, "items": [], "clicks": 0},
        "bottom_banner": {"enabled": False, "items": [], "clicks": 0}
    }
    
    if not os.path.exists(CONFIG_FILE):
        return default_config
        
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
            for pos in ['top_banner', 'bottom_banner']:
                if pos not in config: 
                    config[pos] = default_config[pos]
                if 'items' not in config[pos]:
                    config[pos]['items'] = []
            return config
    except:
        return default_config

def save_config(config):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

# --- 인증 데코레이터 ---
def login_required(f):
    @wraps(f)
    def decorated(*view_args, **view_kwargs):
        auth = request.authorization
        if not auth or not (auth.username == ADMIN_USER and auth.password == ADMIN_PASS):
            return ('인증 필요', 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})
        return f(*view_args, **view_kwargs)
    return decorated

# --- 라우팅 ---

@app.route('/')
def home():
    return jsonify({
        "status": "ok",
        "message": "Screen Capture Defender Ad Server",
        "endpoints": {
            "ad_config": "/api/ad-config.json",
            "admin": "/admin"
        }
    })

# 클릭 카운팅 및 리다이렉트
@app.route('/click/<position>/<int:index>')
def ad_click(position, index):
    config = load_config()
    key = f"{position}_banner"
    
    if key in config and 0 <= index < len(config[key]['items']):
        config[key]['clicks'] += 1
        save_config(config)
        target_url = config[key]['items'][index].get('click_url', 'https://google.com')
        return redirect(target_url)
    
    return "Link not found", 404

@app.route('/api/ad-config.json', methods=['GET'])
def get_ad_config():
    config = load_config()
    processed_config = json.loads(json.dumps(config))
    for pos in ['top', 'bottom']:
        items = processed_config[f'{pos}_banner']['items']
        for i, item in enumerate(items):
            item['click_url'] = f"{request.host_url}click/{pos}/{i}"
    
    response = jsonify(processed_config)
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin_page():
    config = load_config()
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'save_settings':
            for pos in ['top', 'bottom']:
                config[f'{pos}_banner']['enabled'] = f'{pos}_enabled' in request.form
            save_config(config)
            return redirect(url_for('admin_page'))
            
        elif action == 'add_item':
            pos = request.form.get('position')
            link = request.form.get('link_url', '')
            file = request.files.get('image_file')
            
            if pos and file and file.filename != '':
                filename = secure_filename(f"{pos}_{len(config[f'{pos}_banner']['items'])}_{file.filename}")
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                image_url = f"{request.host_url}uploads/{filename}"
                
                config[f'{pos}_banner']['items'].append({
                    "image_url": image_url,
                    "click_url": link
                })
                save_config(config)
            return redirect(url_for('admin_page'))

        elif action == 'delete_item':
            pos = request.form.get('position')
            try:
                index = int(request.form.get('index'))
                items = config[f'{pos}_banner']['items']
                if 0 <= index < len(items):
                    del items[index]
                    save_config(config)
            except:
                pass
            return redirect(url_for('admin_page'))
            
        elif action == 'reset_count':
            pos = request.form.get('position')
            config[f'{pos}_banner']['clicks'] = 0
            save_config(config)
            return redirect(url_for('admin_page'))

    return render_template_string(ADMIN_TEMPLATE, config=config)

ADMIN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🛡️ 광고 관리자</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', sans-serif; 
            padding: 20px; 
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #fff;
        }
        .container { max-width: 900px; margin: 0 auto; }
        h2 { text-align: center; color: #00d4ff; margin-bottom: 30px; font-size: 1.8em; }
        
        .card { 
            background: rgba(255,255,255,0.1); 
            padding: 25px; 
            margin-bottom: 25px; 
            border-radius: 15px; 
            backdrop-filter: blur(10px);
        }
        .card-header { 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            border-bottom: 2px solid rgba(255,255,255,0.1); 
            padding-bottom: 15px; 
            margin-bottom: 20px; 
        }
        .card-header h3 { margin: 0; color: #00d4ff; }
        
        .stat-badge { 
            background: #238636; 
            color: white; 
            padding: 5px 15px; 
            border-radius: 20px; 
            font-weight: bold; 
            font-size: 0.9em; 
        }
        
        .item-list { list-style: none; padding: 0; }
        .item-row { 
            display: flex; 
            align-items: center; 
            background: rgba(0,0,0,0.3); 
            margin-bottom: 10px; 
            padding: 12px; 
            border-radius: 10px; 
            transition: transform 0.2s; 
        }
        .item-row:hover { transform: translateX(5px); }
        
        .item-img { 
            width: 150px; 
            height: 50px; 
            object-fit: cover; 
            border-radius: 5px; 
            border: 1px solid #444; 
            margin-right: 15px; 
        }
        .item-link { 
            flex-grow: 1; 
            color: #aaa; 
            font-size: 0.9em; 
            overflow: hidden; 
            text-overflow: ellipsis; 
            white-space: nowrap; 
        }
        .item-link i { margin-right: 5px; color: #666; }
        
        .btn { 
            padding: 10px 20px; 
            border: none; 
            border-radius: 8px; 
            cursor: pointer; 
            font-weight: 600; 
            transition: all 0.2s; 
            font-size: 0.95em;
        }
        .btn-del { background: #e74c3c; color: white; padding: 8px 15px; }
        .btn-del:hover { background: #c0392b; }
        .btn-add { background: #2ecc71; color: white; width: 100%; padding: 12px; margin-top: 15px; font-size: 1em; }
        .btn-add:hover { background: #27ae60; }
        .btn-save { background: #00d4ff; color: #1a1a2e; font-size: 1.1em; padding: 15px 40px; display: block; margin: 20px auto 0; }
        .btn-save:hover { background: #00b8e6; }
        .btn-reset { background: #555; color: white; font-size: 0.85em; padding: 5px 10px; }
        
        .add-box { 
            background: rgba(0,212,255,0.1); 
            padding: 20px; 
            border-radius: 10px; 
            border: 2px dashed #00d4ff; 
            margin-top: 20px; 
        }
        .add-box h4 { color: #00d4ff; margin-bottom: 15px; }
        
        .input-group { margin-bottom: 15px; }
        .input-group label { 
            display: block; 
            margin-bottom: 8px; 
            font-weight: bold; 
            font-size: 0.9em; 
            color: #aaa; 
        }
        input[type="text"], input[type="file"] { 
            width: 100%; 
            padding: 12px; 
            border: 1px solid #444; 
            border-radius: 8px; 
            box-sizing: border-box; 
            background: #0d1117;
            color: #fff;
            font-size: 1em;
        }
        input[type="file"] { padding: 10px; }
        input:focus { border-color: #00d4ff; outline: none; }
        
        .toggle-switch { 
            display: flex; 
            align-items: center; 
            gap: 12px; 
            font-weight: bold; 
            margin-bottom: 15px;
        }
        .toggle-switch input[type="checkbox"] {
            width: 50px;
            height: 26px;
            cursor: pointer;
        }
        
        .empty-msg { 
            text-align: center; 
            color: #666; 
            padding: 30px; 
            font-style: italic;
        }
        
        .server-status {
            background: rgba(46, 204, 113, 0.2);
            border-left: 4px solid #2ecc71;
            padding: 15px;
            border-radius: 0 10px 10px 0;
            margin-bottom: 25px;
        }
        .server-status h4 { color: #2ecc71; margin-bottom: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <h2>🛡️ Screen Capture Defender<br>광고 배너 관리자</h2>
        
        <div class="server-status">
            <h4>✅ 서버 정상 운영 중</h4>
            <span style="color: #aaa;">호스팅: Railway | API: /api/ad-config.json</span>
        </div>
        
        <form method="POST">
            <input type="hidden" name="action" value="save_settings">
            
            {% for pos in ['top', 'bottom'] %}
            <div class="card">
                <div class="card-header">
                    <h3>{{ "📍 상단 (Top)" if pos == 'top' else "📍 하단 (Bottom)" }} 배너</h3>
                    <div>
                        <span class="stat-badge">클릭: {{ config[pos+'_banner'].clicks }}회</span>
                        <form method="POST" style="display:inline; margin-left:10px;">
                            <input type="hidden" name="action" value="reset_count">
                            <input type="hidden" name="position" value="{{pos}}">
                            <button type="submit" class="btn btn-reset">초기화</button>
                        </form>
                    </div>
                </div>

                <div class="toggle-switch">
                    <input type="checkbox" name="{{pos}}_enabled" id="{{pos}}_enabled" {{ 'checked' if config[pos+'_banner'].enabled }}>
                    <label for="{{pos}}_enabled">광고 노출 활성화</label>
                </div>

                <p style="color:#888; margin-bottom:15px;"><b>등록된 배너: {{ config[pos+'_banner']['items']|length }}개</b></p>
                
                <ul class="item-list">
                    {% for item in config[pos+'_banner']['items'] %}
                    <li class="item-row">
                        <img src="{{ item.image_url }}" class="item-img" onerror="this.src='https://via.placeholder.com/150x50/333/666?text=Error'">
                        <span class="item-link" title="{{ item.click_url }}">
                            <i class="fas fa-link"></i> {{ item.click_url[:50] }}{% if item.click_url|length > 50 %}...{% endif %}
                        </span>
                        <button type="submit" form="del_{{pos}}_{{loop.index0}}" class="btn btn-del">
                            <i class="fas fa-trash-alt"></i>
                        </button>
                    </li>
                    {% else %}
                    <li class="empty-msg">등록된 배너가 없습니다. 아래에서 추가하세요.</li>
                    {% endfor %}
                </ul>
                
                <!-- 배너 추가 폼 -->
                <div class="add-box">
                    <h4><i class="fas fa-plus-circle"></i> 새 배너 추가</h4>
                    <form method="POST" enctype="multipart/form-data">
                        <input type="hidden" name="action" value="add_item">
                        <input type="hidden" name="position" value="{{pos}}">
                        
                        <div class="input-group">
                            <label><i class="fas fa-image"></i> 배너 이미지 (900x100 권장)</label>
                            <input type="file" name="image_file" accept="image/*" required>
                        </div>
                        <div class="input-group">
                            <label><i class="fas fa-link"></i> 클릭 시 이동할 링크</label>
                            <input type="text" name="link_url" placeholder="https://example.com" required>
                        </div>
                        <button type="submit" class="btn btn-add">
                            <i class="fas fa-upload"></i> 이 배너 등록하기
                        </button>
                    </form>
                </div>
            </div>
            {% endfor %}
            
            <button type="submit" class="btn btn-save">
                <i class="fas fa-save"></i> 설정 저장 (활성화 상태)
            </button>
        </form>

        <!-- 삭제 폼들 -->
        {% for pos in ['top', 'bottom'] %}
            {% for item in config[pos+'_banner']['items'] %}
            <form id="del_{{pos}}_{{loop.index0}}" method="POST" style="display:none;">
                <input type="hidden" name="action" value="delete_item">
                <input type="hidden" name="position" value="{{pos}}">
                <input type="hidden" name="index" value="{{loop.index0}}">
            </form>
            {% endfor %}
        {% endfor %}
        
    </div>
</body>
</html>
"""

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
