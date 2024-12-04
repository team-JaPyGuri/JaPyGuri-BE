import sys
import os
import uuid

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nailo.settings")

import django
django.setup()

from nailo_be.models import Designs
from django.conf import settings

image_files = [f"design_{i}.png" for i in range(1, 11)]

image_urls = [os.path.join(settings.MEDIA_URL, "tryon_design", image_file) for image_file in image_files]

designs_to_update = Designs.objects.filter(design_name__startswith="Design ").order_by("design_name")
updated_design_keys = [] 

for design, url in zip(designs_to_update[:10], image_urls):
    try:
        design.design_url = url
        design.is_active = True 
        design.save()
        updated_design_keys.append(design.design_key)
        print(f"Updated {design.design_name} with URL {url}")
    except Exception as e:
        print(f"Error updating {design.design_name}: {str(e)}")

remaining_designs = Designs.objects.exclude(design_key__in=updated_design_keys)
for design in remaining_designs:
    try:
        design.is_active = False
        design.save()
        print(f"Deactivated {design.design_name}")
    except Exception as e:
        print(f"Error deactivating {design.design_name}: {str(e)}")