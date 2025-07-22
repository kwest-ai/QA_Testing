from PIL import Image

class ShortTermMemory:
    def __init__(self):
        self.current_screenshot = None
        self.current_widgets = []

    def store_screenshot(self, img: Image.Image):
        self.current_screenshot = img
        img.save("ui_snapshots/latest.png")

    def store_widgets(self, widgets_json):
        self.current_widgets = widgets_json
        with open("ui_snapshots/widgets.json", "w") as f:
            f.write(widgets_json)

    def save_image_from_bytes(self, img_bytes):
        from PIL import Image
        from io import BytesIO
        image = Image.open(BytesIO(img_bytes))
        image.save("ui_snapshots/latest.png")
        self.current_screenshot = image
        return image 