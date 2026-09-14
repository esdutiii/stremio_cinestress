import base64
import re
from urllib import parse

try:
    from Cryptodome.Cipher import AES
except ImportError:
    from Crypto.Cipher import AES

# Clave e IV base para los enlaces de 1fichier del addon Moria / CineStress
P3_KEY_B64 = b'hTh8uRnL5bX8PZC6Tc3t46nVDFfBpB6Tjw3qazQThpexpg8bLdimevNHj5vJR0nP'

def decrypt_link(encrypted_link: str) -> str:
    # Decodificamos la clave e IV principales
    key_iv = base64.b64decode(P3_KEY_B64)
    iv = key_iv[:16]
    key = key_iv[16:]
    
    # Creamos el descifrador en modo OFB
    cipher = AES.new(key, AES.MODE_OFB, iv)
    
    # Decodificamos el enlace cifrado en base64 urlsafe y aplicamos el descifrado
    raw_ciphertext = base64.urlsafe_b64decode(encrypted_link)
    decrypted_bytes = cipher.decrypt(raw_ciphertext)
    
    # Devolvemos la URL legible
    return decrypted_bytes.decode('utf-8', errors='ignore')

def decode_p3_base64(value: str) -> bytes:
    # Decodificamos el formato base64 invertido por mitades usado en las actualizaciones
    if not isinstance(value, bytes):
        value = parse.unquote(value).encode()
    else:
        value = parse.unquote(value)
        
    value = re.sub(rb'\?', b'', value)
    pad_needed = len(value) % 4
    padding = b''
    if pad_needed:
        padding = b'=' * (4 - pad_needed)
        
    half_index = int((len(value) + len(padding)) / 4)
    reordered = value[:half_index][::-1] + value[half_index:][::-1]
    return base64.b64decode(reordered + padding)
