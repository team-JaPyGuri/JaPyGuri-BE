import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nailo.settings")

import django
django.setup()

from nailo_be.models import Designs

# 네일 이미지 url 변경 코드

image_urls = [
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20230130_9%2F16750847329956HnIE_JPEG",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20240128_139%2F1706423797805G96rG_JPEG",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20230915_173%2F1694765834605GtxY2_JPEG",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20230322_178%2F1679494280825U0Yu5_JPEG",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20240128_49%2F17064237093247NfSG_JPEG",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20240128_70%2F1706423821567bRkFp_JPEG",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20240128_269%2F1706423838034ByPaJ_JPEG",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20240128_196%2F1706423775359d6CIq_JPEG",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20231127_107%2F17010487921428w89f_JPEG",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20231127_88%2F1701048654371kDR6M_JPEG",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20231127_256%2F1701048780020EVvPJ_JPEG",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20231127_172%2F1701048738054sY4Bw_JPEG",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20240819_217%2F17240470883924HEOx_JPEG",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20240819_91%2F17240469738371QgRp_JPEG",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20240819_121%2F1724047028228kScLW_JPEG",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20240312_89%2F1710233543150VkiGL_JPEG",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20240406_155%2F1712358796668hWuif_JPEG",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20240104_272%2F1704373767061n33Mt_JPEG",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20231222_115%2F1703220696056Icj75_JPEG",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20231217_17%2F1702803252189iVga3_JPEG",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20231217_165%2F1702804209605Vu3kq_JPEG",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20231123_144%2F1700701764097e2XpW_JPEG",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20231217_53%2F1702805074487GBjx1_JPEG",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20231217_280%2F1702803430411p1QMy_JPEG",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20231123_207%2F1700702405480PcmSe_JPEG",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20231120_199%2F1700478718737wmLX2_JPEG",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20231106_74%2F1699256057986C44H6_JPEG",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20230903_7%2F1693708797935KfFm0_JPEG",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20220926_266%2F1664198655510fT8WR_JPEG",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20220802_199%2F1659448781196m2VLB_JPEG",
]
# print(len(image_urls))

# URL 리스트와 shop_id 매칭하여 일괄 업데이트
designs = Designs.objects.filter(design_name__startswith="Design ").order_by("design_name")

# 디자인 순서대로 URL 매핑
for design, url in zip(designs, image_urls):
    try:
        design.design_url = url  # design_url 필드에 URL 설정
        design.save()
        print(f"Updated {design.design_name} with URL {url}")
    except Exception as e:
        print(f"Error updating {design.design_name}: {str(e)}")