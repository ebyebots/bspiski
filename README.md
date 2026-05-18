# BSpiski: Country, L7 Anti-Flood 🛡️

**BSpiski** — это автоматизированный скрипт для Linux (iptables/ipset), предназначенный для сбора, фильтрации и объединения баз IP-адресов из различных источников. Он подготавливает оптимизированные списки разрешенных («хороших») и заблокированных («плохих») сетей для организации **бесплатной защиты веб-сайта от DDoS-атак L7 HTTP Flood** на уровне ядра Linux.

Скрипт работает локально и идеально подходит для серверов с минимальной конфигурацией (**1 CPU и 1 ГБ RAM**).

**BSpiski** is an automated script for Linux (iptables/ipset) designed to aggregate, filter, and merge IP address databases from various sources. It prepares optimized lists of allowed ("good") and blocked ("bad") networks to set up **free, kernel-level website protection against L7 DDoS attacks (HTTP Flood)**.

The script runs locally and is perfectly optimized for entry-level server configurations (**1 CPU and 1 GB RAM**).

---

## 📖 Как это работает / How It Works

### 🇷🇺 На русском:
1. **Сбор баз:** Скрипт собирает подсети выбранной страны (GeoIP), актуальные спам/DDoS-базы, списки плохих ASN и верифицированных поисковых ботов (Google, Яндекс и др.).
2. **Генерация списков:** На выходе в папке `bspiski` создаются готовые компактные файлы:
   * **Белый список** (`ipv4.txt` / `ipv6.txt`) — целевая страна + доверенные боты.
   * **Чёрный drop-список** (`drop_ipv4.txt` / `drop_ipv6.txt`) — спам-базы и плохие сети.
3. **Защита на сервере:** Управляющий скрипт `bs.sh` загружает списки в `ipset`. Трафик из белого списка на порты 80/443 пропускается без ограничений, а весь остальной международный трафик и флуд попадают под жесткие лимиты **L7 Anti-Flood** (ограничение соединений, автобан агрессивных гостей и блокировка drop-списков).

### 🇬🇧 In English:
1. **Database Aggregation:** The script collects subnets of the selected country (GeoIP), active spam/DDoS intelligence feeds, bad ASNs lists, and verified search engine bots (Google, Yandex, etc.).
2. **List Generation:** It outputs production-ready files into the `bspiski` folder:
   * **White List** (`ipv4.txt` / `ipv6.txt`) — target country subnets + trusted search crawlers.
   * **Black Drop-List** (`drop_ipv4.txt` / `drop_ipv6.txt`) — active spam feeds and malicious networks.
3. **Server-Side Protection:** The management script `bs.sh` imports these lists into `ipset`. Traffic from the whitelist to ports 80/443 passes seamlessly without restrictions, while all other global traffic and flood signatures hit strict **L7 Anti-Flood** kernel-level rules (rate-limiting per second, automated temporary banning of aggressive guests, and instant drop-actions for the blocklist).

---

## 💡 Кейс и Теория / Case Study & Theory

> 🇷🇺 **Подробный разбор:** Подробнее о том, как реализовать этот метод на своём VPS абсолютно бесплатно, рассказано в блоге: [Белые списки по странам: бесплатная защита сайта от DDoS-атак L7 HTTP Flood](https://ebyebots.ru/blog/belye-spiski-po-stranam-besplatnaya-zashhita-sajta-ot-ddos-atak-l7-http-flood-na-servere-s-1-cpu-1-gb-ram).

> 🇬🇧 **Deep Dive Guide:** For a comprehensive guide on implementation theory, configuration, and kernel-level mechanics, check out the blog post: [Country Whitelists: Free Protection Against L7 HTTP Flood DDoS Attacks](https://ebyebots.ru/blog/belye-spiski-po-stranam-besplatnaya-zashhita-sajta-ot-ddos-atak-l7-http-flood-na-servere-s-1-cpu-1-gb-ram).

---

## 📚 Полная документация / Full Documentation

Полные руководства по детальной настройке и развертыванию доступны в отдельных файлах:  
Comprehensive setup and deployment manuals are available in separate files:

* 🇷🇺 **[Читать документацию на русском языке (README_Russian.txt)](README_Russian.txt)**
* 🇬🇧 **[Read the documentation in English (README_English.txt)](README_English.txt)**
