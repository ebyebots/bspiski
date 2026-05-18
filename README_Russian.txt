BSpiski: Country, L7 Anti-Flood — ИНСТРУКЦИЯ (РУССКИЙ)


Скрипт собирает белые списки (разрешённые сети для сайта) и чёрные drop-списки
(IP и сети для блокировки), затем сохраняет готовые файлы для сервера.

Подробнее на примере, как это работает, объяснил в блоге:
https://ebyebots.ru/blog/belye-spiski-po-stranam-besplatnaya-zashhita-sajta-ot-ddos-atak-l7-http-flood-na-servere-s-1-cpu-1-gb-ram


--------------------------------------------------------------------------------
СТРУКТУРА ПАПОК
--------------------------------------------------------------------------------

belie spiski\                          ← корень проекта (все пути от него)

  RUN\
    BSpiski_Country_L7_Anti-Flood.py   ← скрипт (если установлен Python)
    BSpiski_Country_L7_Anti-Flood.exe  ← программа без Python (после сборки)
    build_exe.bat                      ← пересборка .exe (нужен Python)

  IP Database\                         ← ВСЕ ИСХОДНЫЕ ДАННЫЕ (сюда кладёте базы)
                                       взяты с https://github.com/sapics/ip-location-db#country

    All countries\                     ← GeoIP CSV по всем странам
      *ipv4*.csv, *ipv6*.csv           формат: start_ip, end_ip, код_страны
                                         при запуске выбираете страну (RU, DE…)

    Manual list of GOOD ASN bots\      ← «хорошие» боты (Google, Yandex и другие)
                                       пример ASN 15169 Google:
                                       https://2ip.ru/as/15169/ → https://2ip.ru/as/15169.json
      *.json                           формат: prefixes[] → ipv4Prefix / ipv6Prefix
                                         попадают в БЕЛЫЙ список

    Manual list of BAD ASN bot networks\  ← ручные плохие сети
                                       пример ASN 35048 Biterika:
                                       https://2ip.ru/as/35048/ → https://2ip.ru/as/35048.json
      *.json                           те же поля ipv4Prefix / ipv6Prefix
                                         попадают в drop_ipv4 / drop_ipv6

    Spam IP addresses during a DDoS attack\  ← спам / DDoS IP
                                       https://jeroen.steeman.org/Level4_IP_Block_List.txt
                                       и blocklist.net
      *.txt                            по одному IP на строку (# — комментарий)
      *.csv                            1-й столбец — IP (разделитель ; или ,)

    codes_countries.txt                ← справочник кодов стран (RU - Russian Federation…)
                                         для подсказки при выборе страны

  Language\                            ← язык интерфейса консоли
    ru.ini, en.ini                     тексты сообщений (можно править)
    settings.ini                       создаётся после первого выбора языка
                                         удалите файл — спросит язык снова

  bspiski\                             ← РЕЗУЛЬТАТ (создаётся скриптом)
    ipv4.txt, ipv6.txt                 белый список (страна + хорошие боты)
    drop_ipv4.txt                      блокировка IPv4 (спам + плохие JSON)
    drop_ipv6.txt                      блокировка IPv6 (только плохие JSON)

  bs.sh                                ← скрипт firewall для Linux-сервера
                                         (на Windows не запускается)

  ReadMe\
    README_Russian.txt                 эта инструкция
    README_English.txt                 инструкция на английском


--------------------------------------------------------------------------------
КАК ЗАПУСТИТЬ (WINDOWS)
--------------------------------------------------------------------------------

1. Распакуйте весь проект целиком — папки RUN, IP Database, Language должны
   лежать рядом в одной папке «belie spiski».

2. Заполните IP Database (см. выше).

3. Запуск БЕЗ Python:
   • Дважды щёлкните:  RUN\BSpiski_Country_L7_Anti-Flood.exe

   Запуск С Python:
   • Откройте cmd/PowerShell:
     cd "путь\belie spiski\RUN"
     python "BSpiski_Country_L7_Anti-Flood.py"

4. Первый запуск:
   • Выберите язык: 1 — Русский, 2 — English
   • Выберите страну для белого списка: Enter/Y — RU, или код (DE, US…)

5. Дождитесь окончания. Нажмите Enter в конце.

6. Готовые файлы — в папке bspiski\


--------------------------------------------------------------------------------
КАК ПЕРЕНЕСТИ НА СЕРВЕР (LINUX)
--------------------------------------------------------------------------------

Создаем папку bspiski, у меня такой путь: /etc/iptables/bspiski, кидаем содержимое из скрипта, папка bspiski

ipv4.txt

ipv6.txt

drop_ipv4.txt

drop_ipv6.txt

bs.sh

Даем скрипту права на выполнение

sudo chmod +x /etc/iptables/bspiski/bs.sh

И запускаем его

sudo /etc/iptables/bspiski/bs.sh


--------------------------------------------------------------------------------
ВАЖНО
--------------------------------------------------------------------------------

• Не запускайте .exe из другой папки — без соседних IP Database и Language
  скрипт не найдёт данные.

• drop_ipv4.txt может содержать и одиночные IP, и подсети (1.2.3.4 или 10.0.0.0/24).

• Дубликаты в спам/drop убираются только при ТОЧНОМ совпадении строки.

• Сменить язык: удалите Language\settings.ini и запустите снова.

• Пересборка .exe после правок .py: запустите RUN\build_exe.bat
  (нужен установленный Python и PyInstaller).


================================================================================
