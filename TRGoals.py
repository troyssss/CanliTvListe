from Kekik.cli import konsol
from httpx import Client
from parsel import Selector
import re

class TRGoals:
    def __init__(self, m3u_dosyasi):
        self.m3u_dosyasi = m3u_dosyasi
        self.httpx = Client(timeout=10, verify=False)

    def referer_domainini_al(self):
        referer_deseni = r'#EXTVLCOPT:http-referrer=(https?://[^/]*trgoals[^/]*\.[^\s/]+)'
        with open(self.m3u_dosyasi, "r") as dosya:
            icerik = dosya.read()

        if eslesme := re.search(referer_deseni, icerik):
            return eslesme[1]
        else:
            raise ValueError("M3U dosyasında 'trgoals' içeren referer domain bulunamadı!")

    def guncel_trgoals_domaini_al(self):
        try:
            response = self.httpx.get("https://redirect-09385010482752.pages.dev", follow_redirects=True)
            # Son yönlendirme adresini al
            return str(response.url).strip("/")
        except Exception as e:
            raise ValueError(f"redirect-09385010482752.pages.dev üzerinden domain alınamadı: {e}")

    def m3u_guncelle(self):
        eldeki_domain = self.referer_domainini_al()
        konsol.log(f"[yellow][~] Bilinen Domain : {eldeki_domain}")

        yeni_domain = self.guncel_trgoals_domaini_al()
        konsol.log(f"[green][+] Yeni Domain    : {yeni_domain}")
        
        # Eğer yeni domain bir yönlendirme adresiyse, gerçek domaini çek
        if "redirect-09385010482752.pages.dev" in yeni_domain:
            try:
                response = self.httpx.get(yeni_domain, follow_redirects=True)
                yeni_domain = str(response.url).strip("/")
                konsol.log(f"[green][+] Güncel Domain (redirect sonrası) : {yeni_domain}")
                # Eğer hala yönlendirme adresindeysek, meta refresh ile yeni domaini bulmayı dene
                if "redirect-09385010482752.pages.dev" in yeni_domain:
                    meta_refresh = re.search(r'<meta[^>]+http-equiv=["\']refresh["\'][^>]+content=["\'][^;]+;URL=\s*`?([^"\'>`]+)', response.text, re.IGNORECASE)
                    if meta_refresh:
                        yeni_domain = meta_refresh.group(1).strip("` ")
                        konsol.log(f"[green][+] Meta Refresh ile Bulunan Domain : {yeni_domain}")
            except Exception as e:
                raise ValueError(f"Redirect sonrası domain alınamadı: {e}")

        kontrol_url = f"{yeni_domain}/channel.html?id=yayin1"

        with open(self.m3u_dosyasi, "r") as dosya:
            m3u_icerik = dosya.read()

        if not (eski_yayin_url := re.search(r'https?:\/\/[^\/]+\.(workers\.dev|shop|click)\/?', m3u_icerik)):
            raise ValueError("M3U dosyasında eski yayın URL'si bulunamadı!")

        eski_yayin_url = eski_yayin_url[0]
        konsol.log(f"[yellow][~] Eski Yayın URL : {eski_yayin_url}")

        response = self.httpx.get(kontrol_url, follow_redirects=True)

        if not (yayin_ara := re.search(r'var baseurl = "(https?:\/\/[^"]+)"', response.text)):
            # Alternatif olarak, tek tırnak veya boşluklu tanımlamaları da ara
            yayin_ara = re.search(r'var baseurl\s*=\s*["\'](https?:\/\/[^"]+)["\']', response.text)
            if not yayin_ara:
                # HTML içeriğinde baseurl geçen bir link veya script etiketi var mı kontrol et
                baseurl_html = re.search(r'(https?:\/\/[\w\.-]+\.(workers\.dev|shop|click)\/)', response.text)
                if baseurl_html:
                    yayin_ara = [None, baseurl_html.group(1)]
            if not yayin_ara:
                secici = Selector(response.text)
                baslik = secici.xpath("//title/text()").get()
                if baslik == "404 Not Found":
                    yayin_ara = [None, eski_yayin_url]
                else:
                    konsol.print(response.text)
                    raise ValueError("Base URL bulunamadı!")

        yayin_url = yayin_ara[1] if yayin_ara else eski_yayin_url
        konsol.log(f"[green][+] Yeni Yayın URL : {yayin_url}")

        yeni_m3u_icerik = m3u_icerik.replace(eski_yayin_url, yayin_url)
        yeni_m3u_icerik = yeni_m3u_icerik.replace(eldeki_domain, yeni_domain)

        with open(self.m3u_dosyasi, "w") as dosya:
            dosya.write(yeni_m3u_icerik)

if __name__ == "__main__":
    guncelleyici = TRGoals("Kanallar/kerim.m3u")
    guncelleyici.m3u_guncelle()
