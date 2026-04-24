from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import math


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