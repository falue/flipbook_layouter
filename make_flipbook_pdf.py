import os
from PIL import Image
from reportlab.lib.pagesizes import landscape, A3
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm

# === CONFIGURATION ===
FRAME_WIDTH_MM = 325.0  # Small: 223.0, Large: 325.0
FRAME_HEIGHT_MM = 281.3
INPUT_FOLDER = "./animation"
OUTPUT_FOLDER = "./processed"
OUTPUT_PDF = f"./output/flipbook-{FRAME_WIDTH_MM}x{FRAME_HEIGHT_MM}mm.pdf"

# === CONVERSION TO PIXELS ===
DPI = 300
FRAME_WIDTH_PX = int(FRAME_WIDTH_MM / 25.4 * DPI)
FRAME_HEIGHT_PX = int(FRAME_HEIGHT_MM / 25.4 * DPI)

# Ensure output folder exists
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def resize_and_crop(image):
    """Resize and crop an image to exactly FRAME_WIDTH_PX x FRAME_HEIGHT_PX."""
    img_ratio = image.width / image.height
    target_ratio = FRAME_WIDTH_PX / FRAME_HEIGHT_PX

    # Resize while maintaining aspect ratio
    if img_ratio > target_ratio:
        new_height = FRAME_HEIGHT_PX
        new_width = int(new_height * img_ratio)
    else:
        new_width = FRAME_WIDTH_PX
        new_height = int(new_width / img_ratio)

    image = image.resize((new_width, new_height), Image.LANCZOS)

    # Crop to the target size
    left = (new_width - FRAME_WIDTH_PX) // 2
    top = (new_height - FRAME_HEIGHT_PX) // 2
    right = left + FRAME_WIDTH_PX
    bottom = top + FRAME_HEIGHT_PX

    return image.crop((left, top, right, bottom))

def prepare_frames():
    """Resize and crop all images."""
    frame_paths = sorted([
        os.path.join(INPUT_FOLDER, f)
        for f in os.listdir(INPUT_FOLDER)
        if f.lower().endswith(('.png', '.jpg', '.jpeg'))
    ])

    processed = []
    for i, path in enumerate(frame_paths):
        img = Image.open(path).convert("RGB")
        img = resize_and_crop(img)
        output_path = os.path.join(OUTPUT_FOLDER, f"frame_{i:04d}.jpg")
        img.save(output_path, "JPEG", quality=95)
        processed.append(output_path)
    return processed

def create_composite_images(processed_frames):
    """Create composite images as described."""
    composites = []

    for i in range(len(processed_frames)):
        upper = Image.open(processed_frames[i])
        upper_half = upper.crop((0, 0, FRAME_WIDTH_PX, FRAME_HEIGHT_PX // 2))

        if i > 0:
            lower = Image.open(processed_frames[i - 1])
        else:
            # Use last image for lower half if its the first frame
            lower = Image.open(processed_frames[- 1])
        
        lower_half = lower.crop((0, FRAME_HEIGHT_PX // 2, FRAME_WIDTH_PX, FRAME_HEIGHT_PX))
        lower_half = lower_half.transpose(Image.ROTATE_180)

        combined = Image.new("RGB", (FRAME_WIDTH_PX, FRAME_HEIGHT_PX))
        combined.paste(upper_half, (0, 0))
        combined.paste(lower_half, (0, FRAME_HEIGHT_PX // 2))

        output_path = os.path.join(OUTPUT_FOLDER, f"composite_{i:04d}.jpg")
        combined.save(output_path, "JPEG", quality=95)
        composites.append(output_path)

    return composites

def export_to_pdf(composites):
    """Export combined images to an A3 PDF."""
    pdf = canvas.Canvas(OUTPUT_PDF, pagesize=landscape(A3))
    a3_width, a3_height = landscape(A3)

    for path in composites:
        img = Image.open(path)
        img_path = path  # already saved
        img_width_mm = FRAME_WIDTH_MM
        img_height_mm = FRAME_HEIGHT_MM

        x = (a3_width - img_width_mm * mm) / 2
        y = (a3_height - img_height_mm * mm) / 2

        pdf.drawImage(img_path, x, y, width=img_width_mm * mm, height=img_height_mm * mm)
        pdf.showPage()

    pdf.save()

if __name__ == "__main__":
    print("Make sure to name the files with leading zeros '01.jpg' and '02.jpg' not '1.jpg'!")
    print("")
    print("Resizing and cropping frames...")
    processed = prepare_frames()

    print("Creating composite images...")
    composites = create_composite_images(processed)

    print("Exporting to PDF...")
    export_to_pdf(composites)

    print(f"Done! PDF saved as {OUTPUT_PDF}")
