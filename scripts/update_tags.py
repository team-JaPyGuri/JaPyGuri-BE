import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nailo.settings")

import django
django.setup()

from nailo_be.models import Designs

designs = Designs.objects.all()

tags = ["1", "2", "3"]  # 임의로 설정
for index, design in enumerate(designs):
    design.tag = tags[index % len(tags)] 
    design.save()

print("Done")
