import json
import base64
import os
import urllib.parse
from datetime import datetime

BRAND = "Relocate VPN"
TG_LINK = "https://t.me/RelocateVPN"
REPO = os.getenv('GITHUB_REPOSITORY', 'username/repo')
RAW_URL = f"https://raw.githubusercontent.com/{REPO}/main"
BLOB_URL = f"https://github.com/{REPO}/blob/main"
PAGES_BASE = f"https://{REPO.split('/')[0]}.github.io/{REPO.split('/')[1]}"

BLOCK_SITES = ["win-spy", "torrent", "category-ads"]
PROXY_SITES = ["github", "twitch-ads", "youtube", "telegram"]
DIRECT_SITES = ["private", "category-ru", "microsoft", "apple", "google-play", "epicgames", "riot", "escapefromtarkov", "steam", "twitch", "pinterest", "faceit"]
DIRECT_IPS = ["private", "direct"]

# Extra block domains and IP CIDRs added across all builders
BLOCK_DOMAINS = [
    "max.ru",
    "web.max.ru",
    "download.max.ru",
    "help.max.ru",
    "business.max.ru",
    "dev.max.ru",
    "legal.max.ru",
    "platform-api.max.ru",
    "st.max.ru",
    "ru.oneme.app",
    "oneme.ru",
    "api.oneme.ru",
    "ws-api.oneme.ru",
    "calls.okcdn.ru",
    "api.max.ru",
    "botapi.max.ru",
    "link.max.ru",
    "i.max.ru",
    "i.oneme.ru",
    "iu.max.ru",
    "iu.oneme.ru",
    "iusmile.max.ru",
    "iusmile.oneme.ru",
    "notify-gu.oneme.ru",
    "proxy.oneme.ru",
    "st-test.oneme.ru",
    "api-gost.oneme.ru",
    "fgost.oneme.ru",
    "vu.mycdn.me",
    "pimg.mycdn.me",
    "tracker-api.vk-analytics.ru",
    "sdk-api.apptracer.ru",
]

BLOCK_IP_CIDRS = [
    "185.16.148.119/32",
    "185.16.148.121/32",
    "217.20.152.209/32",
    "217.20.155.50/32",
    "217.20.156.179/32",
    "185.16.148.0/23",
    "185.16.150.0/23",
    "217.20.144.0/22",
    "217.20.148.0/24",
    "217.20.149.0/24",
    "217.20.150.0/23",
    "217.20.152.0/22",
    "217.20.156.0/23",
    "217.20.158.0/24",
    "217.20.159.0/24",
]

def build_clash():
    rules = ["# Кастомный роутинг " + BRAND, "rules:"]
    # Extra exact-domain block rules
    for d in BLOCK_DOMAINS:
        rules.append(f"  - DOMAIN,{d},REJECT")
    # Extra IP-CIDR block rules
    for cidr in BLOCK_IP_CIDRS:
        rules.append(f"  - IP-CIDR,{cidr},REJECT,no-resolve")
    # Geosite block / proxy / direct
    for s in BLOCK_SITES: rules.append(f"  - GEOSITE,{s},REJECT")
    for s in PROXY_SITES: rules.append(f"  - GEOSITE,{s},PROXY")
    for s in DIRECT_SITES: rules.append(f"  - GEOSITE,{s},DIRECT")
    for ip in DIRECT_IPS: rules.append(f"  - GEOIP,{ip},DIRECT,no-resolve")
    rules.append("  - MATCH,PROXY")
    return "\n".join(rules) + "\n"

def build_singbox():
    return json.dumps({
        "route": {
            "auto_detect_interface": True,
            "rules": [
                {"domain": BLOCK_DOMAINS, "outbound": "block"},
                {"ip_cidr": BLOCK_IP_CIDRS, "outbound": "block"},
                {"geosite": BLOCK_SITES, "outbound": "block"},
                {"geosite": PROXY_SITES, "outbound": "proxy"},
                {"geosite": DIRECT_SITES, "outbound": "direct"},
                {"geoip": DIRECT_IPS, "outbound": "direct"}
            ],
            "final": "proxy"
        }
    }, indent=2, ensure_ascii=False)

def build_xray():
    return json.dumps({
        "routing": {
            "domainStrategy": "IPIfNonMatch",
            "rules": [
                {"type": "field", "outboundTag": "block", "domain": [f"full:{d}" for d in BLOCK_DOMAINS]},
                {"type": "field", "outboundTag": "block", "ip": BLOCK_IP_CIDRS},
                {"type": "field", "outboundTag": "block", "domain": [f"geosite:{s}" for s in BLOCK_SITES]},
                {"type": "field", "outboundTag": "proxy", "domain": [f"geosite:{s}" for s in PROXY_SITES]},
                {"type": "field", "outboundTag": "direct", "domain": [f"geosite:{s}" for s in DIRECT_SITES]},
                {"type": "field", "outboundTag": "direct", "ip": [f"geoip:{ip}" for ip in DIRECT_IPS]}
            ]
        }
    }, indent=2, ensure_ascii=False)

def build_shadowrocket():
    rules = [
        "[General]",
        "bypass-system = true",
        "skip-proxy = 192.168.0.0/16, 10.0.0.0/8, 172.16.0.0/12, localhost, *.local",
        "ipv6 = false",
        "",
        "[Rule]"
    ]
    # Extra exact-domain block rules
    for d in BLOCK_DOMAINS:
        rules.append(f"DOMAIN,{d},REJECT")
    # Extra IP-CIDR block rules
    for cidr in BLOCK_IP_CIDRS:
        rules.append(f"IP-CIDR,{cidr},REJECT")
    for s in BLOCK_SITES: rules.append(f"GEOSITE,{s},REJECT")
    for s in PROXY_SITES: rules.append(f"GEOSITE,{s},PROXY")
    for s in DIRECT_SITES: rules.append(f"GEOSITE,{s},DIRECT")
    for ip in DIRECT_IPS: rules.append(f"GEOIP,{ip},DIRECT")
    rules.append("FINAL,PROXY")
    return "\n".join(rules) + "\n"

def build_happ():
    happ_block_sites = (
        [f"geosite:{s}" for s in BLOCK_SITES]
        + [f"domain:{d}" for d in BLOCK_DOMAINS]
    )
    happ_cfg = {
        "Name": "Relocate Rules",
        "RouteOrder": "block-direct-proxy",
        "GlobalProxy": "true",
        "RemoteDNSType": "DoU",
        "DomesticDNSType": "DoU",
        "RemoteDNSDomain": "https://dns.google/dns-query",
        "RemoteDNSIP": "8.8.8.8",
        "DomesticDNSDomain": "https://common.dot.dns.yandex.net/dns-query",
        "DomesticDNSIP": "77.88.8.8",
        "Geoipurl": f"{BLOB_URL}/data/geoip.dat",
        "Geositeurl": f"{BLOB_URL}/data/geosite.dat",
        "LastUpdated": "",
        "DnsHosts": {},
        "FakeDNS": "true",
        "UseChunkFiles": "true",
        "DirectSites": [f"geosite:{s}" for s in DIRECT_SITES],
        "DirectIp": [f"geoip:{ip}" for ip in DIRECT_IPS],
        "ProxySites": ["geosite:twitch-ads"],
        "ProxyIp": [],
        "BlockSites": happ_block_sites,
        "BlockIp": BLOCK_IP_CIDRS,
        "DomainStrategy": "IPIfNonMatch",
    }
    js_str = json.dumps(happ_cfg, separators=(",", ":"), ensure_ascii=False)
    b64 = base64.b64encode(js_str.encode("utf-8")).decode("utf-8")
    return happ_cfg, f"happ://routing/add/{b64}"

def _pages_redirect_html(title, deeplink, description):
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <meta http-equiv="refresh" content="0; url={deeplink}">
  <title>{title}</title>
  <script>window.location.href = "{deeplink}";</script>
</head>
<body>
  <p>{description}</p>
  <p>Если редирект не сработал автоматически, <a href="{deeplink}">нажмите здесь</a>.</p>
</body>
</html>
"""

def build_pages(happ_link, clash_deeplink, sr_deeplink):
    os.makedirs("../docs", exist_ok=True)
    pages = [
        ("../docs/happ.html",         "Установить в Happ",         happ_link,        "Открытие диплинк-ссылки для Happ..."),
        ("../docs/clash.html",         "Импорт в Clash",            clash_deeplink,   "Открытие диплинк-ссылки для Mihomo/Clash..."),
        ("../docs/shadowrocket.html",  "Импорт в Shadowrocket",     sr_deeplink,      "Открытие диплинк-ссылки для Shadowrocket..."),
    ]
    for path, title, deeplink, desc in pages:
        with open(path, "w", encoding="utf-8") as f:
            f.write(_pages_redirect_html(title, deeplink, desc))

    index_html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <title>Relocate VPN — Routing</title>
</head>
<body>
  <h1>Relocate VPN Routing</h1>
  <p>Выберите клиент для быстрой установки:</p>
  <ul>
    <li><a href="happ.html">Happ</a></li>
    <li><a href="clash.html">Mihomo / Clash</a></li>
    <li><a href="shadowrocket.html">Shadowrocket</a></li>
  </ul>
</body>
</html>
"""
    with open("../docs/index.html", "w", encoding="utf-8") as f:
        f.write(index_html)

def build_readme(happ_link, clash_deeplink, sr_deeplink):
    happ_pages_url   = f"{PAGES_BASE}/happ.html"
    clash_pages_url  = f"{PAGES_BASE}/clash.html"
    sr_pages_url     = f"{PAGES_BASE}/shadowrocket.html"

    md = f"""# Кастомный роутинг {BRAND} для приложений

Быстрый и универсальный роутинг: "хирургическая" фильтрация, всё нужное — разблокировано, а ненужное — заблокировано.  
Без утечек и блокировок локальных ресурсов.

**Таргет-страна:** Россия 🇷🇺 

---

## 📦 Релизы (Архивы файлов)
Каждые 6 часов выпускается релиз с архивами: [Смотреть Releases](https://github.com/{REPO}/releases)
- \`configs.zip\` — все готовые файлы маршрутизации
- \`geosite.zip\` — актуальная база доменов (geosite.dat)
- \`geoip.zip\` — актуальная база IP (geoip.dat)

---

## 🚀 Установка для Happ

| Способ | Ссылка | Описание |
| :--- | :--- | :--- |
| 📱 **Быстрая установка** | [![Установить](https://img.shields.io/badge/Статическая_ссылка-1679A7?style=for-the-badge)]({happ_pages_url}) | Редиректит на диплинк, нужно открыть прямо на устройстве |
| 🔗 **DEFAULT.DEEPLINK** | [Просмотр диплинк-ссылки]({RAW_URL}/configs/happ.deeplink) | Диплинк ссылка в текстовом формате |
| 📄 **DEFAULT.JSON** | [happ.json]({RAW_URL}/configs/happ.json) | Незашифрованный JSON-конфиг роутинга |

## 🚀 Установка для Mihomo (Clash, ClashFX, Koala Clash, Prizrak-Box)

| Способ | Ссылка | Описание |
| :--- | :--- | :--- |
| 📱 **Быстрая установка** | [![Установить](https://img.shields.io/badge/Импорт_в_Clash-1679A7?style=for-the-badge)]({clash_pages_url}) | Автоматический импорт в приложения экосистемы Clash |
| 🔗 **DEFAULT.DEEPLINK** | [Просмотр диплинк-ссылки]({RAW_URL}/configs/clash.deeplink) | Диплинк ссылка в текстовом формате |
| 📄 **CONFIG.YAML** | [clash.yaml]({RAW_URL}/configs/clash.yaml) | Сырой файл правил маршрутизации |

## 🚀 Установка для Shadowrocket

| Способ | Ссылка | Описание |
| :--- | :--- | :--- |
| 📱 **Быстрая установка** | [![Установить](https://img.shields.io/badge/Импорт_в_Shadowrocket-1679A7?style=for-the-badge)]({sr_pages_url}) | Автоматическое добавление конфигурации |
| 🔗 **DEFAULT.DEEPLINK** | [Просмотр диплинк-ссылки]({RAW_URL}/configs/shadowrocket.deeplink) | Диплинк ссылка в текстовом формате |
| 📄 **CONFIG.CONF** | [shadowrocket.conf]({RAW_URL}/configs/shadowrocket.conf) | Ссылка на конфиг для ручного импорта |

## 🚀 Установка для Sing-box (Hiddify, Nekobox, Nekoray, Throne)

| Способ | Ссылка | Описание |
| :--- | :--- | :--- |
| 📄 **CONFIG.JSON** | [singbox.json]({RAW_URL}/configs/singbox.json) | Скопируйте ссылку и вставьте в Custom Routing правила |

## 🚀 Установка для Xray/V2ray (v2rayNG, v2rayU, v2raytun, Streisand)

| Способ | Ссылка | Описание |
| :--- | :--- | :--- |
| 📄 **CONFIG.JSON** | [xray.json]({RAW_URL}/configs/xray.json) | Скопируйте ссылку для ручного импорта правил |

---

🔗 **Наш VPN-сервис:** [Telegram]({TG_LINK})

---

## 🗂 Прямые ссылки (Raw)

| Файл | Ссылка |
| :--- | :--- |
| `geoip.dat` | [{RAW_URL}/data/geoip.dat]({RAW_URL}/data/geoip.dat) |
| `geosite.dat` | [{RAW_URL}/data/geosite.dat]({RAW_URL}/data/geosite.dat) |
| `happ.deeplink` | [{RAW_URL}/configs/happ.deeplink]({RAW_URL}/configs/happ.deeplink) |
| `happ.json` | [{RAW_URL}/configs/happ.json]({RAW_URL}/configs/happ.json) |
| `clash.deeplink` | [{RAW_URL}/configs/clash.deeplink]({RAW_URL}/configs/clash.deeplink) |
| `clash.yaml` | [{RAW_URL}/configs/clash.yaml]({RAW_URL}/configs/clash.yaml) |
| `shadowrocket.deeplink` | [{RAW_URL}/configs/shadowrocket.deeplink]({RAW_URL}/configs/shadowrocket.deeplink) |
| `shadowrocket.conf` | [{RAW_URL}/configs/shadowrocket.conf]({RAW_URL}/configs/shadowrocket.conf) |
| `singbox.json` | [{RAW_URL}/configs/singbox.json]({RAW_URL}/configs/singbox.json) |
| `xray.json` | [{RAW_URL}/configs/xray.json]({RAW_URL}/configs/xray.json) |

---
*Сгенерировано автоматически системой CI/CD: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC*
"""
    with open("../README.md", "w", encoding="utf-8") as f:
        f.write(md)


def main():
    os.makedirs("../configs", exist_ok=True)
    with open("../configs/clash.yaml", "w", encoding="utf-8") as f:
        f.write(build_clash())
    with open("../configs/singbox.json", "w", encoding="utf-8") as f:
        f.write(build_singbox())
    with open("../configs/xray.json", "w", encoding="utf-8") as f:
        f.write(build_xray())
    with open("../configs/shadowrocket.conf", "w", encoding="utf-8") as f:
        f.write(build_shadowrocket())

    happ_json, happ_link = build_happ()
    with open("../configs/happ.json", "w", encoding="utf-8") as f:
        f.write(json.dumps(happ_json, indent=2, ensure_ascii=False))
    with open("../configs/happ.deeplink", "w", encoding="utf-8") as f:
        f.write(happ_link + "\n")

    clash_deeplink = f"clash://install-config?url={urllib.parse.quote(RAW_URL + '/configs/clash.yaml', safe='')}"
    with open("../configs/clash.deeplink", "w", encoding="utf-8") as f:
        f.write(clash_deeplink + "\n")

    sr_deeplink = f"shadowrocket://config/add/{RAW_URL}/configs/shadowrocket.conf"
    with open("../configs/shadowrocket.deeplink", "w", encoding="utf-8") as f:
        f.write(sr_deeplink + "\n")

    build_pages(happ_link, clash_deeplink, sr_deeplink)
    build_readme(happ_link, clash_deeplink, sr_deeplink)


if __name__ == "__main__":
    main()
