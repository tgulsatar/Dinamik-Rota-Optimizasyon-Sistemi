import io
import sys
import math
import time

from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

class RotaOptimizatoru:
    def __init__(self, isimler, sure_matrisi, talepler, fiziksel_iha_sayisi):
        self.isimler = isimler
        assert len(isimler) > 0 and isimler[0] == "BASE_ATATURK", \
            f"HATA: isimler[0] = '{isimler[0] if isimler else 'BOŞ'}' — 'BASE_ATATURK' bekleniyor!"
        self.sure_matrisi = sure_matrisi
        self.talepler = [float(t) for t in talepler]
        
        self.num_nodes = len(isimler)
        self.depot = 0
        self.fiziksel_iha_sayisi = fiziksel_iha_sayisi
        self.iha_kapasite = 15
        self.full_sarj_sure = 25

        self.ulasılamaz_dugumler = set()
        for i in range(1, self.num_nodes):  
            gidis_imkansiz = self.sure_matrisi[0][i] >= 9990.0
            donus_imkansiz = self.sure_matrisi[i][0] >= 9990.0
            if gidis_imkansiz or donus_imkansiz:
                self.ulasılamaz_dugumler.add(i)
        
        if self.fiziksel_iha_sayisi <= 0:
            raise ValueError("Fiziksel İHA sayısı 0 olamaz! En az 1 İHA gereklidir.")
        
        sirali_yukler = sorted(
            [self.talepler[i] for i in range(1, self.num_nodes)
             if self.talepler[i] > 0 and i not in self.ulasılamaz_dugumler],
            reverse=True
        )
        sanal_cantalar = []
        
        for yuk in sirali_yukler:
            yerlesti_mi = False
            for i in range(len(sanal_cantalar)):
                if sanal_cantalar[i] + yuk <= self.iha_kapasite:
                    sanal_cantalar[i] += yuk
                    yerlesti_mi = True
                    break
            
            if not yerlesti_mi:
                sanal_cantalar.append(yuk)
        
        ulasılabilir_dugum_sayisi = self.num_nodes - 1 - len(self.ulasılamaz_dugumler)
        garanti_sefer_sayisi = max(len(sanal_cantalar), ulasılabilir_dugum_sayisi)
        
        self.max_sefer = math.ceil(garanti_sefer_sayisi / self.fiziksel_iha_sayisi) + 1
        self.total_virtual_vehicles = self.fiziksel_iha_sayisi * self.max_sefer
    
    def rotalari_hesapla(self):
        manager = pywrapcp.RoutingIndexManager(self.num_nodes, self.total_virtual_vehicles, self.depot)
        routing = pywrapcp.RoutingModel(manager)

        sanal_limitler = [self.full_sarj_sure * 100] * self.total_virtual_vehicles

        def time_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return int(round(self.sure_matrisi[from_node][to_node] * 100))

        transit_callback_index = routing.RegisterTransitCallback(time_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

        routing.AddDimensionWithVehicleCapacity(
            transit_callback_index, 0, sanal_limitler, True, 'Zaman'
        )

        def demand_callback(from_index):
            from_node = manager.IndexToNode(from_index)
            return int(round(self.talepler[from_node] * 100))

        demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
        routing.AddDimensionWithVehicleCapacity(
            demand_callback_index, 0, [self.iha_kapasite * 100] * self.total_virtual_vehicles, True, 'Kapasite'
        )

        for v_id in range(self.total_virtual_vehicles):
            sefer_no = (v_id % self.max_sefer) + 1
            
            if sefer_no == 1:
                sabit_maliyet = 0 
            else:
                sabit_maliyet = max(10000, self.full_sarj_sure * 100 * self.num_nodes) 
                
            routing.SetFixedCostOfVehicle(sabit_maliyet, v_id)

        ulasılabilir_dugum_sayisi = self.num_nodes - 1 - len(self.ulasılamaz_dugumler)
        
        if ulasılabilir_dugum_sayisi > 0:
            solver = routing.solver()
            for v_id in range(self.total_virtual_vehicles):
                sefer_no = (v_id % self.max_sefer) + 1
                if sefer_no > 1:
                    onceki_v_id = v_id - 1
                    
                    start_onceki = routing.Start(onceki_v_id)
                    end_onceki = routing.End(onceki_v_id)
                    
                    start_guncel = routing.Start(v_id)
                    end_guncel = routing.End(v_id)
                    
                    is_empty_onceki = solver.IsEqualCstVar(routing.NextVar(start_onceki), end_onceki)
                    is_empty_guncel = solver.IsEqualCstVar(routing.NextVar(start_guncel), end_guncel)
                    
                    solver.Add(is_empty_onceki <= is_empty_guncel)

        YUKLU_CEZA = 1_000_000
        for node_idx in range(1, self.num_nodes):
            index = manager.NodeToIndex(node_idx)
            if node_idx in self.ulasılamaz_dugumler:
                routing.AddDisjunction([index], 0)
            else:
                routing.AddDisjunction([index], YUKLU_CEZA)

        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PARALLEL_CHEAPEST_INSERTION
        )
        
        search_parameters.local_search_metaheuristic = (
            routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
        )
        
        dinamik_sure = min(30, max(5, int(self.num_nodes * 0.2)))
        search_parameters.time_limit.FromSeconds(dinamik_sure)

        cozum = routing.SolveWithParameters(search_parameters)

        if cozum:
            return self._sonuclari_derle(manager, routing, cozum)
        else:
            return {"Hata": "Kapasite veya süre aşıldı. Bu görev mevcut İHA sınırlarıyla yapılamaz!"}

    def _sonuclari_derle(self, manager, routing, cozum):
        sonuc_raporu = {}

        dusurulmus = []
        for node_idx in range(1, self.num_nodes):
            index = manager.NodeToIndex(node_idx)
            if cozum.Value(routing.NextVar(index)) == index:
                dusurulmus.append(self.isimler[node_idx])
        if dusurulmus:
            sonuc_raporu["_UYARI_DUSURULMUS_NOKTALAR"] = dusurulmus
        
        for v_id in range(self.total_virtual_vehicles):
            index = routing.Start(v_id)
            if routing.IsEnd(cozum.Value(routing.NextVar(index))):
                continue

            fiziksel_id = (v_id // self.max_sefer) + 1
            sefer_no = (v_id % self.max_sefer) + 1
            iha_etiket = f"Falcon_{fiziksel_id}_Sefer_{sefer_no}"
            
            rota_dugumleri = []
            rota_yuku = 0
            rota_suresi = 0.0

            while not routing.IsEnd(index):
                node_index = manager.IndexToNode(index)
                durak_ismi = self.isimler[node_index]
                
                if not rota_dugumleri or rota_dugumleri[-1] != durak_ismi:
                    rota_dugumleri.append(durak_ismi)
                
                rota_yuku += self.talepler[node_index]
                
                previous_index = index
                index = cozum.Value(routing.NextVar(index))
                
                p_node = manager.IndexToNode(previous_index)
                c_node = manager.IndexToNode(index)
                rota_suresi += float(self.sure_matrisi[p_node][c_node])

            son_durak_index = manager.IndexToNode(index)
            son_durak_ismi = self.isimler[son_durak_index]
            if rota_dugumleri and rota_dugumleri[-1] != son_durak_ismi:
                rota_dugumleri.append(son_durak_ismi)

            if len(rota_dugumleri) >= 2:
                sonuc_raporu[iha_etiket] = {
                    "Rota": " ➔ ".join(rota_dugumleri),
                    "Yük": f"{round(rota_yuku, 2)} kg",
                    "Uçuş Süresi": round(rota_suresi, 2)
                }

        return sonuc_raporu

BENCHMARKS = {
    "A-n32-k5": {
        "bks": 784.0,
        "capacity": 100,
        "vehicles": 5,
        "coords": [
            (82, 76), (96, 44), (50, 5), (49, 8), (13, 7), (29, 89), (58, 30),
            (84, 39), (14, 24), (2, 39), (3, 82), (5, 10), (98, 52), (84, 25),
            (61, 59), (1, 65), (88, 51), (91, 2), (19, 32), (93, 3), (50, 93),
            (98, 14), (5, 42), (42, 9), (61, 62), (9, 97), (80, 55), (57, 69),
            (23, 15), (20, 70), (85, 60), (98, 5)
        ],
        "demands": [
            0, 19, 21, 6, 19, 7, 12, 16, 6, 16, 8, 14, 21, 16, 3, 22, 18, 19,
            1, 24, 8, 12, 4, 8, 24, 24, 2, 20, 15, 2, 14, 9
        ]
    },
    "E-n22-k4": {
        "bks": 375.0,
        "capacity": 6000,
        "vehicles": 4,
        "coords": [
            (145, 215), (151, 264), (159, 261), (130, 254), (128, 252), (163, 247), (146, 246),
            (161, 242), (142, 239), (163, 236), (148, 232), (128, 231), (156, 217), (129, 214),
            (146, 208), (164, 208), (141, 206), (147, 193), (164, 193), (129, 189), (155, 185),
            (139, 182)
        ],
        "demands": [
            0, 1100, 700, 800, 1400, 2100, 400, 800, 100, 500, 600, 1200, 1300, 1300, 300, 900,
            2100, 1000, 900, 2500, 1800, 700
        ]
    },
    "A-n60-k9": {
        "bks": 1354.0,
        "capacity": 100,
        "vehicles": 9,
        "coords": [
            (27, 93), (33, 27), (29, 39), (7, 81), (1, 59), (49, 9), (21, 53), (79, 89), (81, 83),
            (85, 11), (45, 9), (7, 65), (95, 27), (81, 85), (37, 81), (69, 69), (15, 95), (89, 75),
            (33, 93), (57, 83), (11, 95), (3, 57), (45, 11), (43, 61), (35, 43), (19, 83), (83, 69),
            (85, 77), (19, 39), (83, 87), (1, 13), (15, 39), (83, 17), (41, 97), (31, 61), (59, 69),
            (29, 15), (93, 83), (63, 97), (65, 57), (15, 69), (31, 97), (57, 9), (85, 37), (21, 29),
            (53, 11), (15, 77), (41, 69), (45, 17), (13, 25), (63, 57), (95, 5), (55, 91), (3, 31),
            (47, 7), (61, 69), (85, 35), (89, 81), (45, 47), (65, 93)
        ],
        "demands": [
            0, 16, 2, 7, 11, 9, 17, 21, 23, 10, 6, 19, 18, 20, 13, 5, 11, 24, 2, 3, 1, 5, 20, 23,
            24, 18, 19, 2, 17, 17, 9, 11, 2, 6, 9, 5, 9, 2, 14, 19, 11, 21, 20, 21, 18, 48, 1, 17,
            42, 2, 4, 24, 18, 21, 11, 9, 18, 22, 9, 23
        ]
    }
}

def oklid_uzaklik(p1, p2):
    return round(math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2))

def matris_olustur(koordinatlar):
    n = len(koordinatlar)
    matris = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i != j:
                matris[i][j] = float(oklid_uzaklik(koordinatlar[i], koordinatlar[j]))
    return matris

class BenchmarkRotaOptimizatoru(RotaOptimizatoru):
    def __init__(self, isimler, sure_matrisi, talepler, fiziksel_iha_sayisi, kapasite, batarya=999999):
        self.isimler = isimler
        assert len(isimler) > 0 and isimler[0] == "BASE_ATATURK", \
            f"HATA: isimler[0] = '{isimler[0] if isimler else 'BOŞ'}' — 'BASE_ATATURK' bekleniyor!"
        
        self.sure_matrisi = sure_matrisi
        self.talepler = [float(t) for t in talepler]
        self.num_nodes = len(isimler)
        self.depot = 0
        self.fiziksel_iha_sayisi = fiziksel_iha_sayisi
        self.iha_kapasite = kapasite
        self.full_sarj_sure = batarya

        self.ulasılamaz_dugumler = set()
        for i in range(1, self.num_nodes):  
            gidis_imkansiz = self.sure_matrisi[0][i] >= 9990.0
            donus_imkansiz = self.sure_matrisi[i][0] >= 9990.0
            if gidis_imkansiz or donus_imkansiz:
                self.ulasılamaz_dugumler.add(i)

        if self.fiziksel_iha_sayisi <= 0:
            raise ValueError("Fiziksel İHA sayısı 0 olamaz!")

        sirali_yukler = sorted(
            [self.talepler[i] for i in range(1, self.num_nodes)
             if self.talepler[i] > 0 and i not in self.ulasılamaz_dugumler],
            reverse=True
        )
        sanal_cantalar = []
        for yuk in sirali_yukler:
            yerlesti = False
            for idx in range(len(sanal_cantalar)):
                if sanal_cantalar[idx] + yuk <= self.iha_kapasite:
                    sanal_cantalar[idx] += yuk
                    yerlesti = True
                    break
            if not yerlesti:
                sanal_cantalar.append(yuk)

        ulasılabilir_dugum_sayisi = self.num_nodes - 1 - len(self.ulasılamaz_dugumler)
        kapasite_bazli_sefer = len(sanal_cantalar)
        
        toplam_min_sure = sum(
            min(self.sure_matrisi[0][i], self.sure_matrisi[i][0]) 
            for i in range(1, self.num_nodes) if i not in self.ulasılamaz_dugumler
        )
        zaman_bazli_sefer = math.ceil(toplam_min_sure / self.full_sarj_sure) if self.full_sarj_sure > 0 else 1

        garanti_sefer_sayisi = max(kapasite_bazli_sefer, zaman_bazli_sefer, ulasılabilir_dugum_sayisi)
        
        self.max_sefer = math.ceil(garanti_sefer_sayisi / self.fiziksel_iha_sayisi) + 1
        self.total_virtual_vehicles = self.fiziksel_iha_sayisi * self.max_sefer

KALITE_SEMBOL = {
    "MÜKEMMEL": "✓✓",
    "İYİ":      "✓ ",
    "ORTA":     "~ ",
    "ZAYIF":    "✗ ",
}

def _kisalt_etiket(etiket: str) -> str:
    try:
        parcalar = etiket.split("_")
        return f"F{parcalar[1]}·S{parcalar[3]}"
    except (IndexError, ValueError):
        return etiket

def run_test(instance_name, detayli_yazdir=False):
    if instance_name not in BENCHMARKS:
        print(f"  [!] {instance_name} bulunamadı.")
        return None

    data = BENCHMARKS[instance_name]
    coords   = data["coords"]
    demands  = data["demands"]
    capacity = data["capacity"]
    vehicles = data["vehicles"]
    bks      = data["bks"]

    n = len(coords)
    isimler = [f"D{i}" for i in range(n)]
    isimler[0] = "BASE_ATATURK"

    sure_matrisi = matris_olustur(coords)

    print(f"\n  {instance_name}  │  {n} düğüm  │  {vehicles} araç  │  BKS: {bks:.0f}")
    print("  " + "─" * 60)

    optimizer = BenchmarkRotaOptimizatoru(
        isimler=isimler,
        sure_matrisi=sure_matrisi,
        talepler=demands,
        fiziksel_iha_sayisi=vehicles,
        kapasite=capacity
    )

    start_time = time.time()
    sonuc = optimizer.rotalari_hesapla()
    elapsed = time.time() - start_time

    if "Hata" in sonuc:
        print(f"  [!] Çözüm bulunamadı: {sonuc['Hata']}")
        return None

    bulunan_toplam = 0.0
    for etiket, bilgi in sonuc.items():
        mes = bilgi.get("Ucus Suresi", bilgi.get("Uçuş Süresi", 0))
        bulunan_toplam += mes

        if detayli_yazdir:
            yuk  = bilgi.get("Yuk", bilgi.get("Yük", "?"))
            rota = bilgi.get("Rota", "?")
            rota_k = rota[:75] + ("…" if len(rota) > 75 else "")
            kisik = _kisalt_etiket(etiket)
            print(f"  {kisik:<6}  {str(yuk):>8}  {mes:>7.1f} km   {rota_k}")

    gap    = (bulunan_toplam - bks) / bks * 100
    kalite = "ZAYIF"
    if   gap <= 1.0: kalite = "MÜKEMMEL"
    elif gap <= 3.0: kalite = "İYİ"
    elif gap <= 6.0: kalite = "ORTA"

    sem = KALITE_SEMBOL.get(kalite, "  ")
    print(f"\n  Toplam: {bulunan_toplam:.1f}   Gap: {gap:+.2f}%   {sem} {kalite}   ({elapsed:.1f}s)")

    return {
        "name": instance_name, "nodes": n, "vehicles": vehicles,
        "found": bulunan_toplam, "bks": bks, "gap": gap,
        "time": elapsed, "quality": kalite,
    }

def main():
    print("=" * 68)
    print("  VRP BENCHMARK TEST ARACI")
    print("=" * 68)

    sonuclar = []
    for instance in BENCHMARKS.keys():
        sonuc = run_test(instance, detayli_yazdir=True)
        if sonuc:
            sonuclar.append(sonuc)

    print("\n\n" + "=" * 68)
    print("  ÖZET")
    print("=" * 68)
    print(f"  {'Instance':<14} {'N':>4} {'K':>3}  {'BKS':>7}  {'Bulunan':>8}  {'Gap':>7}  {'Kalite':<10} {'Süre':>6}")
    print("  " + "─" * 64)
    for r in sonuclar:
        sem = KALITE_SEMBOL.get(r['quality'], "  ")
        print(
            f"  {r['name']:<14} {r['nodes']:>4} {r['vehicles']:>3}"
            f"  {r['bks']:>7.1f}  {r['found']:>8.1f}"
            f"  {r['gap']:>+6.2f}%  {sem} {r['quality']:<8}  {r['time']:>5.1f}s"
        )
    print("=" * 68)

if __name__ == "__main__":
    orijinal_ekran = sys.stdout
    
    orijinal_ekran.write("Test işlemi sürüyor, algoritmalar devrede. Lütfen bekleyin...\n")
    orijinal_ekran.flush()
    
    yeni_rapor_adi = "ana_test_sonucu.txt"
    
    try:
        with open(yeni_rapor_adi, "w", encoding="utf-8-sig") as log_dosyasi:
            sys.stdout = log_dosyasi
            main()
    except Exception as e:
        sys.stdout = orijinal_ekran
        print(f"Operasyon başarısız: {e}")
    finally:
        sys.stdout = orijinal_ekran
        
    print(f'\nTest sonucu "{yeni_rapor_adi}" dosyasına işlenmiştir.')