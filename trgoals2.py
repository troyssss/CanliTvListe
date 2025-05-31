

from Kekik.cli import konsol
from httpx     import Client
from parsel    import Selector
import re
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

class TRGoals:
    def __init__(self, m3u_dosyasi):
        self.m3u_dosyasi = m3u_dosyasi
        self.httpx       = Client(timeout=10, verify=False)

    def referer_domainini_al_original(self): 
        referer_deseni = r'#EXTVLCOPT:http-referrer=(https?://[^/]*trgoals[^/]*\.[^\s/]+)'
        with open(self.m3u_dosyasi, "r", encoding="utf-8") as dosya:
            icerik = dosya.read()

        if eslesme := re.search(referer_deseni, icerik):
            return eslesme[1]
        else:
            raise ValueError("M3U dosyasında '#EXTVLCOPT:http-referrer' ile 'trgoals' içeren referer domain bulunamadı!")

    def trgoals_domaini_al(self):
        redirect_url = "https://bit.ly/m/taraftarium24w"
        deneme = 0
        while "bit.ly" in redirect_url and deneme < 5:
            try:
                redirect_url = self.redirect_gec(redirect_url)
            except Exception as e:
                konsol.log(f"[red][!] redirect_gec hata: {e}")
                break
            deneme += 1

        if "bit.ly" in redirect_url or "error" in redirect_url:
            konsol.log("[yellow][!] 5 denemeden sonra bit.ly çözülemedi, yedek linke geçiliyor...")
            try:
                redirect_url = self.redirect_gec("https://t.co/aOAO1eIsqE") 
            except Exception as e:
                
                raise ValueError(f"Yedek linkten de domain alınamadı: {e}")

        return redirect_url

    def redirect_gec(self, redirect_url: str):
        konsol.log(f"[cyan][~] redirect_gec çağrıldı: {redirect_url}")
        try:
            response = self.httpx.get(redirect_url, follow_redirects=True)
            response.raise_for_status() 
        except Exception as e:
            raise ValueError(f"Redirect sırasında hata oluştu ({redirect_url}): {e}")

        tum_url_listesi = [str(r.url) for r in response.history] + [str(response.url)]

        for url in tum_url_listesi[::-1]:
            if "trgoals" in url:
                return url.strip("/")

        raise ValueError(f"Redirect zincirinde ({redirect_url}) 'trgoals' içeren bir link bulunamadı! Son URL: {response.url}")

    def yeni_domaini_al(self, eldeki_domain: str) -> str:
        def check_domain(domain: str) -> str:
            if domain == "https://trgoalsgiris.xyz": 
                raise ValueError("Yeni domain alınamadı (trgoalsgiris.xyz döndü)")
            return domain

        try:
            yeni_domain = check_domain(self.redirect_gec(eldeki_domain))
        except Exception as e1:
            konsol.log(f"[red][!] `redirect_gec('{eldeki_domain}')` fonksiyonunda hata oluştu: {e1}")
            try:
                yeni_domain = check_domain(self.trgoals_domaini_al())
            except Exception as e2:
                konsol.log(f"[red][!] `trgoals_domaini_al()` fonksiyonunda hata oluştu: {e2}")
                try:
                    yeni_domain = check_domain(self.redirect_gec("https://t.co/MTLoNVkGQN")) 
                except Exception as e3:
                    konsol.log(f"[red][!] `redirect_gec('https://t.co/MTLoNVkGQN')` fonksiyonunda hata oluştu: {e3}")
                    
                    try:
                        rakam_str = re.search(r'trgoals(\d+)', eldeki_domain)
                        if rakam_str:
                            rakam = int(rakam_str.group(1)) + 1
                            base_eldeki_domain = eldeki_domain.split("trgoals")[0]
                            domain_suffix = eldeki_domain.split(".")[-1]
                            yeni_domain = f"{base_eldeki_domain}trgoals{rakam}.{domain_suffix}"
                            konsol.log(f"[yellow][~] Son çare olarak domain üretildi: {yeni_domain}")
                        else:
                            raise ValueError("Eldeki domainden rakam çıkarılamadı.")
                    except Exception as e4:
                        konsol.log(f"[red][!] Domain üretme sırasında hata: {e4}")
                        raise ValueError("Tüm denemelere rağmen yeni trgoals domaini alınamadı.")
        return yeni_domain

    def m3u_guncelle(self):
        try:
            with open(self.m3u_dosyasi, "r", encoding="utf-8") as dosya:
                m3u_icerik = dosya.read()
        except FileNotFoundError:
            konsol.log(f"[red][!] M3U dosyası bulunamadı: {self.m3u_dosyasi}")
            return

        initial_trgoals_domain_found = None
        proxy_referer_pattern = re.compile(r'&referer=(https?://[^/]*trgoals[^/]*\.[^\s/&?]+)')
        
        for line in m3u_icerik.splitlines():
            if "/api/proxy.js?" in line and "&referer=" in line:
                match = proxy_referer_pattern.search(line)
                if match:
                    initial_trgoals_domain_found = match.group(1)
                    konsol.log(f"[cyan][~] Örnek eski TRGoals domain proxy URL'den bulundu: {initial_trgoals_domain_found}")
                    break
        
        if not initial_trgoals_domain_found:
            try:
                initial_trgoals_domain_found = self.referer_domainini_al_original()
                konsol.log(f"[cyan][~] Örnek eski TRGoals domain #EXTVLCOPT'den bulundu: {initial_trgoals_domain_found}")
            except ValueError as e:
                konsol.log(f"[red][!] Başlangıç TRGoals domaini bulunamadı: {e}")
                konsol.log("[yellow][!] Güncelleme yapılamıyor. M3U dosyasında proxy formatında URL veya #EXTVLCOPT ile tanımlanmış bir TRGoals domaini olmalı.")
                return

        konsol.log(f"[yellow][~] Güncelleme için temel alınan TRGoals Domain: {initial_trgoals_domain_found}")

        try:
            yeni_trgoals_domain = self.yeni_domaini_al(initial_trgoals_domain_found)
            konsol.log(f"[green][+] Yeni TRGoals Referer Domain: {yeni_trgoals_domain}")
        except ValueError as e:
            konsol.log(f"[red][!] Yeni TRGoals domaini alınamadı: {e}. Referer güncellenmeyecek.")
            yeni_trgoals_domain = initial_trgoals_domain_found 

        kontrol_url = f"{yeni_trgoals_domain}/channel.html?id=yayin1"
        yeni_stream_domain = None
        try:
            response = self.httpx.get(kontrol_url, follow_redirects=True)
            response.raise_for_status()
            if baseurl_match := re.search(r'(?:var|let|const)\s+baseurl\s*=\s*"(https?://[^"/]+(?:/[^"/]*)?)"', response.text): 
                yeni_stream_domain = baseurl_match.group(1).strip("/")
                konsol.log(f"[green][+] Yeni Yayın (Stream) Domain/Base: {yeni_stream_domain}")
            else:
                secici = Selector(response.text)
                baslik = secici.xpath("//title/text()").get()
                if baslik and "404 Not Found" in baslik:
                    konsol.log(f"[yellow][!] Kontrol URL ({kontrol_url}) 404 verdi. Yayın domaini güncellenmeyecek.")
                else:
                    konsol.log(f"[red][!] Kontrol URL ({kontrol_url}) içeriğinden baseurl bulunamadı. Yanıt (ilk 500 karakter):")
                    konsol.log(response.text[:500] + ("..." if len(response.text) > 500 else ""))
        except Exception as e:
            konsol.log(f"[red][!] Yeni yayın domaini/base alınırken hata ({kontrol_url}): {e}")

        updated_m3u_lines = []
        changed_count = 0
        for line_num, line in enumerate(m3u_icerik.splitlines()):
            original_line = line
            updated_line = line

            if "/api/proxy.js?url=" in line and "&referer=" in line:
                try:
                    proxy_url_parts = urlparse(line)
                    proxy_qs_params = parse_qs(proxy_url_parts.query, keep_blank_values=True)
                    
                    original_stream_url_list = proxy_qs_params.get('url')
                    original_referer_url_list = proxy_qs_params.get('referer')

                    if not (original_stream_url_list and original_referer_url_list):
                        updated_m3u_lines.append(line)
                        continue

                    current_stream_url = original_stream_url_list[0]
                    current_referer_url = original_referer_url_list[0]
                    
                    
                    if "trgoals" in current_referer_url and yeni_stream_domain:
                        stream_url_parts = urlparse(current_stream_url)
                        new_stream_domain_parts = urlparse(yeni_stream_domain)
                        updated_stream_url_parts = stream_url_parts._replace(
                            scheme=new_stream_domain_parts.scheme or stream_url_parts.scheme,
                            netloc=new_stream_domain_parts.netloc
                        )
                        new_full_stream_url = urlunparse(updated_stream_url_parts)
                    else:
                        new_full_stream_url = current_stream_url 
                    
                    
                    if "trgoals" in current_referer_url:
                        new_full_referer_url = yeni_trgoals_domain
                    else:
                        new_full_referer_url = current_referer_url 

                    proxy_qs_params['url'] = [new_full_stream_url]
                    proxy_qs_params['referer'] = [new_full_referer_url]
                    
                    new_proxy_query_string = urlencode(proxy_qs_params, doseq=True, safe=':/')
                    updated_line = urlunparse(proxy_url_parts._replace(query=new_proxy_query_string))
                    
                except Exception as e:
                    konsol.log(f"[red][!] Satır {line_num+1} proxy URL işlenirken hata: {line} - Hata: {e}")
                    updated_line = original_line 
            
            elif line.startswith("#EXTVLCOPT:http-referrer=") and "trgoals" in line:
                current_extvlcopt_referer_match = re.search(r'#EXTVLCOPT:http-referrer=(https?://[^/]*trgoals[^/]*\.[^\s/]+)', line)
                if current_extvlcopt_referer_match:
                    old_extvlcopt_referer = current_extvlcopt_referer_match.group(1)
                    if old_extvlcopt_referer != yeni_trgoals_domain:
                        updated_line = line.replace(old_extvlcopt_referer, yeni_trgoals_domain)
            
            if updated_line != original_line:
                konsol.log(f"[blue][~] Eski ({line_num+1}): {original_line}")
                konsol.log(f"[green][+] Yeni ({line_num+1}): {updated_line}")
                changed_count +=1
            updated_m3u_lines.append(updated_line)

        if changed_count > 0:
            yeni_m3u_icerik = "\n".join(updated_m3u_lines)
            if m3u_icerik.endswith('\n') and not yeni_m3u_icerik.endswith('\n'):
                yeni_m3u_icerik += '\n'

            try:
                with open(self.m3u_dosyasi, "w", encoding="utf-8") as dosya:
                    dosya.write(yeni_m3u_icerik)
                konsol.log(f"[green][✓] M3U dosyası {self.m3u_dosyasi} başarıyla güncellendi. {changed_count} değişiklik yapıldı.")
            except Exception as e:
                konsol.log(f"[red][!] M3U dosyası yazılırken hata: {e}")
        else:
            konsol.log("[yellow][!] M3U dosyasında güncelleme yapılacak bir URL bulunamadı veya URL'ler zaten güncel.")

if __name__ == "__main__":
    guncelleyici = TRGoals("subatv.m3u") 
    guncelleyici.m3u_guncelle()
