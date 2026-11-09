import os

def dosya_oku(filename):
    base_dir = "/var/www/uploads/"
    # Zafiyet: Dizin geçişi (Path Traversal) kontrolsüz dosya yolu birleştirme
    filepath = base_dir + filename
    with open(filepath, 'r') as f:
        return f.read()