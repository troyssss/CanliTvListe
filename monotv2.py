import re
import urllib.parse
from httpx import Client
from Kekik.cli import konsol as log  

class MonoTV:
    def __init__(self, m3u_dosyasi):
        self.m3u_dosyasi = m3u_dosyasi
        self.httpx = Client(
            timeout=10,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122 Safari/537.36"
            }
        )

    def yayin_urlini_al(self):
        json_endpoint = "https://subatvdeneme.kerimmkirac.workers.dev/?url=https://royalvipcanlimac.com/domain.php&referer=https://royalvipcanlimac.com&proxy=hayir&useragent=okhttp%2F4.12.0"
        log.log(f"[cyan][~] domain.php çağrılıyor: {json_endpoint}")
        try:
            response = self.httpx.get(json_endpoint)
            json_data = response.json()
            yayin_url = json_data["baseurl"].replace("\\/", "/").rstrip("/")
            log.log(f"[green][+] Yayın URL bulundu: {yayin_url}")
            return yayin_url
        except Exception as e:
            raise ValueError(f"Yayın URL'si alınamadı: {e}")

    def m3u_guncelle(self):
        with open(self.m3u_dosyasi, "r", encoding="utf-8") as f:
            lines = f.readlines()

        yeni_ana_url_host = self.yayin_urlini_al() 

        degisti_mi = False
        yeni_lines = []
        guncellenen_sayisi = 0

        for line_num, line_content in enumerate(lines):
            line_content_stripped = line_content.strip()
            original_line = line_content
            if "verceldeneme-one.vercel.app/api/proxy.js" in line_content_stripped and "?url=" in line_content_stripped:
                try:
                    parsed_proxy_url = urllib.parse.urlparse(line_content_stripped)
                    query_params = urllib.parse.parse_qs(parsed_proxy_url.query)

                    if 'url' in query_params and query_params['url'] and 'referer' in query_params and query_params['referer'] and query_params['referer'][0].startswith('https://monotv'):
                        original_inner_url_str = query_params['url'][0]
                        parsed_inner_url = urllib.parse.urlparse(original_inner_url_str)
                        
                        new_inner_url_parts = list(parsed_inner_url)
                        parsed_new_host = urllib.parse.urlparse(yeni_ana_url_host)
                        new_inner_url_parts[1] = parsed_new_host.netloc 
                        
                        if not new_inner_url_parts[0] and parsed_new_host.scheme:
                            new_inner_url_parts[0] = parsed_new_host.scheme
                        elif not new_inner_url_parts[0] and not parsed_new_host.scheme:
                            if not parsed_inner_url.scheme:
                                new_inner_url_parts[0] = 'https'
                            else:
                                new_inner_url_parts[0] = parsed_inner_url.scheme 

                        updated_inner_url_str = urllib.parse.urlunparse(new_inner_url_parts)
                        query_params['url'] = [updated_inner_url_str]
                        
                        new_query_string = urllib.parse.urlencode(query_params, doseq=True, safe=':/')
                        
                        updated_proxy_url_str = urllib.parse.urlunparse((
                            parsed_proxy_url.scheme,
                            parsed_proxy_url.netloc,
                            parsed_proxy_url.path,
                            parsed_proxy_url.params,
                            new_query_string,
                            parsed_proxy_url.fragment
                        ))

                        if line_content_stripped != updated_proxy_url_str:
                            log.log(f"[blue]• Güncellendi (Satır {line_num + 1}): {line_content_stripped} → {updated_proxy_url_str}")
                            yeni_lines.append(updated_proxy_url_str + '\n')
                            degisti_mi = True
                            guncellenen_sayisi += 1
                        else:
                            log.log(f"[gray]• Zaten güncel (Satır {line_num + 1}): {line_content_stripped}")
                            yeni_lines.append(original_line)
                    else:
                        yeni_lines.append(original_line) 
                except Exception as e:
                    log.log(f"[red][!] Hata (Satır {line_num + 1}): {line_content_stripped} işlenirken hata: {e}")
                    yeni_lines.append(original_line) 
            else:
                yeni_lines.append(original_line) 

        if degisti_mi:
            with open(self.m3u_dosyasi, "w", encoding="utf-8") as f:
                f.writelines(yeni_lines)
            log.log(f"[green][✓] M3U dosyası güncellendi. Toplam {guncellenen_sayisi} proxy URL güncellendi.")
        else:
            log.log(f"[green][✓] Güncellenecek proxy URL bulunamadı veya tümü zaten günceldi, dosya yazılmadı.")

if __name__ == "__main__":
    guncelle = MonoTV("subatv.m3u")
    guncelle.m3u_guncelle()