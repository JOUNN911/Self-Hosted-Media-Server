# app.py - Flask Backend (İki Kategorili)
from flask import Flask, render_template, jsonify, send_file, abort
import os
import json
from datetime import datetime
import mimetypes

app = Flask(__name__)

# Film klasörleri ve kategorileri
MOVIE_CATEGORIES = {
    'Dizi': {
        'name': 'Dizi',
        'path': r"D:\gam",
        'icon': '🎬',
        'color': '#ff6b6b'
    },
    'film': {
        'name': 'Film',
        'path': r"D:\filmler", 
        'icon': '🎬',
        'color': '#4ecdc4'
    }
}

ALLOWED_VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.3gp'}

def get_file_size(filepath):
    """Dosya boyutunu human-readable formatta döndürür"""
    size = os.path.getsize(filepath)
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"

def scan_movies_in_category(category_key):
    """Belirtilen kategorideki video dosyalarını tarar"""
    movies = []
    category = MOVIE_CATEGORIES.get(category_key)
    
    if not category or not os.path.exists(category['path']):
        return movies
    
    try:
        for filename in os.listdir(category['path']):
            filepath = os.path.join(category['path'], filename)
            
            # Dosya mı kontrol et
            if os.path.isfile(filepath):
                # Video dosyası mı kontrol et
                _, ext = os.path.splitext(filename.lower())
                if ext in ALLOWED_VIDEO_EXTENSIONS:
                    # Dosya bilgilerini al
                    file_stats = os.stat(filepath)
                    creation_time = datetime.fromtimestamp(file_stats.st_ctime)
                    
                    movie = {
                        'filename': filename,
                        'title': os.path.splitext(filename)[0],  # Uzantısız dosya adı
                        'size': get_file_size(filepath),
                        'created_date': creation_time.strftime('%d.%m.%Y'),
                        'filepath': filepath,
                        'extension': ext,
                        'category': category_key,
                        'category_name': category['name']
                    }
                    movies.append(movie)
    
    except PermissionError:
        print(f"Erişim hatası: {category['path']} klasörüne erişim yok!")
    except Exception as e:
        print(f"Hata oluştu: {e}")
    
    # Filmleri alfabetik sırala
    movies.sort(key=lambda x: x['title'].lower())
    return movies

def scan_all_movies():
    """Tüm kategorilerdeki filmleri tarar"""
    all_movies = {}
    total_count = 0
    
    for category_key in MOVIE_CATEGORIES.keys():
        movies = scan_movies_in_category(category_key)
        all_movies[category_key] = movies
        total_count += len(movies)
    
    return all_movies, total_count

@app.route('/')
def index():
    """Ana sayfa"""
    return render_template('index.html')

@app.route('/api/movies')
def get_movies():
    """Tüm kategorilerdeki film listelerini JSON formatında döndürür"""
    all_movies, total_count = scan_all_movies()
    
    # Kategori bilgilerini ekle
    categories_info = {}
    for key, category in MOVIE_CATEGORIES.items():
        categories_info[key] = {
            'name': category['name'],
            'path': category['path'],
            'icon': category['icon'],
            'color': category['color'],
            'count': len(all_movies.get(key, []))
        }
    
    return jsonify({
        'success': True,
        'movies': all_movies,
        'categories': categories_info,
        'total_count': total_count
    })

@app.route('/api/movies/<category>')
def get_movies_by_category(category):
    """Belirli bir kategorideki filmleri döndürür"""
    if category not in MOVIE_CATEGORIES:
        return jsonify({'success': False, 'error': 'Geçersiz kategori'}), 400
    
    movies = scan_movies_in_category(category)
    category_info = MOVIE_CATEGORIES[category]
    
    return jsonify({
        'success': True,
        'movies': movies,
        'category': {
            'key': category,
            'name': category_info['name'],
            'path': category_info['path'],
            'icon': category_info['icon'],
            'color': category_info['color'],
            'count': len(movies)
        }
    })

@app.route('/api/play/<category>/<path:filename>')
def play_movie(category, filename):
    """Film dosyasını stream eder"""
    if category not in MOVIE_CATEGORIES:
        abort(404)
    
    category_path = MOVIE_CATEGORIES[category]['path']
    filepath = os.path.join(category_path, filename)
    
    # Dosya var mı kontrol et
    if not os.path.exists(filepath):
        abort(404)
    
    # Güvenlik kontrolü - sadece belirtilen kategori klasöründeki dosyalar
    if not filepath.startswith(os.path.abspath(category_path)):
        abort(403)
    
    # MIME type'ı belirle
    mime_type, _ = mimetypes.guess_type(filepath)
    if not mime_type or not mime_type.startswith('video/'):
        mime_type = 'video/mp4'
    
    return send_file(filepath, mimetype=mime_type, as_attachment=False)

@app.route('/api/refresh')
def refresh_movies():
    """Tüm kategorilerdeki film listelerini yeniler"""
    all_movies, total_count = scan_all_movies()
    return jsonify({
        'success': True,
        'message': 'Film listeleri güncellendi',
        'total_count': total_count
    })

@app.route('/api/refresh/<category>')
def refresh_category(category):
    """Belirli bir kategorideki film listesini yeniler"""
    if category not in MOVIE_CATEGORIES:
        return jsonify({'success': False, 'error': 'Geçersiz kategori'}), 400
    
    movies = scan_movies_in_category(category)
    return jsonify({
        'success': True,
        'message': f'{MOVIE_CATEGORIES[category]["name"]} kategorisi güncellendi',
        'count': len(movies)
    })

if __name__ == '__main__':
    print("Film Arşivi Sunucusu")
    print("=" * 50)
    for key, category in MOVIE_CATEGORIES.items():
        print(f"{category['icon']} {category['name']}: {category['path']}")
    print("=" * 50)
    print("Flask sunucu başlatılıyor...")
    print("http://127.0.0.1:5000 adresine gidin")
    
    # Debug mode'u aktif et
    app.run(debug=True, host='127.0.0.1', port=5000)