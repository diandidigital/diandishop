from PIL import Image, ImageDraw, ImageFont

def rounded_rect(draw, xy, corner_radius, fill):
    x0, y0, x1, y1 = xy
    draw.rectangle([x0 + corner_radius, y0, x1 - corner_radius, y1], fill=fill)
    draw.rectangle([x0, y0 + corner_radius, x1, y1 - corner_radius], fill=fill)
    draw.ellipse([x0, y0, x0 + corner_radius*2, y0 + corner_radius*2], fill=fill)
    draw.ellipse([x1 - corner_radius*2, y0, x1, y0 + corner_radius*2], fill=fill)
    draw.ellipse([x0, y1 - corner_radius*2, x0 + corner_radius*2, y1], fill=fill)
    draw.ellipse([x1 - corner_radius*2, y1 - corner_radius*2, x1, y1], fill=fill)

def draw_logo(size):
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Fond bleu arrondi
    cr = max(int(size * 0.18), 4)
    rounded_rect(draw, [0, 0, size-1, size-1], cr, (39, 73, 215, 255))

    # Corps du sac (blanc)
    sx, sy = int(size*0.22), int(size*0.42)
    ex, ey = int(size*0.78), int(size*0.88)
    cr2 = max(int(size*0.07), 2)
    rounded_rect(draw, [sx, sy, ex, ey], cr2, (255, 255, 255, 242))

    # Poignee
    lw = max(int(size * 0.07), 2)
    for i in range(lw):
        draw.arc(
            [int(size*0.31)+i, int(size*0.18)+i, int(size*0.69)-i, int(size*0.50)-i],
            start=200, end=340, fill=(255, 255, 255, 230)
        )

    # Bande turquoise en bas
    band_y = int(size*0.72)
    if ey - band_y > cr2 * 2:
        rounded_rect(draw, [sx, band_y, ex, ey], cr2, (39, 184, 255, 230))

    # Texte DS
    font_size = max(int(size * 0.25), 8)
    try:
        font = ImageFont.truetype("arialbd.ttf", font_size)
    except Exception:
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except Exception:
            font = ImageFont.load_default()

    text = "DS"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    tx = (size - tw) // 2
    ty = int(size * 0.50) - th // 2
    draw.text((tx, ty), text, fill=(39, 73, 215, 255), font=font)

    return img

base = "c:/Users/TOSHIBA/diandishop/diandishop-python/static"

sizes = [256, 128, 64, 48, 32, 16]
images = [draw_logo(s) for s in sizes]
images[0].save(f"{base}/favicon.ico", format="ICO", sizes=[(s, s) for s in sizes])

draw_logo(192).save(f"{base}/logo192.png", format="PNG")
draw_logo(512).save(f"{base}/logo512.png", format="PNG")

print("Favicon et logos generes avec succes.")
