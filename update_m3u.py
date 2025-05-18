import re
import os

MANUEL_ID_LISTESI = {
    "3002": None,
    "1908": None,
    "2213": None,
    "3304": None,
    "1911": None,
    "2602": None,
    "1110": None,
    "1109": None,
    "2212": None,
    "2608": None,
    "2404": None,
    "2703": None,
    "3715": None,
    "1314": None,
    "2601": None,
    "3601": None,
    "1608": None,
    "1610": None,
    "2506": None,
    "2704": None,
    "3802": None,
    "3803": None,
    "3801": None,
    "1616": None,
    "2003": None,
    "2310": None,
    "2114": None,
    "3903": None,
    "2002": None,
    "1809": None,
    "1810": None,
    "3901": None
}

def parse_m3u(file_path):
    kanallar = {}
    mevcut_id = None

    with open(file_path, 'r', encoding='utf-8') as f:
        for satir in f:
            satir = satir.strip()
            if satir.startswith('#EXTINF'):
                eslesme = re.search(r'tvg-id="([^"]+)"', satir)
                mevcut_id = eslesme.group(1) if eslesme else None
            elif satir and not satir.startswith('#') and mevcut_id:
                kanallar[mevcut_id] = satir
                mevcut_id = None
    return kanallar


def update_m3u_file(dosya_adi, yeni_kanallar):
    if not os.path.exists(dosya_adi):
        print(f"{dosya_adi} bulunamadı. Yeni oluşturuluyor...")
        with open(dosya_adi, 'w', encoding='utf-8') as f:
            f.write("#EXTM3U\n")

    with open(dosya_adi, 'r', encoding='utf-8') as f:
        satirlar = f.readlines()

    guncellenmis = []
    i = 0
    while i < len(satirlar):
        satir = satirlar[i].strip()
        guncellenmis.append(satirlar[i])

        if satir.startswith('#EXTINF'):
            eslesme = re.search(r'tvg-id="([^"]+)"', satir)
            kanal_id = eslesme.group(1) if eslesme else None

            if kanal_id in MANUEL_ID_LISTESI and i + 1 < len(satirlar):
                eski_url = satirlar[i + 1].strip()
                yeni_url = yeni_kanallar.get(kanal_id)

                i += 1
                if yeni_url and eski_url != yeni_url:
                    print(f"🔁 {kanal_id} güncellendi ({dosya_adi}).")
                    guncellenmis.append(yeni_url + '\n')
                else:
                    guncellenmis.append(satirlar[i])
            elif i + 1 < len(satirlar):
                i += 1
                guncellenmis.append(satirlar[i])
        i += 1

    with open(dosya_adi, 'w', encoding='utf-8') as f:
        f.writelines(guncellenmis)

    print(f"✅ {dosya_adi} başarıyla güncellendi!")


def update_all_m3u():
    yeni_kanallar = parse_m3u('yeni.m3u')
    update_m3u_file('subatv.m3u', yeni_kanallar)
    update_m3u_file('Kanallar/kerim.m3u', yeni_kanallar)


if __name__ == "__main__":
    update_all_m3u()  
