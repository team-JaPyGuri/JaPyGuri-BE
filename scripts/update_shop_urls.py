import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nailo.settings")

import django
django.setup()

from nailo_be.models import Shops
# URL 리스트 준비
image_urls = [
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20230818_17%2F1692320629751Y8z8t_JPEG%2F1690633434499.jpg",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20240825_224%2F1724557571825z2z65_JPEG%2F65F0353A-1E6E-4EEC-A02A-8E23A406D7C8.jpeg",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20221126_165%2F1669390436524HSciX_JPEG%2F20221124_124907.jpg",
    "https://search.pstatic.net/common/?src=http%3A%2F%2Fblogfiles.naver.net%2FMjAyMTA1MThfNjgg%2FMDAxNjIxMzE3NjMyMTQy.sghhEnRsft8CFlJ98o4nzazcYfuQMnVM7kegqCha994g.UWEAa_WHb2GtewKvzL9j48J58N_4hRuclZ35gdjtp3Yg.JPEG.13si_s2%2F_MG_1094.JPG",
    "https://search.pstatic.net/common/?src=http%3A%2F%2Fimage.nmv.naver.net%2Fblog_2021_05_25_344%2Fcd4bdd75-bd01-11eb-96b3-a0369ff95ec0_01.jpg",
    "https://search.pstatic.net/common/?src=http%3A%2F%2Fblogfiles.naver.net%2FMjAyNDA5MTJfNDUg%2FMDAxNzI2MDk4Nzg0NjU2.2XcqB5_TjBGcMZaLhx5ZlR8_ipa8Eg7nkdZlmFd9IKgg.onroVkwrmaaqt21JyE7FB86bLHzSoYShWmIPe0_ikOkg.JPEG%2FIMG_3482.jpg",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20221101_212%2F1667270782020li7EN_JPEG%2F120DF262-297D-4106-ABCE-9EB6151D813D.jpeg",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20231219_34%2F17029518438085KQsu_JPEG%2FKakaoTalk_20231219_105342959_01.jpg",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20200528_267%2F1590600373193zyGKj_JPEG%2FzNGTp65et7CcJ1Y9KbM5dBYz.jpeg",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20200528_14%2F1590600402811mSCTR_JPEG%2FOO_nA6AqeCCHPzo7fh_nLPyM.jpeg",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20200528_266%2F1590600450791uBppr_JPEG%2FLlF8rBcdqFl3TcxENrnrLazy.jpeg",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20230217_173%2F16766432188872d7mg_JPEG%2F80754A02-602D-43FC-9ECC-4C6BD228607B.jpeg",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20201119_50%2F1605760862919Fv5fy_JPEG%2Fd9ijAjrK4T-Znnv3scm1LRrW.jpg",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20241104_166%2F17307293832241lBlO_JPEG%2F5E664C69-438A-44D3-9091-1A378F569A87.jpeg",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20241102_53%2F1730532250125MY93g_JPEG%2F1D55965C-1C9A-4BA0-8E7C-ED9086DF7AB8.jpeg",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20240530_80%2F1717062183563lp1Pq_JPEG%2F%25C5%25BE%25B3%25D7%25C0%25CF-%25C3%25B9%25B9%25E6%25B9%25AE-%25B9%25E8%25B3%25CA.jpg",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20240229_287%2F17091847160170kBIY_JPEG%2F%25B3%25D7%25C0%25CF%25B9%25D9%25BB%25E7%25C1%25F82.jpg",
    "https://search.pstatic.net/common/?src=http%3A%2F%2Fblogfiles.naver.net%2FMjAyNDAzMTRfMjM5%2FMDAxNzEwMzkwMDczNzky.w3y7eCF7lj7GA_Np_pBdzefHSPzCOQspdqU1GQ0MykIg.VDEE0Eupjn4llDsc9MQD6y3IOBv-GauPE7Scmrs3SHMg.JPEG%2FIMG_0878.jpg",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20240229_65%2F17091847260680vLb3_JPEG%2F%25C5%25D7%25B6%25F3%25BD%25BA_%25BB%25E7%25C1%25F81.jpg",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20240229_200%2F1709184617878P0mFW_JPEG%2F%25C6%25D0%25B5%25F0%25B9%25D9%25BB%25E7%25C1%25F8.jpg",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20240305_230%2F1709612334292Svyn5_JPEG%2FKakaoTalk_20240304_140259785_09.jpg",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20201203_157%2F1606974887161dcxCk_JPEG%2FamfZokK7-2NX8vcNg0Lb7CB0.jpg",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20231219_7%2F1702951886781KpOuh_JPEG%2FKakaoTalk_20231205_100423258.jpg",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fpup-review-phinf.pstatic.net%2FMjAyNDA5MDVfMTA2%2FMDAxNzI1NTMxODA4ODcx.ISVxnoqrTwMtDk2KNAPMUGOePKc19olZ92bIO56-7o0g.bhfAnHijwZv15Uhl1sW-HxTFV-WyhUuIWmMMWYf0A3Ug.JPEG",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20241107_272%2F17309481048935TQ1f_JPEG%2F1000018784.jpg",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20241107_38%2F1730948105917sMRD5_JPEG%2F1000018793.jpg",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20231219_199%2F1702951884459LuoGh_PNG%2FKakaoTalk_20231219_105342959_04.png",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fnaverbooking-phinf.pstatic.net%2F20240214_51%2F1707899945783NxFQ6_JPEG%2F2423432.jpg",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20241030_150%2F1730265183238NfEjI_JPEG%2FIMG_1396_polarr.jpeg",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20241030_150%2F1730265183238NfEjI_JPEG%2FIMG_1396_polarr.jpeg",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20241006_266%2F17282266086895a2np_JPEG%2F1000001970.jpg",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20240605_96%2F1717590976993QiQQi_JPEG%2FIMG_20240520_195151_241.jpg",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20210819_260%2F1629359192631zujpz_JPEG%2FSk05wYiM2DryU5vq8q_Vxruy.jpg",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20240402_151%2F1712044268642XU07o_JPEG%2F20240303_111006.jpg",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20221011_159%2F1665489406828WHc3e_JPEG%2FIMG_20220924_190856_693.jpg",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20240402_143%2F1712044153815cxW6R_JPEG%2FIMG_20240326_124241_719.jpg",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20240402_89%2F17120441408529M5mn_JPEG%2FIMG_20240401_173740_413.jpg",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20230515_121%2F1684135158278cj5VW_JPEG%2F20230514_211340_081.jpg",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20230615_238%2F1686813469065hUCSp_JPEG%2F20230604_160947.jpg",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20220506_113%2F16518314668038q3cl_JPEG%2FIMG_20220501_195608_010.jpg",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20220526_161%2F1653566345321vnHkW_JPEG%2F20220526_164359_435.jpg",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20240307_175%2F1709819022147jCrar_JPEG%2FIMG_8726.jpeg",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20240307_31%2F1709818516831udmJt_JPEG%2FIMG_1006.jpeg",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20221222_85%2F167170402489200pSn_JPEG%2F18EB63E3-5171-4141-BAD6-51BADCD555AB.jpeg",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20230109_191%2F1673276212130rJScg_JPEG%2Fimage.jpg",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20240226_61%2F1708875380856IPJhn_JPEG%2FIMG_7595.jpeg",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20211212_31%2F1639305051992j7zXt_JPEG%2FA9F0F886-741F-4933-B633-584B375482C8.jpeg",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20211212_180%2F1639312453046ovyiz_JPEG%2FDFBD4042-4EE4-4018-A45D-06B0C2E225AD.jpeg",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20241101_5%2F1730449408832zfYST_PNG%2F1000028179.png",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20240610_30%2F1717996920830sokp3_JPEG%2FKakaoTalk_20240507_173544862_22.jpg",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20240610_135%2F17179969934362n5uA_JPEG%2FKakaoTalk_20240529_120920559.jpg",
    "https://search.pstatic.net/common/?src=http%3A%2F%2Fblogfiles.naver.net%2FMjAyNDExMDRfODMg%2FMDAxNzMwNzA4Mjc1MTU2.DdSw9s_45GdF-3wTRD3p5iAsUAmn9MFVh01fOJCVI3wg.mD2GIuH3z6_XuUGUtgZp4RYUs8bSQ5njKe-34ojEFdYg.JPEG%2FKakaoTalk_20241022_122232119_03.jpg",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20240610_4%2F1717996957282I1BNi_JPEG%2FKakaoTalk_20240507_173610466_01.jpg",
    "https://search.pstatic.net/common/?src=http%3A%2F%2Fblogfiles.naver.net%2FMjAyNDEwMjRfNTUg%2FMDAxNzI5NzQ1NzcyMjE4.UdKyn_1S5nrn_RCWUalW1_B-1ps07fEQ-H_CK4yZBqcg.kpfd91EOeuwfRiq2iyXnPsPneyjU-MhDz2XEmDxlS7sg.JPEG%2FKakaoTalk_20241015_115424621_01.jpg",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20240610_75%2F1717996888092uQTU7_JPEG%2FKakaoTalk_20240610_141327147_09.jpg",
    "https://search.pstatic.net/common/?src=https%3A%2F%2Fldb-phinf.pstatic.net%2F20240421_116%2F1713675969134bD5XE_JPEG%2F%25B0%25A1%25B0%25DD%25C7%25A5.jpg",
]

# print(len(image_urls))

# URL 리스트와 shop_id 매칭하여 일괄 업데이트
for i, url in enumerate(image_urls, start=1):
    try:
        shop = Shops.objects.get(shop_id=i)  # shop_id가 i인 Shops 객체 가져오기
        shop.shop_url = url  # shop_url 필드에 URL 설정
        shop.save()
        print(f"Updated shop_id {i} with URL {url}")
    except Shops.DoesNotExist:
        print(f"Shop with ID {i} not found.")
