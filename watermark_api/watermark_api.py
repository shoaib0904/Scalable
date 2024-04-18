from flask import Flask, request, send_file
from PIL import Image, ImageDraw, ImageFont
import os
import uuid
from flask_cors import CORS # type: ignore

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
WATERMARK_FOLDER = 'watermarks'
OUTPUT_FOLDER = 'output'

for folder in [UPLOAD_FOLDER, WATERMARK_FOLDER, OUTPUT_FOLDER]:
    os.makedirs(folder, exist_ok=True)

@app.route('/add_watermark', methods=['POST'])
def add_watermark():
    image_file = request.files['image']
    watermark_file = request.files['watermark']
    position = request.form.get('position', 'bottom-right')
    opacity = float(request.form.get('opacity', 0.5))

    image_path = os.path.join(UPLOAD_FOLDER, str(uuid.uuid4()) + os.path.splitext(image_file.filename)[1])
    watermark_path = os.path.join(WATERMARK_FOLDER, str(uuid.uuid4()) + os.path.splitext(watermark_file.filename)[1])
    image_file.save(image_path)
    watermark_file.save(watermark_path)

    image = Image.open(image_path)

    watermark = Image.open(watermark_path).convert('RGBA')

    watermark_with_opacity = Image.new('RGBA', watermark.size)
    for x in range(watermark.width):
        for y in range(watermark.height):
            r, g, b, alpha = watermark.getpixel((x, y))
            watermark_with_opacity.putpixel((x, y), (r, g, b, int(alpha * opacity)))

    if 'top' in position:
        y = 0
    elif 'bottom' in position:
        y = image.size[1] - watermark.size[1]
    else:
        y = (image.size[1] - watermark.size[1]) // 2

    if 'left' in position:
        x = 0
    elif 'right' in position:
        x = image.size[0] - watermark.size[0]
    else:
        x = (image.size[0] - watermark.size[0]) // 2

    image.paste(watermark_with_opacity, (x, y), watermark_with_opacity)

    output_path = os.path.join(OUTPUT_FOLDER, os.path.splitext(os.path.basename(image_path))[0] + '_watermarked.jpg')
    image.save(output_path)

    return send_file(output_path, mimetype='image/jpeg')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True ,port=5001)
