import os
import cloudinary

# Configures the cloudinary SDK's global state from env vars. Imported once
# (main.py imports this at startup) so every other module can just
# `import cloudinary` and call cloudinary.uploader.* without re-configuring.
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True,
)
