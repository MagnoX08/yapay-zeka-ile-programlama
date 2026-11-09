import os
import html

def calculate_sum(a, b):
    # Güvenli toplama fonksiyonu
    return a + b

def sanitize_input(user_input):
    # Girdiyi güvenli hale getirme (HTML escape)
    return html.escape(user_input)