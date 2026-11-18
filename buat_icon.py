from PIL import Image, ImageDraw

S = 256
img = Image.new("RGBA", (S, S), (0, 0, 0, 0))

# gradasi ungu
grad = Image.new("RGBA", (S, S))
gp = grad.load()
for y in range(S):
    for x in range(S):
        t = (x + y) / (2 * S)
        r = int(0x63 + (0x7C - 0x63) * t)
        g = int(0x66 + (0x3A - 0x66) * t)
        b = int(0xF1 + (0xED - 0xF1) * t)
        gp[x, y] = (r, g, b, 255)

# kotak membulat sebagai mask
mask = Image.new("L", (S, S), 0)
ImageDraw.Draw(mask).rounded_rectangle((0, 0, S - 1, S - 1), radius=int(S * 0.24), fill=255)
img.paste(grad, (0, 0), mask)

# petir putih
bolt = [(0.60, 0.08), (0.24, 0.56), (0.47, 0.56), (0.38, 0.92),
        (0.78, 0.42), (0.54, 0.42), (0.66, 0.08)]
ImageDraw.Draw(img).polygon([(x * S, y * S) for x, y in bolt], fill="white")

img.save("nexus.ico", sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
print("nexus.ico berhasil dibuat")