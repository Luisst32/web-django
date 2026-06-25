from django.core.files.storage import FileSystemStorage
import os
import hashlib
from django.conf import settings

class HashMatchStorage(FileSystemStorage):
    def _save(self, name, content):
        # Calculate size and hash of the incoming content
        try:
            content.seek(0)
            uploaded_hash = hashlib.md5()
            for chunk in content.chunks():
                uploaded_hash.update(chunk)
            uploaded_hash_hex = uploaded_hash.hexdigest()
            uploaded_size = content.size
        except Exception:
            # Fallback if content lacks size or seek/chunks methods
            return super()._save(name, content)

        # Search for duplicate file in the media root
        media_root = settings.MEDIA_ROOT
        if os.path.exists(media_root):
            for root, dirs, files in os.walk(media_root):
                for file in files:
                    filepath = os.path.join(root, file)
                    try:
                        # Filter by size first (extremely fast)
                        if os.path.getsize(filepath) == uploaded_size:
                            # Verify with MD5 hash
                            h = hashlib.md5()
                            with open(filepath, 'rb') as f:
                                while True:
                                    data = f.read(65536)
                                    if not data:
                                        break
                                    h.update(data)
                            file_hash_hex = h.hexdigest()
                            
                            if file_hash_hex == uploaded_hash_hex:
                                # Found duplicate! Reuse the existing file path
                                rel_path = os.path.relpath(filepath, media_root)
                                return rel_path
                    except Exception:
                        continue
        
        # Reset pointer and proceed to standard save if no duplicate was found
        try:
            content.seek(0)
        except Exception:
            pass
        return super()._save(name, content)
