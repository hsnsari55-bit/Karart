def classify(layer_name):

    layer = layer_name.strip().lower()

    # DUVAR
    if "duvar" in layer:
        return "WALL"

    # KAPI
    if "kapı" in layer or "kapi" in layer:
        return "DOOR"

    # PENCERE
    if "pencere" in layer:
        return "WINDOW"

    # KOLON
    if "kolon" in layer:
        return "COLUMN"

    # MERDİVEN
    if "merdiven" in layer:
        return "STAIR"

    # HATCH / TARAMA
    if "tarama" in layer or "hatch" in layer:
        return "HATCH"

    # YAZILAR
    if "yaz" in layer:
        return "TEXT"

    # ÖLÇÜ
    if "olcu" in layer or "ölçü" in layer or "kot" in layer:
        return "DIMENSION"

    # AKS
    if "aks" in layer:
        return "AXIS"

    # TEFRİŞ (Türkçe karakter farklarını yakalar)
    if "tefr" in layer:
        return "FURNITURE"

    return "OTHER"


if __name__ == "__main__":

    tests = [
        "Duvar",
        "kapı",
        "pencere",
        "Kolon",
        "Merdiven",
        "YAZI",
        "k ic olcu",
        "tarama",
        "tefrıs",
        "tefriş",
        "0"
    ]

    for t in tests:
        print(f"{t:<20} -> {classify(t)}")