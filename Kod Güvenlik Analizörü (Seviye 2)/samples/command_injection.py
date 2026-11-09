import subprocess

def ping_host(host):
    # Zafiyet: Kullanıcı girdisi doğrudan kabuk komutuna (shell=True) ekleniyor
    command = f"ping -c 1 {host}"
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout