import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nailo.settings")

import django
django.setup()

from nailo_be.models import Designs

# 네일 이미지 url 변경 코드

image_urls = [
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20240819_91%2F17240469738371QgRp_JPEG%2FIMG_20240527_164505_268.jpg",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20241014_261%2F1728892124507DqEYD_JPEG%2F1725264087160.jpg",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20240819_121%2F1724047028228kScLW_JPEG%2FIMG_20240624_161418_984.jpg",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20240410_139%2F1712700056594oDMRp_JPEG%2FIMG_1103.jpeg",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20240312_89%2F1710233543150VkiGL_JPEG%2F1705984101980.jpg",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20240312_85%2F1710233589964vyBiN_JPEG%2F1707785928895.jpg",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20240406_155%2F1712358796668hWuif_JPEG%2F1708523718786.jpg",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20240104_113%2F1704373972529pawBE_JPEG%2FIMG_0657.jpeg",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20240104_272%2F1704373767061n33Mt_JPEG%2FIMG_0655.jpeg",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20231222_115%2F1703220696056Icj75_JPEG%2FIMG_0566.jpeg",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20231217_165%2F1702804209605Vu3kq_JPEG%2F1699008949395.jpg",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20231217_174%2F1702802482027Cc4aK_JPEG%2F20231204_132659.jpg",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20231123_144%2F1700701764097e2XpW_JPEG%2F1671333029912-1.jpg",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20231217_53%2F1702805074487GBjx1_JPEG%2F1702369816962.jpg",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20231217_60%2F1702804326625SU7Me_JPEG%2F1699265279325.jpg",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20231217_280%2F1702803430411p1QMy_JPEG%2F1701262800994.jpg",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20231217_103%2F1702803889834x81zD_JPEG%2F1700799570233.jpg",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20211028_59%2F1635396327057AuR1d_JPEG%2F85xF_K-BOCpEf4Da-Mb-BLh0.jpeg.jpg",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20241001_183%2F1727712143054G7oVf_JPEG%2FIMG_5796.jpeg",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20241001_180%2F1727712086382ToW5T_JPEG%2FIMG_5819.jpeg",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20241001_273%2F1727712109718B4bIo_JPEG%2FIMG_5803.jpeg",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20231207_27%2F1701940613632OAtJp_JPEG%2FIMG_2825.jpeg",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20231113_34%2F169987476122459uDu_JPEG%2FB9F59C9C-98F2-46B7-8D4F-E70E70C54961.jpeg",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20231013_203%2F1697192162303221ez_JPEG%2FIMG_1780.jpeg",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20230911_51%2F16944339638479rO8X_JPEG%2FIMG_1502.jpeg",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20230816_165%2F1692142019434xMzxH_JPEG%2FIMG_1016.jpeg",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20240806_204%2F1722872124938KiPk2_JPEG%2F20240801_135242.jpg",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20241109_53%2F1731144925874CDqRz_JPEG%2F8B45EEC6-5903-491F-B010-95EACE7F7B92-38757-00001643C1BF69AB.jpeg",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20240908_220%2F1725790764925aPKrU_JPEG%2FKakaoTalk_20240908_191824117.jpg",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20240710_52%2F1720591960172GwkW5_JPEG%2FFD567A4B-B1A3-4FD3-A405-3B5F5A314E6A.jpeg",
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