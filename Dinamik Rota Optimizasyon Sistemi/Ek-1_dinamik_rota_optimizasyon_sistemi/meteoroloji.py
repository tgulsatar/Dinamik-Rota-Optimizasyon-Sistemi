import requests
import time
import re


class Meteoroloji:
    def __init__(self, ana_istasyon="LTBA", yedek_istasyon="LTFM"):
        self.ana_istasyon = ana_istasyon
        self.yedek_istasyon = yedek_istasyon
        self.maks_deneme = 2
        
    def _api_istegi_yap(self, icao_code):
        url = f"https://tgftp.nws.noaa.gov/data/observations/metar/stations/{icao_code}.TXT"
        
        for deneme in range(1, self.maks_deneme + 1):
            try:
                if deneme > 1:
                    time.sleep(0.5)
                
                response = requests.get(url, timeout=5, verify=False) 
                
                if response.status_code == 200:
                    satirlar = response.text.strip().split('\n')
                    if len(satirlar) >= 2:
                        metar_kodu = satirlar[1]
                        
                        ruzgar_deseni = re.search(r'\b(\d{3}|VRB)(\d{2,3})(?:G\d{2,3})?(KT|MPS)\b', metar_kodu)
                        
                        if ruzgar_deseni:
                            yon_str = ruzgar_deseni.group(1)
                            hiz_str = ruzgar_deseni.group(2)
                            birim = ruzgar_deseni.group(3)
                            
                            ruzgar_yonu = 0.0 if yon_str == 'VRB' else float(yon_str)
                            hiz_ham = float(hiz_str)
                            
                            if birim == 'KT':
                                ruzgar_hizi_kmh = hiz_ham * 1.852
                            else:
                                ruzgar_hizi_kmh = hiz_ham * 3.6
                                
                            return ruzgar_yonu, ruzgar_hizi_kmh
            except Exception as e:
                pass
        return None
   
    def canli_ruzgar_verisi_cek(self):
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        print(f"NOAA Radarından Canlı METAR verisi aranıyor (Ana Üs: {self.ana_istasyon})...")
        
        metar_info = self._api_istegi_yap(self.ana_istasyon)

        if not metar_info:
            print(f"Ana üs yanıt vermiyor! Yedek meydan '{self.yedek_istasyon}' dinleniyor...")
            metar_info = self._api_istegi_yap(self.yedek_istasyon)

        if not metar_info:
            print("Radyo sessizliği! Statik lodos senaryosuna dönülüyor.")
            return 220.0, 15.0  

        return metar_info