pip install homeassistant


wget https://github.com/home-assistant/operating-system/releases/download/16.2/haos_ova-16.2.vdi.zip



```bash
# 1. 创建虚拟机
VBoxManage createvm --name "Home_Assistant_OS" --register

NETIF=$(ip -o link show | awk -F': ' '$2 !~ /lo|wl|docker|veth/ {print $2; exit}' | grep en)

# 2. 配置基本参数
VBoxManage modifyvm "Home_Assistant_OS" \
  --ostype "Linux_64" \
  --memory 1024 \
  --cpus 1 \
  --boot1 disk \
  --firmware efi 

VBoxManage modifyvm "Home_Assistant_OS" \
  --nic1 nat \
  --nic2 bridged --bridgeadapter1 $NETIF  # en0 换成你的网卡

VBoxManage modifyvm "Home_Assistant_OS" --natpf1  "homeassistant-web,tcp,,8123,,8123"


VBoxManage showvminfo "Home_Assistant_OS"

# 3. 添加 SATA 控制器并挂载 VDI
VBoxManage storagectl "Home_Assistant_OS" --name "SATA0" --add sata --controller IntelAHCI
VBoxManage storageattach "Home_Assistant_OS" --storagectl "SATA0" \
  --port 0 --device 0 --type hdd --medium "/home/peng/Downloads/home-assistant/haos_ova-16.2.vdi"

# VBoxManage storagectl "Home_Assistant_OS" --remove  --name=SATA0 --controller IntelAHCI  
# 4. 启动
VBoxManage startvm "Home_Assistant_OS" --type headless


VBoxManage showvminfo "Home_Assistant_OS" | grep -E "Autostart|State"

# 5. 开机自启
```bash
# 先完成自启配置，见SuConfig

VBoxManage modifyvm "Home_Assistant_OS" --autostart-enabled on
VBoxManage modifyvm "Home_Assistant_OS" --autostop-type savestate
```





# 研究：
https://www.home-assistant.io/integrations/universal/


