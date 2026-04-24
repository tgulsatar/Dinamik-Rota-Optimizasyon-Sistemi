import math
from donanim import DasalFalcon


class GorevYoneticisi:
    def __init__(self, ruzgar_hizi, ruzgar_yonu):
        self.ruzgar_hizi = ruzgar_hizi
        self.ruzgar_yonu = ruzgar_yonu
        self.iha = DasalFalcon() 


    def haversine(self, lat1, lon1, lat2, lon2):
        R = 6371.0
        dlat, dlon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
        a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
        return R * (2 * math.atan2(math.sqrt(min(1.0, a)), math.sqrt(max(0.0, 1 - a))))

    def kerteriz(self, lat1, lon1, lat2, lon2):
        lat1_rad, lat2_rad = math.radians(lat1), math.radians(lat2)
        diff_lon = math.radians(lon2 - lon1)
        x = math.sin(diff_lon) * math.cos(lat2_rad)
        y = math.cos(lat1_rad) * math.sin(lat2_rad) - (math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(diff_lon))
        return (math.degrees(math.atan2(x, y)) + 360) % 360


    def asimetrik_sure(self, mesafe_km, bearing):
        angle_diff = math.radians(self.ruzgar_yonu - bearing)
        
        headwind = self.ruzgar_hizi * math.cos(angle_diff)
        crosswind = self.ruzgar_hizi * math.sin(angle_diff)
        
        if abs(crosswind) >= self.iha.hiz:
            return 9999.0  
            
        asin_arg = max(-1.0, min(1.0, crosswind / self.iha.hiz))
        wca = math.asin(asin_arg)
        
        ground_speed = (self.iha.hiz * math.cos(wca)) - headwind
        
        if ground_speed <= 5.0: 
            return 9999.0
            
        sure_dakika = (mesafe_km / ground_speed) * 60.0
        
        return sure_dakika

    def dinamik_matris_uret(self, aktif_noktalar):
        isimler = list(aktif_noktalar.keys())
        boyut = len(isimler)
        mesafe_matrisi = [[0.0 for _ in range(boyut)] for _ in range(boyut)]
        sure_matrisi = [[0.0 for _ in range(boyut)] for _ in range(boyut)]
        
        for i in range(boyut):
            for j in range(boyut):
                if i != j:
                    n1, n2 = aktif_noktalar[isimler[i]], aktif_noktalar[isimler[j]]
                    dist = self.haversine(n1["lat"], n1["lon"], n2["lat"], n2["lon"])
                    mesafe_matrisi[i][j] = round(dist, 2)
                    brng = self.kerteriz(n1["lat"], n1["lon"], n2["lat"], n2["lon"])
                    sure_matrisi[i][j] = round(self.asimetrik_sure(dist, brng), 2)
                    
        return isimler, mesafe_matrisi, sure_matrisi