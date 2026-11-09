import pickle

def load_data(serialized_data):
    # Zafiyet: Güvenilmeyen veri pickle modülü ile doğrudan seri dışı bırakılıyor (deserialization)
    return pickle.loads(serialized_data)