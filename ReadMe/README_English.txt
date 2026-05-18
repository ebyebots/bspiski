================================================================================
  BSpiski: Country, L7 Anti-Flood — GUIDE (ENGLISH)
================================================================================

The script builds whitelists (allowed networks for the site) and black drop-lists
(IPs and networks to block), then saves ready-to-use files for the server.

For a detailed walkthrough with examples, see the blog post:
https://ebyebots.ru/blog/belye-spiski-po-stranam-besplatnaya-zashhita-sajta-ot-ddos-atak-l7-http-flood-na-servere-s-1-cpu-1-gb-ram


--------------------------------------------------------------------------------
FOLDER STRUCTURE
--------------------------------------------------------------------------------

belie spiski\                          ← project root (all paths are relative to it)

  RUN\
    BSpiski_Country_L7_Anti-Flood.py   ← script (if Python is installed)
    BSpiski_Country_L7_Anti-Flood.exe  ← standalone app without Python (after build)
    build_exe.bat                      ← rebuild .exe (Python required)

  IP Database\                         ← ALL SOURCE DATA (place your databases here)
                                       from https://github.com/sapics/ip-location-db#country

    All countries\                     ← GeoIP CSV for all countries
      *ipv4*.csv, *ipv6*.csv           format: start_ip, end_ip, country_code
                                         at run time you choose a country (RU, DE…)

    Manual list of GOOD ASN bots\      ← “good” bots (Google, Yandex, and others)
                                       example ASN 15169 Google:
                                       https://2ip.ru/as/15169/ → https://2ip.ru/as/15169.json
      *.json                           format: prefixes[] → ipv4Prefix / ipv6Prefix
                                         go into the WHITELIST

    Manual list of BAD ASN bot networks\  ← manual bad networks
                                       example ASN 35048 Biterika:
                                       https://2ip.ru/as/35048/ → https://2ip.ru/as/35048.json
      *.json                           same fields ipv4Prefix / ipv6Prefix
                                         go into drop_ipv4 / drop_ipv6

    Spam IP addresses during a DDoS attack\  ← spam / DDoS IPs
                                       https://jeroen.steeman.org/Level4_IP_Block_List.txt
                                       and blocklist.net
      *.txt                            one IP per line (# — comment)
      *.csv                            1st column — IP (separator ; or ,)

    codes_countries.txt                ← country code reference (RU - Russian Federation…)
                                         for hints when choosing a country

  Language\                            ← console UI language
    ru.ini, en.ini                     message texts (editable)
    settings.ini                       created after first language choice
                                         delete the file to be asked again

  bspiski\                             ← OUTPUT (created by the script)
    ipv4.txt, ipv6.txt                 whitelist (country + good bots)
    drop_ipv4.txt                      IPv4 block list (spam + bad JSON)
    drop_ipv6.txt                      IPv6 block list (bad JSON only)

  bs.sh                                ← firewall script for Linux server
                                         (does not run on Windows)

  ReadMe\
    README_Russian.txt                 this guide in Russian
    README_English.txt                 this guide in English


--------------------------------------------------------------------------------
HOW TO RUN (WINDOWS)
--------------------------------------------------------------------------------

1. Unpack the entire project — folders RUN, IP Database, and Language must
   sit together in one “belie spiski” folder.

2. Fill IP Database (see above).

3. Run WITHOUT Python:
   • Double-click:  RUN\BSpiski_Country_L7_Anti-Flood.exe

   Run WITH Python:
   • Open cmd/PowerShell:
     cd "path\belie spiski\RUN"
     python "BSpiski_Country_L7_Anti-Flood.py"

4. First run:
   • Choose language: 1 — Russian, 2 — English
   • Choose country for whitelist: Enter/Y — RU, or code (DE, US…)

5. Wait until finished. Press Enter at the end.

6. Output files are in the bspiski\ folder


--------------------------------------------------------------------------------
HOW TO DEPLOY ON SERVER (LINUX)
--------------------------------------------------------------------------------

Create a bspiski folder; example path: /etc/iptables/bspiski. Copy the contents
from the script output — the bspiski folder:

ipv4.txt

ipv6.txt

drop_ipv4.txt

drop_ipv6.txt

bs.sh

Make the script executable:

sudo chmod +x /etc/iptables/bspiski/bs.sh

Then run it:

sudo /etc/iptables/bspiski/bs.sh


--------------------------------------------------------------------------------
IMPORTANT
--------------------------------------------------------------------------------

• Do not run .exe from another folder — without neighboring IP Database and
  Language folders the script will not find data.

• drop_ipv4.txt may contain single IPs and subnets (1.2.3.4 or 10.0.0.0/24).

• Duplicates in spam/drop lists are removed only on EXACT string match.

• To change language: delete Language\settings.ini and run again.

• Rebuild .exe after editing .py: run RUN\build_exe.bat
  (requires installed Python and PyInstaller).


================================================================================
