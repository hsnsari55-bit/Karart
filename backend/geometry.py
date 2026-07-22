def get_center(entity):

    if entity["type"] == "LINE":

        x = (entity["start"][0] + entity["end"][0]) / 2
        y = (entity["start"][1] + entity["end"][1]) / 2

    elif entity["type"] == "LWPOLYLINE":

        xs = [p[0] for p in entity["points"]]
        ys = [p[1] for p in entity["points"]]

        x = sum(xs) / len(xs)
        y = sum(ys) / len(ys)

    return x, y