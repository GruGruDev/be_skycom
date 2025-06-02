import json

import requests
import unidecode

from .models import Districts, Provinces, Wards


def get_vtpost_province_id():
    province_url = "https://partner.viettelpost.vn/v2/categories/listProvinceById?provinceId=0"
    try:
        response = requests.get(province_url)
        vtpost_provinces = response.json()
    except Exception:
        vtpost_provinces = None
    provinces = Provinces.objects.all()
    province_list = []

    if vtpost_provinces:
        for province in provinces:
            for vtpost_province in vtpost_provinces["data"]:
                unslug = province.slug.replace("-", "")
                if unslug == unidecode.unidecode(vtpost_province["PROVINCE_NAME"].replace(" ", "").replace("-", "").lower()):
                    province.vtpost_province_id = vtpost_province["PROVINCE_ID"]
                    province_list.append(province)

        Provinces.objects.bulk_update(province_list, batch_size=2000, fields=["vtpost_province_id"])

special_district_vtpost_mapping = {
    "318": ("60", "3"),
    "666": ("117", "9"),
    "654": ("525", "45"),
    "317": ("66", "3"),
    "602": ("586", "52"),
    "540": ("464", "40"),
}

def get_vtpost_district_id():
    district_url = "https://partner.viettelpost.vn/v2/categories/listDistrict?provinceId=-1"
    try:
        response = requests.get(district_url)
        vtpost_districts = response.json()
    except Exception:
        vtpost_districts = None
    districts = Districts.objects.prefetch_related("province").all()
    district_list = []

    if vtpost_districts:
        for district in districts:
            for vtpost_district in vtpost_districts["data"]:
                unslug = district.label.replace(" ", "").replace("-", "").lower() + str(district.province.vtpost_province_id)
                unslug_vtpost = vtpost_district["DISTRICT_NAME"].replace(" ", "").replace("-", "").lower() + str(vtpost_district["PROVINCE_ID"])
                if str(district.code) in special_district_vtpost_mapping:
                    special_vtpost_district, special_vtpost_province = special_district_vtpost_mapping.get(str(district.code))
                    district.vtpost_district_id = special_vtpost_district
                    district.vtpost_province_id = special_vtpost_province
                    district_list.append(district)
                elif unidecode.unidecode(unslug) == unidecode.unidecode(unslug_vtpost):
                    district.vtpost_district_id = vtpost_district["DISTRICT_ID"]
                    district.vtpost_province_id = vtpost_district["PROVINCE_ID"]
                    district_list.append(district)

        Districts.objects.bulk_update(district_list, batch_size=2000, fields=["vtpost_province_id", "vtpost_district_id"])
        
        districts = Districts.objects.prefetch_related("province").filter(vtpost_district_id__isnull=True)
        if districts.exists():
            district_list = []
            for district in districts:
                for vtpost_district in vtpost_districts["data"]:
                    unslug_huyen = "huyen" + district.name.replace(" ", "").replace("-", "").lower() + str(district.province.vtpost_province_id)
                    unslug_thixa = "thixa" + district.name.replace(" ", "").replace("-", "").lower() + str(district.province.vtpost_province_id)
                    unslug_tp = "thanhpho" + district.name.replace(" ", "").replace("-", "").lower() + str(district.province.vtpost_province_id)
                    unslug_vtpost = vtpost_district["DISTRICT_NAME"].replace(" ", "").replace("-", "").lower() + str(vtpost_district["PROVINCE_ID"])
                    arr = [unidecode.unidecode(unslug_huyen), unidecode.unidecode(unslug_thixa), unidecode.unidecode(unslug_tp)]
                    if unidecode.unidecode(unslug_vtpost) in arr:
                        district.vtpost_district_id = vtpost_district["DISTRICT_ID"]
                        district.vtpost_province_id = vtpost_district["PROVINCE_ID"]
                        district_list.append(district)

            Districts.objects.bulk_update(district_list, batch_size=2000, fields=["vtpost_province_id", "vtpost_district_id"])

special_vtpost_ward_mapping = {
    "06616": ("4158", "238", "22"),
    "03244": ("11758", "717", "64"),
    "19114": ("7659", "402", "35"),
    "02902": ("3844", "222", "20"),
    "23707": ("9006", "498", "44"),
    "23344": ("8918", "492", "43"),
    "04136": ("5710", "316", "30"),
    "03460": ("5608", "310", "29"),
    "02431": ("4246", "243", "23"),
    "23671": ("9074", "503", "44"),
    "03177": ("11706", "713", "64"),
    "24700": ("1635", "114", "9"),
    "25819": ("9801", "568", "50"),
    "14863": ("6529", "353", "32"),
    "24826": ("9466", "535", "46"),
    "03454": ("5581", "308", "29"),
    "03772": ("5739", "318", "30"),
    "05245": ("6044", "334", "31"),
    "25231": ("9674", "555", "48"),
    "24079": ("8965", "495", "44"),
    "25438": ("9617", "549", "48"),
    "02683": ("3726", "217", "20"),
    "13141": ("3094", "181", "16"),
    "20707": ("8025", "426", "38"),
    "13459": ("18477", "160", "14"),
    "24160": ("9228", "515", "45"),
    "25060": ("9358", "527", "46"),
    "24397": ("9192", "514", "45"),
    "04225": ("5831", "323", "30"),
    "23335": ("8883", "488", "43"),
    "03223": ("11759", "717", "64"),
    "23536": ("8843", "485", "43"),
    "04222": ("5673", "314", "30"),
    "05722": ("4637", "260", "25"),
    "24694": ("1640", "114", "9"),
    "14896": ("6562", "355", "32"),
    "03371": ("11681", "711", "64"),
    "24226": ("9273", "520", "45"),
    "00067": ("11", "1", "1"),
    "26257": ("9866", "574", "51"),
    "20719": ("8021", "426", "38"),
    "20440": ("8095", "431", "38"),
    "01096": ("3340", "194", "18"),
    "23140": ("10160", "592", "52"),
    "19246": ("7525", "396", "35"),
    "30259": ("10550", "623", "55"),
    "03226": ("11762", "717", "64"),
    "05392": ("5866", "325", "31"),
    "24430": ("9303", "522", "45"),
    "24103": ("8952", "495", "44"),
    "23800": ("9101", "505", "44"),
    "00796": ("3432", "199", "18"),
    "23404": ("8851", "486", "43"),
    "09724": ("319", "15", "1"),
    "12664": ("2907", "176", "16"),
    "23647": ("9068", "503", "44"),
    "03466": ("5579", "308", "29"),
    "25117": ("9408", "530", "46"),
    "32131": ("11540", "700", "63"),
    "24955": ("9478", "536", "46"),
    "03982": ("25661", "319", "30"),
    "23395": ("8907", "490", "43"),
    "24388": ("9199", "514", "45"),
    "30985": ("11088", "659", "59"),
    "24973": ("9492", "537", "46"),
    "23929": ("8936", "494", "44"),
    "02068": ("3874", "224", "21"),
    "25099": ("9403", "530", "46"),
    "03892": ("5828", "322", "30"),
    "25907": ("9812", "569", "50"),
    "02848": ("3782", "219", "20"),
    "23942": ("9128", "508", "44"),
    "23353": ("8928", "492", "43"),
    "12538": ("2888", "175", "16"),
    "31346": ("1533", "103", "8"),
    "23827": ("9085", "504", "44"),
    "23806": ("9093", "505", "44"),
    "29143": ("10925", "650", "58"),
    "25057": ("9360", "527", "46"),
    "18871": ("7557", "398", "35"),
    "12982": ("3031", "180", "16"),
    "15037": ("6289", "343", "32"),
    "00898": ("3285", "191", "18"),
    "04075": ("5788", "320", "30"),
    "30502": ("10742", "638", "56"),
    "01978": ("3949", "228", "21"),
    "24031": ("9120", "507", "44"),
    "16763": ("6826", "369", "33"),
    "26308": ("9904", "576", "51"),
    "24850": ("9353", "526", "46"),
    "31115": ("11232", "672", "59"),
    "23413": ("8854", "486", "43"),
    "24274": ("9263", "518", "45"),
    "23794": ("9091", "505", "44"),
    "23660": ("9073", "503", "44"),
    "22093": ("8649", "471", "41"),
    "24727": ("1649", "115", "9"),
    "24065": ("9154", "510", "44"),
    "23938": ("8938", "494", "44"),
    "23317": ("8886", "488", "43"),
    "02836": ("3811", "220", "20"),
    "20458": ("8094", "431", "38"),
    "21631": ("8484", "460", "40"),
    "06553": ("4099", "236", "22"),
    "03010": ("3688", "215", "20"),
    "29218": ("11018", "655", "58"),
    "24064": ("9153", "510", "44"),
    "14848": ("6530", "353", "32"),
    "24949": ("9477", "536", "46"),
    "06313": ("3984", "231", "22"),
    "29929": ("10501", "619", "55"),
    "24289": ("9259", "518", "45"),
    "24928": ("9481", "536", "46"),
    "09781": ("305", "15", "1"),
    "25398": ("9647", "552", "48"),
    "03697": ("5629", "312", "30"),
    "23535": ("8930", "493", "43"),
    "24640": ("1631", "113", "9"),
    "01102": ("3342", "194", "18"),
    "03391": ("5535", "305", "29"),
    "19477": ("7728", "406", "36"),
    "20701": ("8026", "426", "38"),
    "01147": ("3339", "194", "18"),
    "31018": ("11233", "673", "59"),
    "02908": ("3838", "222", "20"),
    "28159": ("10317", "606", "54"),
    "23668": ("9067", "503", "44"),
    "24049": ("8970", "496", "44"),
    "01888": ("3953", "229", "21"),
    "03784": ("5757", "318", "30"),
    "23824": ("9077", "504", "44"),
    "00811": ("3435", "199", "18"),
    "03574": ("5526", "305", "29"),
    "24514": ("9335", "525", "45"),
    "24718": ("1647", "115", "9"),
    "01290": ("3577", "208", "19"),
    "23650": ("9070", "503", "44"),
    "16777": ("6785", "366", "33"),
    "01561": ("3485", "202", "19"),
    "01720": ("3596", "209", "19"),
    "24412": ("9306", "522", "45"),
    "19768": ("7968", "422", "37"),
    "02302": ("4311", "245", "23"),
    "02473": ("4251", "243", "23"),
    "05299": ("5987", "332", "31"),
    "05335": ("6013", "332", "31"),
    "10282": ("537", "27", "1"),
    "19603": ("7737", "408", "36"),
    "19756": ("7953", "422", "37"),
    "30265": ("10552", "623", "55"),
    "24505": ("9334", "525", "45"),
}

def get_vtpost_ward_id():
    ward_url = "https://partner.viettelpost.vn/v2/categories/listWards?districtId=-1"
    try:
        response = requests.get(ward_url)
        vtpost_wards = response.json()
    except Exception:
        vtpost_wards = None
    wards = Wards.objects.prefetch_related("district").all()
    ward_list = []
    vtpost_ward_mapping = {}
    for vtpost_ward in vtpost_wards["data"]: 
        lower_vtpost = vtpost_ward["WARDS_NAME"].replace(" ", "").replace("-", "").replace("'", "").lower() + str(vtpost_ward["DISTRICT_ID"])
        vtpost_ward_mapping[unidecode.unidecode(lower_vtpost)] = vtpost_ward

    if vtpost_wards:
        for ward in wards:
            special_lower_ward = None
            lower_ward = ward.type.replace(" ", "").replace("-", "").lower() +  ward.name.replace(" ", "").replace("-", "").lower() + str(ward.district.vtpost_district_id)
            if ward.name[0] == "0":
                special_lower_ward = ward.type.replace(" ", "").replace("-", "").lower() +  ward.name[1:].replace(" ", "").replace("-", "").lower() + str(ward.district.vtpost_district_id)
            if unidecode.unidecode(lower_ward) in vtpost_ward_mapping or (special_lower_ward and unidecode.unidecode(special_lower_ward) in vtpost_ward_mapping):
                vtpost_ward = vtpost_ward_mapping.get(unidecode.unidecode(lower_ward)) if not special_lower_ward else vtpost_ward_mapping.get(unidecode.unidecode(special_lower_ward))
                ward.vtpost_ward_id = vtpost_ward["WARDS_ID"]
                ward.vtpost_district_id = vtpost_ward["DISTRICT_ID"]
                ward.vtpost_province_id = ward.district.vtpost_province_id
                ward_list.append(ward)

        Wards.objects.bulk_update(ward_list, batch_size=2000, fields=["vtpost_province_id", "vtpost_district_id", "vtpost_ward_id"])
        wards = Wards.objects.prefetch_related("district").filter(vtpost_ward_id__isnull=True)
        if wards.exists():
            ward_list = []
            for ward in wards:
                lower_ward = ward.name.replace(" ", "").replace("-", "").lower() + str(ward.district.vtpost_district_id)
                lower_ward_to_y = unidecode.unidecode(lower_ward).replace("i", "y")
                lower_ward_to_i = unidecode.unidecode(lower_ward).replace("y", "i")
                lower_ward_phuong = "phuong" +  ward.name.replace(" ", "").replace("-", "").lower() + str(ward.district.vtpost_district_id)
                lower_ward_xa = "xa" +  ward.name.replace(" ", "").replace("-", "").replace("'", "").lower() + str(ward.district.vtpost_district_id)
                lower_ward_thitran = "thitran" +  ward.name.replace(" ", "").replace("-", "").lower() + str(ward.district.vtpost_district_id)
                lower_ward_tt = "tt" +  ward.name.replace(" ", "").replace("-", "").lower() + str(ward.district.vtpost_district_id)
                lower_ward_kcn = "kcn" +  ward.name.replace(" ", "").replace("-", "").lower() + str(ward.district.vtpost_district_id)
                lower_ward_p = "p" +  ward.name.replace(" ", "").replace("-", "").lower() + str(ward.district.vtpost_district_id)
                lower_ward_1 = ward.type.replace(" ", "").replace("-", "").lower() +  ward.name.replace(" ", "").replace("-", "").replace("I", "1").lower() + str(ward.district.vtpost_district_id)
                lower_ward_2 = ward.type.replace(" ", "").replace("-", "").lower() +  ward.name.replace(" ", "").replace("-", "").replace("II", "2").lower() + str(ward.district.vtpost_district_id)
                lower_ward_3 = ward.type.replace(" ", "").replace("-", "").lower() +  ward.name.replace(" ", "").replace("-", "").replace("III", "3").lower() + str(ward.district.vtpost_district_id)
                lower_ward_4 = ward.type.replace(" ", "").replace("-", "").lower() +  ward.name.replace(" ", "").replace("-", "").replace("IV", "4").lower() + str(ward.district.vtpost_district_id)
                lower_ward_5 = ward.type.replace(" ", "").replace("-", "").lower() +  ward.name.replace(" ", "").replace("-", "").replace("V", "5").lower() + str(ward.district.vtpost_district_id)
                lower_ward_6 = ward.type.replace(" ", "").replace("-", "").lower() +  ward.name.replace(" ", "").replace("-", "").replace("VI", "6").lower() + str(ward.district.vtpost_district_id)
                lower_ward_7 = ward.type.replace(" ", "").replace("-", "").lower() +  ward.name.replace(" ", "").replace("-", "").replace("VII", "7").lower() + str(ward.district.vtpost_district_id)
                lower_ward_i = ward.type.replace(" ", "").replace("-", "").lower() +  ward.name.replace(" ", "").replace("-", "").replace("1", "I").lower() + str(ward.district.vtpost_district_id)
                lower_ward_ii = ward.type.replace(" ", "").replace("-", "").lower() +  ward.name.replace(" ", "").replace("-", "").replace("2", "II").lower() + str(ward.district.vtpost_district_id)
                lower_ward_iii = ward.type.replace(" ", "").replace("-", "").lower() +  ward.name.replace(" ", "").replace("-", "").replace("3", "III").lower() + str(ward.district.vtpost_district_id)
                vtpost_ward = (
                    vtpost_ward_mapping.get(unidecode.unidecode(lower_ward)) 
                    or vtpost_ward_mapping.get(unidecode.unidecode(lower_ward_phuong)) 
                    or vtpost_ward_mapping.get(unidecode.unidecode(lower_ward_xa)) 
                    or vtpost_ward_mapping.get(unidecode.unidecode(lower_ward_thitran))
                    or vtpost_ward_mapping.get(unidecode.unidecode(lower_ward_tt))
                    or vtpost_ward_mapping.get(unidecode.unidecode(lower_ward_kcn))
                    or vtpost_ward_mapping.get(unidecode.unidecode(lower_ward_1))
                    or vtpost_ward_mapping.get(unidecode.unidecode(lower_ward_2))
                    or vtpost_ward_mapping.get(unidecode.unidecode(lower_ward_3))
                    or vtpost_ward_mapping.get(unidecode.unidecode(lower_ward_4))
                    or vtpost_ward_mapping.get(unidecode.unidecode(lower_ward_5))
                    or vtpost_ward_mapping.get(unidecode.unidecode(lower_ward_6))
                    or vtpost_ward_mapping.get(unidecode.unidecode(lower_ward_7))
                    or vtpost_ward_mapping.get(unidecode.unidecode(lower_ward_i))
                    or vtpost_ward_mapping.get(unidecode.unidecode(lower_ward_ii))
                    or vtpost_ward_mapping.get(unidecode.unidecode(lower_ward_iii))
                    or vtpost_ward_mapping.get(unidecode.unidecode(lower_ward_p))
                    or vtpost_ward_mapping.get(lower_ward_to_y)
                    or vtpost_ward_mapping.get(lower_ward_to_i)
                )
                if vtpost_ward:
                    ward.vtpost_ward_id = vtpost_ward["WARDS_ID"]
                    ward.vtpost_district_id = vtpost_ward["DISTRICT_ID"]
                    ward.vtpost_province_id = ward.district.vtpost_province_id
                    ward_list.append(ward)
                elif str(ward.code) in special_vtpost_ward_mapping:
                    special_ward, special_district, special_province = special_vtpost_ward_mapping.get(str(ward.code))
                    ward.vtpost_ward_id = int(special_ward)
                    ward.vtpost_district_id = int(special_district)
                    ward.vtpost_province_id = int(special_province)
                    ward_list.append(ward)

            Wards.objects.bulk_update(ward_list, batch_size=2000, fields=["vtpost_province_id", "vtpost_district_id", "vtpost_ward_id"])