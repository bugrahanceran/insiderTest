# AWS EKS Üzerinde Selenium Ölçekleme

## 1. Proje Amacı
Bu projenin temel amacı, Selenium otomasyon testlerini yerel ortam bağımlılığından kurtarmak, Docker container teknolojisi ile izole etmek ve Kubernetes (AWS EKS) üzerinde ölçeklenebilir (scalable) bir altyapıda koşturmaktır.

## 2. Mimari Yapı
Proje, **Server-Client** mimarisine dayalı iki ana Kubernetes bileşeni üzerine kurgulanmıştır:

* **Chrome Node (Server):** Testlerin fiilen koşulduğu, headless Chrome tarayıcılarını barındıran podlar. Resmi `selenium/standalone-chrome` imajı kullanılmıştır.
* **Test Controller (Client):** Python ve Pytest kodlarını içeren, test senaryolarını yöneten ve Chrome Node'lara istek gönderen pod.
* **İletişim:** İki bileşen arasındaki haberleşme Kubernetes **Service (ClusterIP)** objesi üzerinden, `4444` portu ve DNS ismi (`chrome-node-service`) ile sağlanmıştır.

## 3. Geliştirme Süreci (Adım Adım)

### Faz 1: Kodlama ve Test Mantığı
* Python ve `pytest` framework'ü kullanılarak test senaryoları yazıldı.
* `RemoteWebDriver` kullanılarak testlerin uzaktaki bir sunucuda (Grid) koşulması sağlandı.
* Google'ın bot korumasına takılmamak ve altyapıyı stabil test etmek için `the-internet.herokuapp.com` ortamı kullanıldı.

### Faz 2: Containerization (Docker)
* Test Controller için `python:3.9-slim` tabanlı, minimum boyutta bir `Dockerfile` hazırlandı.
* İmaj build edilip Docker Hub (`bugracer/test-controller`) registry'sine pushlandı.
* Chrome Node için endüstri standardı olan resmi Selenium imajları tercih edildi.

### Faz 3: Kubernetes Orkestrasyonu
* **YAML Manifestleri:** Deployment ve Service tanımları yapıldı.
* **Performans Optimizasyonu:** Chrome tarayıcısının çökmemesi için Kubernetes tarafında `volumeMounts` ile paylaşımlı bellek (`/dev/shm`) tanımlandı.
* **Deployment Stratejisi:** Test Controller için `Deployment` objesi kullanıldı ancak iş bitiminde temizlenmesi sağlandı.

### Faz 4: Otomasyon Scripti (Python)
Manuel `kubectl` komutları yerine süreci yöneten akıllı bir Python scripti (`scripts/deploy_and_run.py`) geliştirildi. Bu script şunları sağlar:
* **Dinamik Ölçekleme:** Kullanıcıdan alınan `nodecount` parametresine göre browser sayısını ayarlar.
* **Akıllı Bekleme:** Podlar tamamen `Ready` duruma gelmeden testleri başlatmaz (Race condition engellendi).
* **Log Takibi:** Test loglarını anlık (stream) olarak terminale basar.
* **Otomatik Temizlik:** Test bitiminde `CrashLoopBackOff` hatasını önlemek için Controller podunu siler.

### Faz 5: Bulut Entegrasyonu (AWS EKS)
* **Yönetim:** AWS üzerinde bir EC2 Bastion Host kurularak güvenli erişim sağlandı.
* **IAM Yetkilendirmesi:** Access Key yerine IAM Role kullanılarak güvenlik "Best Practice" uygulandı.
* **Cluster Kurulumu:** `eksctl` aracı ile `t3.small` node tipinde (Selenium bellek ihtiyacı nedeniyle) yönetilen bir Kubernetes kümesi kuruldu.
* **Sonuç:** Proje buluta deploy edildi, testler başarıyla geçti ve kaynaklar maliyet yönetimi için temizlendi.

## 4. Challange

* Chrome container'ın yetersiz bellek hatası vermemesi için.
    * Kubernetes YAML dosyasında `/dev/shm` volume mount işlemi yapıldı.
* Test Controller podunun iş bitince `CrashLoopBackOff` durumuna düşmemesi içim.
    * Python scriptine "test bittiği an deployment'ı sil" (Cleanup) mantığı eklendi.
* Podlar hazır olmadan testin başlamaması için (Connection Refused).
    * Script içerisine `kubectl wait` ve döngüsel `status` kontrolü eklendi.

## 5. Kullanılan Teknolojiler

* **Dil:** Python 3.9
* **Test:** Pytest, Selenium WebDriver
* **Altyapı:** Docker, Kubernetes (K8s)
* **Cloud:** AWS EC2, AWS EKS (Elastic Kubernetes Service)
* **Araçlar:** Git, Kubectl, Eksctl

## 6. Kurulum Komutları Referansı

Aşağıdaki komutlar, projenin yönetildiği EC2 (Bastion Host) makinesinde altyapıyı hazırlamak için kullanılmıştır.

```bash
### kubectl
curl -O [https://s3.us-west-2.amazonaws.com/amazon-eks/1.29.0/2024-01-04/bin/linux/amd64/kubectl](https://s3.us-west-2.amazonaws.com/amazon-eks/1.29.0/2024-01-04/bin/linux/amd64/kubectl)
chmod +x ./kubectl
mkdir -p $HOME/bin && cp ./kubectl $HOME/bin/kubectl && export PATH=$PATH:$HOME/bin
echo 'export PATH=$PATH:$HOME/bin' >> ~/.bashrc

### eksctl
PLATFORM=$(uname -s)_$amd64
curl -sLO "[https://github.com/eksctl-io/eksctl/releases/latest/download/eksctl_$PLATFORM.tar.gz](https://github.com/eksctl-io/eksctl/releases/latest/download/eksctl_$PLATFORM.tar.gz)"
tar -xzf eksctl_$PLATFORM.tar.gz -C /tmp && rm eksctl_$PLATFORM.tar.gz
sudo mv /tmp/eksctl /usr/local/bin

### docker
sudo yum install docker -y
sudo service docker start
sudo usermod -a -G docker ec2-user

### create cluster
eksctl create cluster \
  --name selenium-cluster \
  --region us-east-1 \
  --nodegroup-name standard-workers \
  --node-type t3.small \
  --nodes 2 \
  --nodes-min 1 \
  --nodes-max 3 \
  --managed

### run project
git clone git@github.com:bugrahanceran/insiderTest.git
cd insiderTest
python3 scripts/deploy_and_run.py --nodecount 2

### cleanup
eksctl delete cluster --name selenium-cluster --region us-east-1
```
## 7. Görseller
**Local test passed:**

<img width="641" height="598" alt="Desting for pods to be ready (appuchrote-node)" src="https://github.com/user-attachments/assets/4d0ab7c2-42d4-47c1-bff3-d56cbcf12df0" />


**EC2 instance configuration:**

<img width="1346" height="1180" alt="Pasted Graphic 1" src="https://github.com/user-attachments/assets/c0dfad3b-1d0f-4f5c-ba79-4dbbffd292b9" />



**Cloud Formation:**

<img width="1567" height="1111" alt="Pasted Graphic 6" src="https://github.com/user-attachments/assets/0046166b-f0c5-4294-bb0b-acfd0788c5a5" />



**EKS:**

<img width="1552" height="1102" alt="Pasted Graphic 5" src="https://github.com/user-attachments/assets/9dae7238-f0a5-461d-b03a-935ee65ca1f9" />



**All tests passed:**

<img width="860" height="879" alt="o) Rape got pot on easy (appeast-castrollar (apprtast-csatrollar)" src="https://github.com/user-attachments/assets/f2133b32-39b8-4297-b8a4-a72bc0e86017" />



**Deletion:**

<img width="1574" height="483" alt="Pasted Graphic 7" src="https://github.com/user-attachments/assets/74e2f6e1-cd38-4833-9970-1dd9031a6136" />

