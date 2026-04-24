Bilgisayarınızda Python 3.8 veya üzeri bir sürümün yüklü olduğundan emin olun. Yazılımı çalıştırmak için aşağıdaki adımları uygulayarak gerekli kütüphaneleri kurmanız gerekmektedir.

Komut satırını (Terminal/CMD) açın ve projenin (bu dosyanın) bulunduğu dizine gidin:

cd path/to/uygulama


Gerekli kütüphaneleri tek seferde kurmak için aşağıdaki komutu çalıştırın:

pip install -r requirements.txt


Çalıştırma:

Gerekli kurulumları tamamladıktan sonra yazılımın arayüzünü başlatmak için aşağıdaki komutu çalıştırın:

streamlit run arayuz.py


*(Not: Eğer üstteki komut "komut bulunamadı" (command not found) hatası verirse veya Streamlit ortam değişkenlerine (PATH) ekli değilse, alternatif olarak aşağıdaki komutu kullanabilirsiniz:)*

python -m streamlit run arayuz.py

Komutu çalıştırdığınızda, tarayıcınızda otomatik olarak Komuta Merkezi arayüzü açılacaktır (Genellikle http://localhost:8501 adresinde).


Proje Kod Dosyaları Yapısı:

arayuz.py: Arayüzün, harita gösteriminin ve kullanıcı etkileşiminin sağlandığı ana modül.

optimizasyon.py: OR-Tools kullanılarak VRP matematiksel modelinin çözüldüğü ve rotaların hesaplandığı modül.

matematik\_motoru.py: Koordinatlar arası mesafe, kerteriz ve rüzgar etkenli asimetrik uçuş süresi hesaplamalarının yapıldığı modül.

meteoroloji.py: NOAA API üzerinden canlı hava durumu verilerinin çekildiği modül.

donanim.py: Operasyonda kullanılan İHA (Dasal Falcon C-15) parametrelerini ve limitlerini barındıran modül.