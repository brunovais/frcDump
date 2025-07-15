# Firebase Remote Config Dump

A powerful tool to extract Google credentials from an Android APK file, and dump Firebase Remote Config API.  

---

## 🚀 How to Use

```bash
# 1. Install
pipx install git+https://github.com/brunovais/frcDump.git

# 2. Run the script with --help to get instructions
frcDump --help

```

### Help

```
usage: frcDump [-h] [--apk APK] [-id APPID] [-k APIKEY]

Firebase RemoteConfig Dump

options:
  -h, --help           show this help message and exit
  --apk APK            Path of apk file. Ex: /path/of/apk/file.apk
  -id, --appid APPID   Search remote config by appid. Ex: 0:123455776998:android:123c123a1234f1234ff1a1
  -k, --apikey APIKEY  Google Api Key. Ex: AIzaxxxxxx
```

---

## Requirements

- Python 3.7+
- [apktool](https://ibotpeaches.github.io/Apktool/) installed and available in PATH
- `pipx` module (install below)

---

## Credits

Created by [@brunovais](https://github.com/brunovais) and [@phor3nsic](https://github.com/phor3nsic)
