import streamlit as st
import folium
import pandas as pd
import streamlit.components.v1 as components
import math
import re 
import plotly.express as px
import time 

from matematik_motoru import GorevYoneticisi
from optimizasyon import RotaOptimizatoru
from meteoroloji import Meteoroloji

st.set_page_config(page_title="Taktik Hava Köprüsü | Komuta Merkezi", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #e0e0e0; }
    
    [data-testid="stMetric"] {
        background-color: #1a1c23 !important; padding: 20px; border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3); border-left: 5px solid #3b82f6 !important; 
        border: 1px solid #30363d !important;
    }
    [data-testid="stMetricLabel"] { color: #94a3b8 !important; font-size: 14px !important; }
    [data-testid="stMetricValue"] { color: #ffffff !important; font-weight: bold !important; }
    [data-testid="stMetricDelta"] { font-weight: bold !important; }

    section[data-testid="stSidebar"] { background-color: #161b22 !important; border-right: 1px solid #30363d; }
    section[data-testid="stSidebar"] .stMarkdown h1, h2, h3 { color: #3b82f6 !important; }

    [data-testid="stExpander"] { background-color: #0d1117; border: 1px solid #30363d; border-radius: 8px; }
    [data-testid="stExpander"] summary { font-weight: bold; color: #58a6ff; }

    .stButton>button {
        width: 100%; border-radius: 10px; height: 3.6em; font-weight: 800;
        font-size: 14px; letter-spacing: 0.6px; text-transform: uppercase;
        background: linear-gradient(135deg, #1d4ed8 0%, #2563eb 100%) !important;
        color: white !important; border: 1px solid #3b82f6 !important;
        box-shadow: 0 2px 10px rgba(37, 99, 235, 0.3);
        transition: all 0.25s ease;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%) !important;
        box-shadow: 0 0 22px rgba(59, 130, 246, 0.65);
        transform: translateY(-2px);
        border-color: #60a5fa !important;
    }
    .st-key-del_btn button { background-color: #ef4444 !important; height: 2.5em; }
    .st-key-del_btn button:hover { background-color: #dc2626 !important; border: 1px solid #fca5a5 !important; }
    [class*="st-key-del_"] button { background-color: #ef4444 !important; height: 2.5em;
        box-shadow: none; text-transform: uppercase; font-size: 12px; }
    [class*="st-key-del_"] button:hover { background-color: #dc2626 !important; border: 1px solid #fca5a5 !important; }

    [class*="st-key-btn_metar"] button {
        background: linear-gradient(135deg, #0e7490 0%, #0891b2 100%) !important;
        border-color: #22d3ee !important;
        box-shadow: 0 2px 10px rgba(8, 145, 178, 0.35) !important;
    }
    [class*="st-key-btn_metar"] button:hover {
        background: linear-gradient(135deg, #0891b2 0%, #06b6d4 100%) !important;
        box-shadow: 0 0 20px rgba(6, 182, 212, 0.6) !important;
    }

    [class*="st-key-btn_manuel"] button {
        background: linear-gradient(135deg, #15803d 0%, #16a34a 100%) !important;
        border-color: #4ade80 !important;
        box-shadow: 0 2px 10px rgba(22, 163, 74, 0.35) !important;
    }
    [class*="st-key-btn_manuel"] button:hover {
        background: linear-gradient(135deg, #16a34a 0%, #22c55e 100%) !important;
        box-shadow: 0 0 20px rgba(34, 197, 94, 0.6) !important;
    }

    [class*="st-key-btn_excel"] button {
        background: linear-gradient(135deg, #7e22ce 0%, #9333ea 100%) !important;
        border-color: #c084fc !important;
        box-shadow: 0 2px 10px rgba(147, 51, 234, 0.35) !important;
    }
    [class*="st-key-btn_excel"] button:hover {
        background: linear-gradient(135deg, #9333ea 0%, #a855f7 100%) !important;
        box-shadow: 0 0 20px rgba(168, 85, 247, 0.6) !important;
    }

    [class*="st-key-btn_temizle"] button {
        background: linear-gradient(135deg, #7f1d1d 0%, #991b1b 100%) !important;
        border-color: #f87171 !important;
        box-shadow: 0 2px 8px rgba(153, 27, 27, 0.35) !important;
        font-size: 13px;
    }
    [class*="st-key-btn_temizle"] button:hover {
        background: linear-gradient(135deg, #991b1b 0%, #dc2626 100%) !important;
        box-shadow: 0 0 18px rgba(220, 38, 38, 0.55) !important;
    }

    [class*="st-key-btn_baslat"] button {
        background: linear-gradient(135deg, #c2410c 0%, #ea580c 50%, #f97316 100%) !important;
        border-color: #fb923c !important;
        box-shadow: 0 4px 18px rgba(234, 88, 12, 0.5) !important;
        font-size: 15px;
        height: 4em;
    }
    [class*="st-key-btn_baslat"] button:hover {
        background: linear-gradient(135deg, #ea580c 0%, #f97316 100%) !important;
        box-shadow: 0 0 28px rgba(249, 115, 22, 0.75) !important;
        transform: translateY(-3px);
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        background-color: #161b22;
        border-radius: 12px;
        padding: 6px;
        border: 1px solid #30363d;
    }
    .stTabs [data-baseweb="tab"] {
        height: 52px;
        min-width: 200px;
        font-weight: 700;
        font-size: 15px;
        color: #64748b !important;
        border-radius: 8px !important;
        padding: 0 28px !important;
        letter-spacing: 0.3px;
        transition: all 0.2s ease;
        border-bottom: none !important;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: #93c5fd !important;
        background-color: #1e2936 !important;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        color: #ffffff !important;
        background-color: #2563eb !important;
        box-shadow: 0 0 18px rgba(37, 99, 235, 0.45);
        border-bottom: none !important;
    }

    iframe { border-radius: 12px; border: 1px solid #30363d; }
    
    .custom-row { border-bottom: 1px solid #30363d; padding-top: 10px; padding-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

if 'hedefler' not in st.session_state:
    st.session_state.hedefler = []
if 'gorev_emri' not in st.session_state:
    st.session_state.gorev_emri = None
if 'islenmis_noktalar' not in st.session_state:
    st.session_state.islenmis_noktalar = {}
if 'ruzgar_hizi' not in st.session_state:
    st.session_state.ruzgar_hizi = 22.0
if 'ruzgar_aci' not in st.session_state:
    st.session_state.ruzgar_aci = 225.0
if 'oto_gizle' not in st.session_state:
    st.session_state.oto_gizle = False
if 'secili_rota' not in st.session_state:
    st.session_state.secili_rota = None
if 'haritaya_git' not in st.session_state:
    st.session_state.haritaya_git = False

st.title("Dinamik Rota Optimizasyon Sistemi")
st.markdown("---")

if st.session_state.oto_gizle:
    components.html(
        """
        <script>
            const parentDocs = window.parent.document;
            const collapseBtn = parentDocs.querySelector('[data-testid="collapsedControl"]');
            if (collapseBtn && collapseBtn.getAttribute('aria-expanded') === 'true') {
                collapseBtn.click();
            }
        </script>
        """, height=0
    )
    st.session_state.oto_gizle = False 



with st.sidebar.expander("Filo Parametreleri", expanded=True):
    aktif_iha = st.slider("Operasyonel İHA Adedi", 1, 10, 5)
    filo_toplam_kapasite = aktif_iha * 15 

with st.sidebar.expander("Çevre Parametreleri", expanded=False):
    if st.button("Canlı METAR Verisi Çek (LTBA)", use_container_width=True, key="btn_metar"):
        with st.spinner("Hava Durumu Sunucusuna Bağlanılıyor..."):
            hava_servisi = Meteoroloji() 
            sonuc = hava_servisi.canli_ruzgar_verisi_cek()
            
            if sonuc:
                st.session_state.ruzgar_aci = sonuc[0]
                st.session_state.ruzgar_hizi = sonuc[1]
                st.success(f"VERİ ALINDI: {sonuc[0]}° | {sonuc[1]:.1f} km/h")
                time.sleep(1)
                st.rerun()
            else:
                st.error("API Bağlantı Hatası! Lütfen manuel giriş yapın.")

    st.markdown("<div style='text-align: center; color: #94a3b8; font-size: 14px; margin: 10px 0;'>- VEYA -</div>", unsafe_allow_html=True)
    
    yeni_hiz = st.number_input("Rüzgar Hızı (km/h)", value=float(st.session_state.ruzgar_hizi), step=1.0)
    yeni_aci = st.number_input("Rüzgar Yönü (Derece)", value=float(st.session_state.ruzgar_aci), step=5.0)
    
    if st.button("Manuel Parametreleri Uygula", use_container_width=True, key="btn_manuel"):
        st.session_state.ruzgar_hizi = yeni_hiz
        st.session_state.ruzgar_aci = yeni_aci
        st.toast("Çevre parametreleri sisteme işlendi!", icon="✅")
        time.sleep(0.5)
        st.rerun()

with st.sidebar.expander("Görev Atama", expanded=True):
    st.markdown("**Veritabanından Toplu Yükleme**")
    yuklenen_excel = st.file_uploader("Excel Dosyası (.xlsx, .xls)", type=["xlsx", "xls"])

    if yuklenen_excel is not None:
        if st.button("EXCEL VERİLERİNİ AKTAR", key="btn_excel"):
            try:
                df_excel = pd.read_excel(yuklenen_excel)
                beklenen_sutunlar = ["Hedef Tanımı", "Hedef Tipi", "Enlem-Boylam", "Yük (kg)"]
                eksik_sutunlar = [s for s in beklenen_sutunlar if s not in df_excel.columns]
                
                if eksik_sutunlar:
                    st.error(f"SİSTEM UYARISI: Eksik sütunlar: {', '.join(eksik_sutunlar)}")
                else:
                    eklenen_hedef_sayisi = 0
                    for index, row in df_excel.iterrows():
                        isim_temiz = str(row["Hedef Tanımı"]).replace(" ", "_")
                        tip_raw = str(row["Hedef Tipi"]).lower()
                        if "hastane" in tip_raw:
                            nihai_tip = "Hastane / Sağlık Merkezi"
                        else:
                            nihai_tip = "Afet / Acil Durum Bölgesi"
                            
                        koordinat_metni = str(row["Enlem-Boylam"])
                        lat_str, lon_str = koordinat_metni.split(",")
                        
                        st.session_state.hedefler.append({
                            "isim": isim_temiz, 
                            "tip": nihai_tip, 
                            "lat": float(lat_str.strip()), 
                            "lon": float(lon_str.strip()), 
                            "talep": float(row["Yük (kg)"])
                        })
                        eklenen_hedef_sayisi += 1
                    
                    st.session_state.gorev_emri = None 
                    st.session_state.secili_rota = None
                    st.success(f"{eklenen_hedef_sayisi} hedef aktarıldı.")
                    time.sleep(1.5)
                    st.rerun()
            except Exception as e:
                st.error(f"HATA: Dosya okunamadı. Detay: {str(e)[:120]}")

    st.markdown("<div style='text-align: center; color: #94a3b8; font-size: 14px; margin: 10px 0;'>- VEYA -</div>", unsafe_allow_html=True)

    with st.form("gorev_formu", clear_on_submit=True):
        isim = st.text_input("Hedef Tanımı", placeholder="Örn: Sektör-7 Enkaz")
        tip = st.selectbox("Hedef Tipi", ["Afet / Acil Durum Bölgesi", "Hastane / Sağlık Merkezi"])
        koordinat_metni = st.text_input("Koordinat Bilgisi", placeholder="41.015, 28.979")
        talep = st.number_input("Talep Edilen Yük (kg)", min_value=0.1, max_value=50.0, value=5.0, step=0.1)
        ekle = st.form_submit_button("MANUEL GÖREV ATAMASINI ONAYLA")

    if ekle:
        if isim and koordinat_metni:
            try:
                isim_temiz = isim.replace(" ", "_")
                lat_str, lon_str = koordinat_metni.split(",")
                enlem, boylam = float(lat_str.strip()), float(lon_str.strip())
                st.session_state.hedefler.append({"isim": isim_temiz, "tip": tip, "lat": enlem, "lon": boylam, "talep": talep})
                st.session_state.gorev_emri = None 
                st.session_state.secili_rota = None
            except Exception:
                st.error("HATA: Geçersiz koordinat dizilimi tespit edildi.")
            else:
                st.rerun()
        else:
            st.warning("SİSTEM UYARISI: Gerekli alanların tamamı doldurulmalıdır.")

with st.sidebar.expander("Hedef Yönetimi", expanded=False):
    if st.session_state.hedefler:
        for i, h in enumerate(st.session_state.hedefler):
            colA, colB = st.columns([7, 3])
            colA.write(f"{h['isim']} ({h['talep']} kg)")
            if colB.button("Sil", key=f"del_{i}"):
                st.session_state.hedefler.pop(i)
                st.session_state.gorev_emri = None
                st.session_state.secili_rota = None
                st.rerun()
                
        if st.button("TÜM KAYITLARI TEMİZLE", key="btn_temizle"):
            st.session_state.hedefler = []
            st.session_state.gorev_emri = None
            st.session_state.secili_rota = None
            st.rerun()
    else:
        st.info("Sistemde kayıtlı operasyon noktası bulunmamaktadır.")

total_targets = len(st.session_state.hedefler)
total_payload = sum(h['talep'] for h in st.session_state.hedefler)

col1, col2 = st.columns(2)
with col1:
    st.metric("Aktif Görev Noktası", f"{total_targets} Adet")
with col2:
    st.metric("Toplam Operasyonel Yük Talebi", f"{total_payload:.1f} kg")

if st.session_state.hedefler:
    st.markdown("<br>", unsafe_allow_html=True) 
    
    if st.button("ROTALAMAYI BAŞLAT", key="btn_baslat", use_container_width=True):
        
        loading_placeholder = st.empty()
        loading_placeholder.markdown("""
            <style>
            .loading-overlay {
                position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
                background-color: rgba(14, 17, 23, 0.90); z-index: 999999;
                display: flex; flex-direction: column; justify-content: center; align-items: center;
                backdrop-filter: blur(5px);
            }
            .loader {
                border: 8px solid #161b22;
                border-top: 8px solid #3b82f6;
                border-radius: 50%;
                width: 60px;
                height: 60px;
                animation: spin 1s linear infinite;
                margin-bottom: 25px;
            }
            @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
            </style>
            <div class="loading-overlay">
                <div class="loader"></div>
                <h2 style="color: #60a5fa; font-family: sans-serif; letter-spacing: 2px;">Otonom Rota Optimizasyonu Yürütülüyor...</h2>
                <h5 style="color: #94a3b8; font-family: monospace; font-weight: normal;">Sistem matrisleri hesaplıyor, lütfen bekleyiniz.</h5>
            </div>
        """, unsafe_allow_html=True)
        
        time.sleep(0.5) 
        
        base_lat, base_lon = 40.968581, 28.825583 
        aktif_gorev_noktalari = {"BASE_ATATURK": {"lat": base_lat, "lon": base_lon, "yuk": 0}}
        for h in st.session_state.hedefler:
            aktif_gorev_noktalari[h['isim']] = {"lat": h['lat'], "lon": h['lon'], "yuk": h['talep']}

        islenmis_noktalar = {}
        for target_isim, veri in aktif_gorev_noktalari.items():
            if veri["yuk"] > 15:
                parca_sayisi = math.ceil(veri["yuk"] / 15)
                kalan_yuk = veri["yuk"]
                for i in range(1, parca_sayisi + 1):
                    dilim = 15 if kalan_yuk >= 15 else kalan_yuk
                    islenmis_noktalar[f"{target_isim}_Parca{i}"] = {"lat": veri["lat"], "lon": veri["lon"], "yuk": dilim}
                    kalan_yuk -= 15
            else:
                islenmis_noktalar[target_isim] = veri
        
        st.session_state.islenmis_noktalar = islenmis_noktalar

        yonetici = GorevYoneticisi(st.session_state.ruzgar_hizi, st.session_state.ruzgar_aci)
        koordinatlar = {k: {"lat": v["lat"], "lon": v["lon"]} for k, v in islenmis_noktalar.items()}
        talepler = [v["yuk"] for v in islenmis_noktalar.values()]

        aktif_isimler, _, anlik_sure = yonetici.dinamik_matris_uret(koordinatlar)
        beyin = RotaOptimizatoru(aktif_isimler, anlik_sure, talepler, aktif_iha)
        
        st.session_state.gorev_emri = beyin.rotalari_hesapla()
        st.session_state.secili_rota = None
        st.session_state.haritaya_git = False
        
        loading_placeholder.empty()
        st.session_state.oto_gizle = True 
        st.rerun() 

def yuk_temizle(yuk_metni):
    try:
        sayilar = re.findall(r"[-+]?(?:\d*\.\d+|\d+)", str(yuk_metni))
        return float(sayilar[0]) if sayilar else 0.0
    except: return 0.0

def format_iha_isim(ham_isim):
    if "_Sefer_" in ham_isim:
        kisimlar = ham_isim.split("_Sefer_")
        return f"{kisimlar[0].replace('_', ' ')} - {kisimlar[1]}. Sorti"
    return ham_isim.replace("_", " ")

sirali_gorevler = []
dusurulmus_noktalar = []
if st.session_state.gorev_emri and "Hata" not in st.session_state.gorev_emri:
    def dogal_sirala(isim):
        sayilar = re.findall(r'\d+', isim)
        return (int(sayilar[0]), isim) if sayilar else (0, isim)
    dusurulmus_noktalar = st.session_state.gorev_emri.get("_UYARI_DUSURULMUS_NOKTALAR", [])
    sirali_gorevler = sorted(
        [(k, v) for k, v in st.session_state.gorev_emri.items()
         if not k.startswith("_UYARI") and isinstance(v, dict)],
        key=lambda x: dogal_sirala(x[0])
    )


if st.session_state.get('haritaya_git', False):
    components.html(
        """
        <script>
            const parentDocs = window.parent.document;
            const tabs = parentDocs.querySelectorAll('[data-baseweb="tab"]');
            if (tabs.length > 0) {
                tabs[0].click(); // Harita sekmesine tıkla
            }
            parentDocs.documentElement.scrollTop = 0; // Sayfayı yukarı kaydır
        </script>
        """, height=0
    )
    st.session_state.haritaya_git = False 



tab1, tab2, tab3 = st.tabs([
    "Taktik Harekat Haritası", 
    "Operasyon Analiz Raporu", 
    "Filo Performans Grafikleri"
])

with tab1:
    base_lat, base_lon = 40.968581, 28.825583 
    m = folium.Map(location=[base_lat, base_lon], zoom_start=12, control_scale=True, tiles=None) 

    folium.TileLayer('CartoDB positron', name='Açık Tema', show=True).add_to(m)
    folium.TileLayer('CartoDB dark_matter', name='Karanlık Tema', show=False).add_to(m)
    folium.TileLayer(tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}', attr='Google', name='Uydu Görüntüsü', show=False).add_to(m)

    folium.Marker([base_lat, base_lon], icon=folium.Icon(color='black', icon='star', prefix='fa')).add_to(m)
    
    folium.Marker(
        [base_lat, base_lon],
        icon=folium.DivIcon(
            icon_size=(150, 36), icon_anchor=(75, 65),
            html='<div style="text-align: center; font-size: 11px; font-weight: 800; color: #ffffff; text-shadow: 0px 0px 4px #000, 1px 1px 2px #000; line-height: 1.2;">ANA KOMUTA MERKEZİ<br><span style="color: #a3e635;">(LTBA)</span></div>'
        )
    ).add_to(m)

    for h in st.session_state.hedefler:
        is_dropped = any(
            d == h['isim'] or d.startswith(h['isim'] + '_Parca')
            for d in dusurulmus_noktalar
        )
        if is_dropped:
            renk, ikon = "orange", "ban"
        elif h["tip"] == "Afet / Acil Durum Bölgesi":
            renk, ikon = "red", "warning"
        else:
            renk, ikon = "blue", "plus-square"
        
        folium.Marker([h['lat'], h['lon']], icon=folium.Icon(color=renk, icon=ikon, prefix='fa')).add_to(m)
        
        dropped_badge = "<br><span style='color:#fb923c;font-size:9px;'>&#9888; ULAŞILAMAZ</span>" if is_dropped else ""
        label_html = f'''
        <div style="text-align: center; font-family: sans-serif; font-size: 11px; font-weight: 700; color: #f8fafc; text-shadow: 0px 0px 5px rgba(0,0,0,1), 1px 1px 3px rgba(0,0,0,0.8); line-height: 1.2;">
            {h["isim"]}<br><span style="color: #60a5fa;">{h["talep"]} kg</span>{dropped_badge}
        </div>
        '''
        folium.Marker([h['lat'], h['lon']], icon=folium.DivIcon(icon_size=(140, 50), icon_anchor=(70, 75), html=label_html)).add_to(m)

    if st.session_state.get("islenmis_noktalar"):
        for durak_ismi, durak_veri in st.session_state.islenmis_noktalar.items():
            if "_Parca" in durak_ismi:
                parca_label = f'''
                <div style="text-align:center;font-size:9px;font-weight:700;color:#fde68a;text-shadow:0 0 4px #000;">
                    {durak_ismi.replace("_"," ")}<br><span style="color:#fb923c;">{durak_veri["yuk"]} kg</span>
                </div>
                '''
                folium.Marker(
                    [durak_veri["lat"], durak_veri["lon"]],
                    icon=folium.DivIcon(icon_size=(130, 40), icon_anchor=(65, 55), html=parca_label)
                ).add_to(m)

    if st.session_state.gorev_emri and "Hata" not in st.session_state.gorev_emri:
        renkler = ['#e11d48', '#3b82f6', '#10b981', '#a855f7', '#f97316', '#06b6d4', '#cbd5e1']
        renk_idx = 0
        
        secili_rota = st.session_state.get('secili_rota', None)
        
        for iha, veri in sirali_gorevler:
            rota_duraklari = veri["Rota"].split(" ➔ ")
            hat_rengi = renkler[renk_idx % len(renkler)]
            
            if secili_rota is None:
                c_weight = 1.5
                c_opacity = 1.0
            elif secili_rota == iha:
                c_weight = 4.0
                c_opacity = 1.0
            else:
                c_weight = 1.0
                c_opacity = 0.15
            
            for j in range(len(rota_duraklari) - 1):
                durak1 = rota_duraklari[j]
                durak2 = rota_duraklari[j+1]
                
                if durak1 not in st.session_state.islenmis_noktalar:
                    continue
                if durak2 not in st.session_state.islenmis_noktalar:
                    continue
                lat1 = st.session_state.islenmis_noktalar[durak1]["lat"]
                lon1 = st.session_state.islenmis_noktalar[durak1]["lon"]
                lat2 = st.session_state.islenmis_noktalar[durak2]["lat"]
                lon2 = st.session_state.islenmis_noktalar[durak2]["lon"]
                
                d_lat = lat2 - lat1
                d_lon = lon2 - lon1
                mesafe = math.sqrt(d_lat**2 + d_lon**2)
                
                kavisli_koordinatlar = []
                
                if mesafe == 0:
                    continue
                    
                p_lat = -(d_lon / mesafe)
                p_lon = (d_lat / mesafe)
                
                sapma_miktari = 0.00006 * ((renk_idx % 4) + 1)
                
                if renk_idx % 2 != 0:
                    sapma_miktari *= -1 
                
                c_lat = (lat1 + lat2) / 2 + (p_lat * sapma_miktari)
                c_lon = (lon1 + lon2) / 2 + (p_lon * sapma_miktari)
                
                adim_sayisi = 15
                for step in range(adim_sayisi + 1):
                    t = step / adim_sayisi
                    nokta_lat = ((1 - t) ** 2) * lat1 + 2 * (1 - t) * t * c_lat + (t ** 2) * lat2
                    nokta_lon = ((1 - t) ** 2) * lon1 + 2 * (1 - t) * t * c_lon + (t ** 2) * lon2
                    kavisli_koordinatlar.append([nokta_lat, nokta_lon])
                
                ucus_hatti = folium.PolyLine(
                    locations=kavisli_koordinatlar, 
                    color=hat_rengi, 
                    weight=c_weight, 
                    opacity=c_opacity, 
                    dash_array='4, 6', 
                    tooltip=f"{format_iha_isim(iha)} Operasyon Hattı ({durak1} ➔ {durak2})"
                ).add_to(m)
                
            renk_idx += 1

    folium.LayerControl(position='topright').add_to(m)
    
    odaklanma_ve_pusula_js = f"""
    <script>
    setTimeout(function() {{
        var map_keys = Object.keys(window).filter(k => k.startsWith('map_'));
        if(map_keys.length > 0) {{
            var map = window[map_keys[0]];
            var all_lines = [];
            
            var ruzgarAci = {st.session_state.ruzgar_aci};
            var ruzgarHiz = {st.session_state.ruzgar_hizi};
            
            var WindControl = L.Control.extend({{
                options: {{ position: 'topright' }},
                onAdd: function () {{
                    var container = L.DomUtil.create('div', 'leaflet-bar leaflet-control');
                    container.style.backgroundColor = '#161b22';
                    container.style.border = '2px solid #3b82f6';
                    container.style.borderRadius = '50%';
                    container.style.width = '70px';
                    container.style.height = '70px';
                    container.style.display = 'flex';
                    container.style.flexDirection = 'column';
                    container.style.justifyContent = 'center';
                    container.style.alignItems = 'center';
                    container.style.color = '#e0e0e0';
                    container.style.fontWeight = 'bold';
                    container.style.fontFamily = 'sans-serif';
                    container.style.marginTop = '15px';
                    container.style.marginRight = '15px';
                    container.style.position = 'relative';
                    container.style.boxShadow = '0 0 10px rgba(0,0,0,0.5)';
                    
                    container.innerHTML = `
                        <div style="font-size: 9px; color: #94a3b8; margin-bottom: 2px;">RÜZGAR</div>
                        <div style="font-size: 13px;">${{ruzgarHiz.toFixed(1)}}<span style="font-size:8px;">km/h</span></div>
                        <div style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; transform: rotate(${{ruzgarAci}}deg);">
                            <div style="position: absolute; top: -3px; left: 50%; transform: translateX(-50%); width: 0; height: 0; border-left: 6px solid transparent; border-right: 6px solid transparent; border-top: 12px solid #ef4444;"></div>
                        </div>
                    `;
                    return container;
                }}
            }});
            map.addControl(new WindControl());

            map.eachLayer(function(layer) {{
                if(layer instanceof L.Polyline && !(layer instanceof L.Polygon)) {{
                    all_lines.push(layer);
                    
                    layer.on('click', function(e) {{
                        all_lines.forEach(l => l.setStyle({{opacity: 0.15, weight: 1.0}}));
                        e.target.setStyle({{opacity: 1.0, weight: 4.0}});
                        L.DomEvent.stopPropagation(e);
                    }});
                }}
            }});

            map.eachLayer(function(layer) {{
                if(layer instanceof L.Marker || layer instanceof L.CircleMarker) {{
                    layer.on('click', function(e) {{
                        var mLat = layer.getLatLng().lat;
                        var mLng = layer.getLatLng().lng;
                        var tol = 0.0005; 

                        all_lines.forEach(function(l) {{
                            var match = false;
                            
                            function checkMatch(pts) {{
                                if (!pts) return;
                                for(var i=0; i<pts.length; i++) {{
                                    if (Array.isArray(pts[i])) {{
                                        checkMatch(pts[i]); 
                                    }} else if (pts[i].lat !== undefined) {{
                                        var dLat = Math.abs(pts[i].lat - mLat);
                                        var dLng = Math.abs(pts[i].lng - mLng);
                                        if (dLat < tol && dLng < tol) {{
                                            match = true;
                                        }}
                                    }}
                                }}
                            }}
                            
                            checkMatch(l.getLatLngs());

                            if(match) {{
                                l.setStyle({{opacity: 1.0, weight: 4.0}});
                            }} else {{
                                l.setStyle({{opacity: 0.15, weight: 1.0}});
                            }}
                        }});

                        L.DomEvent.stopPropagation(e);
                    }});
                }}
            }});
            
            map.on('click', function(e) {{
                all_lines.forEach(l => l.setStyle({{opacity: 1.0, weight: 1.5}}));
            }});
        }}
    }}, 1000);
    </script>
    """
    m.get_root().html.add_child(folium.Element(odaklanma_ve_pusula_js))

    components.html(m._repr_html_(), height=550)

with tab2:
    if st.session_state.gorev_emri:
        if "Hata" in st.session_state.gorev_emri:
            st.error(f"SİSTEM HATASI: {st.session_state.gorev_emri['Hata']}")
        else:
            st.success("Operasyon planlaması başarıyla tamamlandı. Çözüm özeti aşağıdadır.")

            if dusurulmus_noktalar:
                st.warning(
                    f"⚠️ **Şu hedef(ler) rota dışına alındı** (rüzgar hızı/menzil nedeniyle ulaşılamıyor): "
                    f"`{'`, `'.join(dusurulmus_noktalar)}`\n\n"
                    f"Diğer {len(sirali_gorevler)} görev öncelikli olarak planlandı. "
                    f"Rüzgar koşulları veya İHA menzilini gözden geçirmeniz önerilir."
                )
            
            if sirali_gorevler:
                fiziksel_iha_sureleri = {}
                
                for iha, veri in sirali_gorevler:
                    fiziksel_id = iha.split("_Sefer_")[0] 
                    if fiziksel_id not in fiziksel_iha_sureleri:
                        fiziksel_iha_sureleri[fiziksel_id] = 0.0
                    fiziksel_iha_sureleri[fiziksel_id] += veri['Uçuş Süresi']
                
                gercek_es_zamanli_sure = max(fiziksel_iha_sureleri.values()) if fiziksel_iha_sureleri else 0
                toplam_kumulatif_sure = sum([veri['Uçuş Süresi'] for iha, veri in sirali_gorevler])
                zaman_tasarrufu = toplam_kumulatif_sure - gercek_es_zamanli_sure
                
                st.markdown("#### Optimizasyon Çözüm Analizi")
                st.info("Otonom optimizasyon algoritması, görev dağılımını başarıyla tamamlamıştır. Filodaki aktif unsurların paralel ve kümülatif görev icra etmesi planlanmış, geleneksel (tekli) sevk yöntemine kıyasla önemli ölçüde zaman tasarrufu sağlanmıştır.")
                
                mc1, mc2, mc3 = st.columns(3)
                
                mc1.metric("Eşzamanlı Operasyon Süresi", f"{gercek_es_zamanli_sure:.1f} dk", 
                           help="Fiziksel İHA'ların kümülatif sorti toplamları baz alınmıştır. Operasyon, üsse en son dönen İHA iniş yaptığında biter.")
                
                mc2.metric("Ardışık (Geleneksel) Uçuş Süresi", f"{toplam_kumulatif_sure:.1f} dk", 
                           help="Tüm görevlerin tek bir İHA ile sırayla (ardışık olarak) yapılması durumunda harcanacak teorik toplam süredir.")
                
                tasarruf_yuzdesi = (zaman_tasarrufu / toplam_kumulatif_sure) * 100 if toplam_kumulatif_sure > 0 else 0
                mc3.metric("Optimizasyon Zaman Tasarrufu", f"{zaman_tasarrufu:.1f} dk", 
                           delta=f"%{tasarruf_yuzdesi:.1f} Verimlilik Artışı", 
                           help="Eşzamanlı filo yönetimi sayesinde kazanılan net zamandır.")
            
            st.markdown("---")
            
            st.markdown("#### Filo Görev Dağılım Tablosu")
            
            hc1, hc2, hc3, hc4, hc5 = st.columns([3, 2, 2, 2, 2])
            hc1.markdown("**Atanan Unsur**")
            hc2.markdown("**Faydalı Yük (kg)**")
            hc3.markdown("**Hesaplanan Süre**")
            hc4.markdown("**Durak Sayısı**")
            hc5.markdown("**Harita İzleme**")
            st.markdown("---")
            
            for iha, veri in sirali_gorevler:
                c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 2, 2])
                c1.write(format_iha_isim(iha))
                c2.write(str(yuk_temizle(veri['Yük'])))
                c3.write(f"{veri['Uçuş Süresi']:.1f} dk")
                c4.write(str(len(veri['Rota'].split(" ➔ ")) - 2))
                
                if c5.button("Haritada İncele", key=f"btn_{iha}"):
                    st.session_state.secili_rota = iha
                    st.session_state.haritaya_git = True
                    time.sleep(0.1) 
                    st.rerun()
                        
                st.markdown("<div class='custom-row'></div>", unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("#### Detaylı Sefer Yönergeleri")

            AR = "#3b82f6"
            BK = "#1e3a5f"
            r, g, b = 59, 130, 246


            tum_html = ""
            for idx, (iha, veri) in enumerate(sirali_gorevler):
                ar, bk = AR, BK
                duraklari = veri["Rota"].split(" \u27a4 ")
                yukkg = yuk_temizle(veri['Yük'])
                sure = veri['Uçuş Süresi']
                durak_sayisi = len(duraklari) - 2

                wp = ""
                for j, durak in enumerate(duraklari):
                    is_base = (durak == "BASE_ATATURK")
                    etiket = "USSE" if is_base else durak.replace("_", " ")
                    icon = "&#127968;" if is_base else "&#128205;"
                    fg = "#94a3b8" if is_base else "#f1f5f9"
                    bg = "rgba(255,255,255,0.05)" if is_base else f"rgba({r},{g},{b},0.18)"
                    bd = "#30363d" if is_base else ar + "66"
                    wp += f"<span style='display:inline-flex;align-items:center;background:{bg};border:1px solid {bd};border-radius:8px;padding:5px 13px;color:{fg};font-size:12px;font-weight:600;white-space:nowrap;font-family:monospace;'>{icon} {etiket}</span>"
                    if j < len(duraklari) - 1:
                        wp += f"<span style='color:{ar};font-size:16px;margin:0 3px;'>&#10148;</span>"

                tum_html += f"""
<div style='background:linear-gradient(135deg,{bk}cc 0%,#0d1117 100%);border:1px solid {ar}55;border-left:4px solid {ar};border-radius:12px;padding:18px 22px;margin-bottom:14px;'>
  <div style='display:flex;align-items:center;gap:10px;margin-bottom:14px;flex-wrap:wrap;'>
    <span style='font-size:15px;font-weight:800;color:{ar};letter-spacing:0.5px;'>&#9992; {format_iha_isim(iha)}</span>
    <span style='background:{ar}22;border:1px solid {ar}44;border-radius:20px;padding:3px 12px;font-size:12px;color:{ar};font-weight:700;'>&#9201; {sure:.1f} dk</span>
    <span style='background:rgba(255,255,255,0.05);border:1px solid #30363d;border-radius:20px;padding:3px 12px;font-size:12px;color:#94a3b8;font-weight:600;'>&#128230; {yukkg:.1f} kg</span>
    <span style='background:rgba(255,255,255,0.03);border:1px solid #1e293b;border-radius:20px;padding:3px 12px;font-size:12px;color:#64748b;'>{durak_sayisi} durak</span>
  </div>
  <div style='display:flex;align-items:center;flex-wrap:wrap;gap:6px;background:rgba(0,0,0,0.28);border-radius:8px;padding:12px 14px;'>
    {wp}
  </div>
</div>"""

            st.markdown(tum_html, unsafe_allow_html=True)

                
    st.markdown("""
        <div style='background-color: #161b22; padding: 12px; border-radius: 6px; border-left: 4px solid #3b82f6; margin-top: 30px; margin-bottom: 15px;'>
            <h4 style='margin:0; color: #e2e8f0; font-size: 17px; letter-spacing: 0.5px;'>Sistem Veritabanı Kayıtları</h4>
        </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.hedefler:
        df = pd.DataFrame(st.session_state.hedefler)
        st.dataframe(df.rename(columns={"isim":"Hedef İsmi","tip":"Kategori","lat":"Enlem (N)","lon":"Boylam (E)","talep":"Talep (kg)"}), use_container_width=True, hide_index=True)
    else:
        st.write("Veritabanında aktif kayıt bulunmamaktadır.")

with tab3:
    if st.session_state.gorev_emri:
        if "Hata" not in st.session_state.gorev_emri:
            st.markdown("#### Filo Lojistik ve Operasyonel Yük Analizi")
            st.write("Görseller, sistem tarafından hesaplanan görev dağılımlarının operasyonel yoğunluğunu temsil etmektedir.")
            
            grafik_verisi = []
            kullanilan_toplam_kapasite = 0.0
            
            for iha, veri in sirali_gorevler:
                sayisal_yuk = yuk_temizle(veri['Yük']) 
                kullanilan_toplam_kapasite += sayisal_yuk
                
                grafik_verisi.append({
                    "İHA": format_iha_isim(iha), 
                    "Yük (kg)": sayisal_yuk,
                    "Uçuş Süresi (dk)": veri['Uçuş Süresi']
                })
            
            df_grafik = pd.DataFrame(grafik_verisi)
            
            col_g1, col_g2 = st.columns(2)
            
            with col_g1:
                fig_yuk = px.bar(df_grafik, x="İHA", y="Yük (kg)", text_auto=True, 
                                 title="Taşınan Faydalı Yük Dağılımı",
                                 color_discrete_sequence=["#3b82f6"]) 
                fig_yuk.update_layout(template="plotly_dark", xaxis_title="Hava Unsurları", yaxis_title="Kütle (kg)")
                st.plotly_chart(fig_yuk, use_container_width=True)
                
            with col_g2:
                fig_sure = px.bar(df_grafik, x="İHA", y="Uçuş Süresi (dk)", text_auto='.1f', 
                                  title="Tahmini Operasyon Süreleri",
                                  color_discrete_sequence=["#10b981"]) 
                fig_sure.update_layout(template="plotly_dark", xaxis_title="Hava Unsurları", yaxis_title="Süre (Dakika)")
                st.plotly_chart(fig_sure, use_container_width=True)
                
            st.markdown("---")
            st.markdown("#### Filo Toplam Kapasite Tüketim Oranı")
            
            kullanim_orani = (kullanilan_toplam_kapasite / filo_toplam_kapasite) * 100 if filo_toplam_kapasite > 0 else 0
            
            st.write(f"**Aktif Taşıma Kapasitesi Kullanımı:** %{kullanim_orani:.1f} ({kullanilan_toplam_kapasite:.1f} kg / {filo_toplam_kapasite} kg)")
            st.progress(min(kullanim_orani / 100.0, 1.0))
    else:
        st.info("Sistem Bilgisi: Grafiklerin derlenebilmesi için algoritmanın yürütülmüş olması gerekmektedir.")