filepath = "data/GÜZELCE 467 ADA 3 PARSEL .(23.12.2025).dxf"
with open(filepath, "rb") as f:
    f.seek(0, 2)
    size = f.tell()
    # Read last 1000 bytes
    f.seek(max(0, size - 1000))
    last_bytes = f.read()

print("File size:", size)
print("Last 500 bytes of file as string (trying utf-8 / latin-1 decoding):")
try:
    print(last_bytes[-500:].decode('utf-8'))
except Exception:
    print(last_bytes[-500:].decode('latin-1'))
