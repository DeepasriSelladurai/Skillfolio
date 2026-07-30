from PIL import Image, ImageFilter, ImageEnhance, ImageOps


# -------------------------
# Main dispatcher
# -------------------------
def process_image(input_path, output_path, operation, value=""):
    """
    Opens an image, applies the requested operation, and saves the result.

    operation: one of
        "resize", "grayscale", "rotate", "blur",
        "sharpen", "brightness", "contrast",
        "flip_horizontal", "flip_vertical", "invert"
    value: extra parameter needed by some operations
        - resize: "WIDTHxHEIGHT" e.g. "300x300"
        - rotate: degrees e.g. "90"
        - blur: radius e.g. "5"
        - brightness / contrast: factor e.g. "1.5"
    """
    image = Image.open(input_path)

    # Normalize mode so saving works consistently for all formats
    if image.mode in ("P", "RGBA") and operation not in ("flip_horizontal", "flip_vertical"):
        image = image.convert("RGBA") if image.mode == "RGBA" else image.convert("RGB")

    if operation == "resize":
        image = _resize(image, value)
    elif operation == "grayscale":
        image = _grayscale(image)
    elif operation == "rotate":
        image = _rotate(image, value)
    elif operation == "blur":
        image = _blur(image, value)
    elif operation == "sharpen":
        image = _sharpen(image)
    elif operation == "brightness":
        image = _brightness(image, value)
    elif operation == "contrast":
        image = _contrast(image, value)
    elif operation == "flip_horizontal":
        image = _flip_horizontal(image)
    elif operation == "flip_vertical":
        image = _flip_vertical(image)
    elif operation == "invert":
        image = _invert(image)
    else:
        raise ValueError(f"Unknown operation: {operation}")

    image.save(output_path)


# -------------------------
# Individual operations
# -------------------------
def _resize(image, value):
    try:
        width_str, height_str = value.lower().split("x")
        width, height = int(width_str), int(height_str)
    except (ValueError, AttributeError):
        raise ValueError("Resize value must be in the form WIDTHxHEIGHT, e.g. 300x300")
    return image.resize((width, height))


def _grayscale(image):
    return ImageOps.grayscale(image)


def _rotate(image, value):
    try:
        degrees = float(value)
    except (ValueError, TypeError):
        raise ValueError("Rotate value must be a number of degrees, e.g. 90")
    return image.rotate(-degrees, expand=True)


def _blur(image, value):
    try:
        radius = float(value) if value else 2
    except ValueError:
        raise ValueError("Blur value must be a number, e.g. 5")
    return image.filter(ImageFilter.GaussianBlur(radius))


def _sharpen(image):
    return image.filter(ImageFilter.SHARPEN)


def _brightness(image, value):
    try:
        factor = float(value) if value else 1.0
    except ValueError:
        raise ValueError("Brightness value must be a number, e.g. 1.5")
    return ImageEnhance.Brightness(image).enhance(factor)


def _contrast(image, value):
    try:
        factor = float(value) if value else 1.0
    except ValueError:
        raise ValueError("Contrast value must be a number, e.g. 1.5")
    return ImageEnhance.Contrast(image).enhance(factor)


def _flip_horizontal(image):
    return image.transpose(Image.FLIP_LEFT_RIGHT)


def _flip_vertical(image):
    return image.transpose(Image.FLIP_TOP_BOTTOM)


def _invert(image):
    if image.mode == "RGBA":
        r, g, b, a = image.split()
        rgb_image = Image.merge("RGB", (r, g, b))
        inverted = ImageOps.invert(rgb_image)
        r2, g2, b2 = inverted.split()
        return Image.merge("RGBA", (r2, g2, b2, a))
    return ImageOps.invert(image.convert("RGB"))