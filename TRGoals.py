# Bu araç @keyiflerolsun tarafından | @KekikAkademi için yazılmıştır.

from Kekik.cli import konsol
from httpx     import Client
from parsel    import Selector
import re

class MonotvYayinGuncelleyici:
    def __init__(self, m3u_dosyasi):
        self.m3u_dosyasi = m3u_dosyasi
        self.httpx       = Client(timeout=10, verify=False)

    def referer_domainini_al(self):
        referer_deseni = r'#EXTVLCOPT:http-referrer=(https?://[^/]+)'
        with open(self.m3u_dosyasi, "r") as dosya:
            icerik = dosya.read()
        if eslesme := re.search(referer_deseni, icerik):
            return eslesme[1]
        else:
            raise ValueError("M3U dosyasında referer domain bulunamadı!")

    def yayin_urlini_bul(self, domain: str, kanal_id: str = "yayin1"):
        url = f"{domain}/channel.html?id={kanal_id}"
        konsol.log(f"[cyan][~] Kanal Sayfası: {url}")
        response = self.httpx.get(url, follow_redirects=True)

        if not (yayin_eslesme := re.search(r'var baseurl = "(https?://[^"]+)"', response.text)):
            secici = Selector(response.text)
            baslik = secici.xpath("//title/text()").get()
            if baslik == "404 Not Found":
                raise ValueError("Sayfa bulunamadı.")
            else:
                konsol.print(response.text)
                raise ValueError("Yayın URL'si bulunamadı!")

        return yayin_eslesme[1]

    def eski_yayin_urlini_bul(self, icerik: str) -> str:
        if not (eski := re.search(r'https?:\/\/[^\/]+\.(workers\.dev|shop|click)\/[^\s"]+', icerik)):
            raise ValueError("Eski yayın URL'si bulunamadı!")
        return eski[0]

    def m3u_guncelle(self):
        domain = self.referer_domainini_al()
        konsol.log(f"[yellow][~] Referer Domain : {domain}")

        with open(self.m3u_dosyasi, "r") as dosya:
            m3u_icerik = dosya.read()

        eski_yayin_url = self.eski_yayin_urlini_bul(m3u_icerik)
        konsol.log(f"[yellow][~] Eski Yayın URL  : {eski_yayin_url}")

        yeni_yayin_url = self.yayin_urlini_bul(domain)
        konsol.log(f"[green][+] Yeni Yayın URL  : {yeni_yayin_url}")

        yeni_m3u_icerik = m3u_icerik.replace(eski_yayin_url, yeni_yayin_url)
        with open(self.m3u_dosyasi, "w") as dosya:
            dosya.write(yeni_m3u_icerik)

if __name__ == "__main__":
    guncelleyici = MonotvYayinGuncelleyici("Kanallar/kerim.m3u")
    guncelleyici.m3u_guncelle()
