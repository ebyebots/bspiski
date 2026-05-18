import os
import sys
import csv
import glob
import json
import ipaddress
import configparser

# BSpiski: Country, L7 Anti-Flood
# -----------------------------
# НАСТРОЙКИ (скрипт/exe в RUN/, данные в IP Database/, вывод в bspiski/)
# -----------------------------
def _script_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


SCRIPT_DIR = _script_dir()
BASE_DIR = os.path.dirname(SCRIPT_DIR)

IP_DATABASE_DIR = os.path.join(BASE_DIR, "IP Database")
RESULT_DIR = os.path.join(BASE_DIR, "bspiski")
LANG_DIR = os.path.join(BASE_DIR, "Language")
LANG_SETTINGS = os.path.join(LANG_DIR, "settings.ini")

COUNTRIES_CSV_DIR = os.path.join(IP_DATABASE_DIR, "All countries")
COUNTRIES_CODES_FILE = os.path.join(IP_DATABASE_DIR, "codes_countries.txt")
DEFAULT_COUNTRY_CODE = "RU"
CSV_PATTERN_V4 = "*ipv4*.csv"
CSV_PATTERN_V6 = "*ipv6*.csv"

JSON_DIR = os.path.join(IP_DATABASE_DIR, "Manual list of GOOD ASN bots")

ALL_DIR = RESULT_DIR

DDOS_FLOOD_DIR = os.path.join(IP_DATABASE_DIR, "Spam IP addresses during a DDoS attack")
MANUAL_BAD_JSON_DIR = os.path.join(IP_DATABASE_DIR, "Manual list of BAD ASN bot networks")
DROP_IPV4_TXT = os.path.join(RESULT_DIR, "drop_ipv4.txt")
DROP_IPV6_TXT = os.path.join(RESULT_DIR, "drop_ipv6.txt")

_STRINGS = {}
_CURRENT_LANG = None


def _rel(path):
    try:
        return os.path.relpath(path, BASE_DIR)
    except ValueError:
        return path


def t(key, **kwargs):
    s = _STRINGS.get(key, key)
    if kwargs:
        try:
            return s.format(**kwargs)
        except KeyError:
            return s
    return s


def _load_lang_file(lang):
    path = os.path.join(LANG_DIR, f"{lang}.ini")
    cfg = configparser.ConfigParser()
    if not cfg.read(path, encoding="utf-8"):
        return {}
    if cfg.has_section("messages"):
        return dict(cfg["messages"])
    return {k: v for sec in cfg.sections() for k, v in cfg.items(sec)}


def _save_language(lang):
    os.makedirs(LANG_DIR, exist_ok=True)
    cfg = configparser.ConfigParser()
    cfg["general"] = {"language": lang}
    with open(LANG_SETTINGS, "w", encoding="utf-8") as f:
        cfg.write(f)


def _read_saved_language():
    if not os.path.isfile(LANG_SETTINGS):
        return None
    cfg = configparser.ConfigParser()
    cfg.read(LANG_SETTINGS, encoding="utf-8")
    lang = cfg.get("general", "language", fallback="").strip().lower()
    if lang in ("ru", "en"):
        return lang
    return None


def _ask_language_first_time():
    while True:
        print("\n--------------------------------------------------")
        print("Select language / Выберите язык")
        print("1 — Русский")
        print("2 — English")
        print("--------------------------------------------------")
        raw = input("Your choice (1 or 2) / Ваш выбор (1 или 2): ").strip().lower()
        if raw in ("2", "en", "english", "e", "eng"):
            return "en"
        if raw in ("1", "ru", "r", "rus", "ру"):
            return "ru"
        print("  → Enter 1 or 2 / Введите 1 или 2")


def setup_language():
    global _STRINGS, _CURRENT_LANG
    os.makedirs(LANG_DIR, exist_ok=True)

    lang = _read_saved_language()
    if lang is None:
        lang = _ask_language_first_time()
        _save_language(lang)
        _STRINGS = _load_lang_file(lang)
        label = "Русский" if lang == "ru" else "English"
        print(t("lang_saved", lang=label))

    _CURRENT_LANG = lang
    _STRINGS = _load_lang_file(lang)
    if not _STRINGS:
        print(f"⚠️ Missing {lang}.ini in Language/")
        _STRINGS = _load_lang_file("ru") or _load_lang_file("en")


def ensure_dirs():
    os.makedirs(ALL_DIR, exist_ok=True)


def write_networks(path, networks):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for net in sorted(networks, key=lambda x: (x.version, int(x.network_address))):
            f.write(str(net) + "\n")


def collapse(networks):
    return list(ipaddress.collapse_addresses(networks))


def _detect_csv_delimiter(sample_line):
    if not sample_line:
        return ","
    return ";" if sample_line.count(";") >= sample_line.count(",") else ","


def load_country_codes():
    path = COUNTRIES_CODES_FILE
    codes = {}
    if not os.path.isfile(path):
        print(t("countries_file_missing", path=path))
        return codes
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        for line in f:
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            if " - " not in s:
                continue
            code, name = s.split(" - ", 1)
            code = code.strip().upper()
            if len(code) == 2 and code.isalpha():
                codes[code] = name.strip()
    return codes


def ask_country_code(codes):
    default = DEFAULT_COUNTRY_CODE
    default_name = codes.get(default, "")
    default_label = f"{default} — {default_name}" if default_name else default

    print("\n--------------------------------------------------")
    print(t("country_title"))
    print(t("country_default", label=default_label))
    print(t("country_codes_ref", path=_rel(COUNTRIES_CODES_FILE)))
    print(t("country_hint"))
    print("--------------------------------------------------")

    raw = input(t("country_input")).strip()
    yes_tokens = {"Y", "YES", "Д", "ДА"} if _CURRENT_LANG == "ru" else {"Y", "YES"}
    if raw == "" or raw.upper() in yes_tokens:
        chosen = default
    else:
        chosen = raw.upper()
        if len(chosen) != 2 or not chosen.isalpha():
            print(t("country_invalid_code"))
            chosen = default

    name = codes.get(chosen)
    if name:
        print(t("country_selected", code=chosen, name=name))
    else:
        print(t("country_unknown_code", code=chosen, path=_rel(COUNTRIES_CODES_FILE)))
    return chosen


def load_manual_bad_networks_json():
    folder = MANUAL_BAD_JSON_DIR
    if not os.path.isdir(folder):
        print(t("folder_not_found", path=_rel(folder)))
        return [], [], set(), set()

    files = sorted(glob.glob(os.path.join(folder, "*.json")))
    print(t("json_files", path=_rel(folder), count=len(files)))

    all_v4 = []
    all_v6 = []

    for path in files:
        print(t("json_manual_drop", path=path))
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(t("json_error", path=path, error=e))
            continue

        for p in data.get("prefixes", []):
            if "ipv4Prefix" in p:
                s = p["ipv4Prefix"].strip()
                if s:
                    all_v4.append(s)
            if "ipv6Prefix" in p:
                s = p["ipv6Prefix"].strip()
                if s:
                    all_v6.append(s)

    return all_v4, all_v6, set(all_v4), set(all_v6)


def load_ddos_flood_spam():
    folder = DDOS_FLOOD_DIR
    if not os.path.isdir(folder):
        print(t("folder_not_found", path=_rel(folder)))
        return [], set()

    all_rows = []
    txt_files = sorted(glob.glob(os.path.join(folder, "*.txt")))
    csv_files = sorted(glob.glob(os.path.join(folder, "*.csv")))

    print(t("ddos_folder_stats", path=_rel(folder), txt=len(txt_files), csv=len(csv_files)))

    for path in txt_files:
        print(t("file_txt", path=path))
        with open(path, "r", encoding="utf-8-sig", newline="") as f:
            for line in f:
                s = line.rstrip("\r\n")
                if not s:
                    continue
                if s.lstrip().startswith("#"):
                    continue
                all_rows.append(s)

    for path in csv_files:
        print(t("file_csv", path=path))
        with open(path, "r", encoding="utf-8-sig", newline="") as f:
            first = f.readline()
            delim = _detect_csv_delimiter(first)
            f.seek(0)
            reader = csv.reader(f, delimiter=delim)
            row_iter = iter(reader)
            try:
                first_row = next(row_iter)
            except StopIteration:
                continue
            header_cell = first_row[0].strip() if first_row else ""
            if header_cell.upper() != "IP":
                if first_row and first_row[0] != "":
                    all_rows.append(first_row[0])
            for row in row_iter:
                if not row:
                    continue
                if row[0] != "":
                    all_rows.append(row[0])

    return all_rows, set(all_rows)


def write_drop_txt(path, unique_strings):
    ordered = sorted(unique_strings)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for s in ordered:
            f.write(s + "\n")
    print(t("saved", path=path, count=len(ordered)))


def load_csv(country_code):
    csv_path = COUNTRIES_CSV_DIR

    if not os.path.exists(csv_path):
        print(t("folder_not_found", path=_rel(csv_path)))
        return set(), set(), 0

    files = (
        glob.glob(os.path.join(csv_path, CSV_PATTERN_V4)) +
        glob.glob(os.path.join(csv_path, CSV_PATTERN_V6))
    )

    print(t("csv_files", path=_rel(csv_path), country=country_code, count=len(files)))

    v4 = set()
    v6 = set()
    dirty = 0

    for file in files:
        print(t("csv_file", path=file))

        with open(file, "r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f)

            for row in reader:
                if len(row) < 3:
                    continue

                raw_start, raw_end, raw_cc = row[0], row[1], row[2]

                if any(s != s.strip() for s in [raw_start, raw_end, raw_cc]):
                    dirty += 1

                start = raw_start.strip()
                end = raw_end.strip()
                cc = raw_cc.strip()

                if cc != country_code:
                    continue

                try:
                    start_ip = ipaddress.ip_address(start)
                    end_ip = ipaddress.ip_address(end)
                    nets = ipaddress.summarize_address_range(start_ip, end_ip)
                    for net in nets:
                        if net.version == 4:
                            v4.add(net)
                        else:
                            v6.add(net)
                except Exception:
                    continue

    return v4, v6, dirty


def load_json():
    json_path = JSON_DIR

    if not os.path.exists(json_path):
        print(t("json_folder_not_found", path=_rel(json_path)))
        return set(), set(), 0

    files = glob.glob(os.path.join(json_path, "*.json"))
    print(t("json_files", path=_rel(json_path), count=len(files)))

    v4 = set()
    v6 = set()
    dirty = 0

    for file in files:
        print(t("json_good_bot", path=file))

        try:
            with open(file, "r", encoding="utf-8") as f:
                content = f.read()
                if "\r" in content:
                    dirty += 1
                data = json.loads(content)

                for p in data.get("prefixes", []):
                    if "ipv4Prefix" in p:
                        try:
                            v4.add(ipaddress.ip_network(p["ipv4Prefix"].strip()))
                        except Exception:
                            continue
                    if "ipv6Prefix" in p:
                        try:
                            v6.add(ipaddress.ip_network(p["ipv6Prefix"].strip()))
                        except Exception:
                            continue
        except Exception as e:
            print(t("json_error", path=file, error=e))

    return v4, v6, dirty


def main():
    setup_language()
    ensure_dirs()

    print(t("start") + "\n")

    country_codes = load_country_codes()
    country_code = ask_country_code(country_codes)
    country_name = country_codes.get(country_code, "")

    csv_v4, csv_v6, dirty_csv = load_csv(country_code)
    json_v4, json_v6, dirty_json = load_json()

    print("\n" + t("before_processing"))
    print(t("stat_csv_ipv4", count=len(csv_v4)))
    print(t("stat_csv_ipv6", count=len(csv_v6)))
    print(t("stat_json_ipv4", count=len(json_v4)))
    print(t("stat_json_ipv6", count=len(json_v6)))

    all_v4 = collapse(list(csv_v4) + list(json_v4))
    all_v6 = collapse(list(csv_v6) + list(json_v6))

    print("\n" + t("after_collapse"))
    print(t("whitelist_ipv4", count=len(all_v4)))
    print(t("whitelist_ipv6", count=len(all_v6)))

    write_networks(os.path.join(ALL_DIR, "ipv4.txt"), all_v4)
    write_networks(os.path.join(ALL_DIR, "ipv6.txt"), all_v6)

    ddos_all, ddos_unique = load_ddos_flood_spam()
    total_dd = len(ddos_all)
    unique_dd = len(ddos_unique)
    removed_dd = total_dd - unique_dd

    print("\n--------------------------------------------------")
    print(_rel(DDOS_FLOOD_DIR))
    print(t("ddos_total_ip", count=total_dd))
    print(t("ddos_duplicates_removed", count=removed_dd))
    print(t("ddos_unique_total", count=unique_dd))
    print("--------------------------------------------------")

    all_m4, all_m6, man_v4, man_v6 = load_manual_bad_networks_json()
    tot_m4, tot_m6 = len(all_m4), len(all_m6)
    rem_m4 = tot_m4 - len(man_v4)
    rem_m6 = tot_m6 - len(man_v6)

    print("\n--------------------------------------------------")
    print(_rel(MANUAL_BAD_JSON_DIR))
    print(t("bad_ipv4_total", count=tot_m4))
    print(t("bad_ipv4_dupes", count=rem_m4))
    print(t("bad_ipv4_unique", count=len(man_v4)))
    print(t("bad_ipv6_total", count=tot_m6))
    print(t("bad_ipv6_dupes", count=rem_m6))
    print(t("bad_ipv6_unique", count=len(man_v6)))
    print("--------------------------------------------------")

    merged_v4 = set(ddos_unique) | set(man_v4)
    only_dd = len(merged_v4) - len(man_v4)
    only_man = len(merged_v4) - len(ddos_unique)
    in_both = len(ddos_unique) + len(man_v4) - len(merged_v4)

    print("\n--------------------------------------------------")
    print(t("merge_drop_ipv4_title"))
    print(t("merge_unique_lines", count=len(merged_v4)))
    print(t("merge_only_ddos", count=only_dd))
    print(t("merge_only_manual", count=only_man))
    print(t("merge_in_both", count=in_both))
    print("--------------------------------------------------")

    print("\n--------------------------------------------------")
    print(t("drop_ipv6_title"))
    print(t("drop_ipv6_unique", count=len(man_v6)))
    print("--------------------------------------------------")

    if os.path.isdir(DDOS_FLOOD_DIR) or os.path.isdir(MANUAL_BAD_JSON_DIR):
        write_drop_txt(DROP_IPV4_TXT, merged_v4)
        write_drop_txt(DROP_IPV6_TXT, man_v6)

    cc_label = f"{country_code} — {country_name}" if country_name else country_code
    print("\n--------------------------------------------------")
    print(t("summary_title"))
    print(t("summary_country", label=cc_label))
    print(t("summary_cc_ipv4", code=country_code, count=len(csv_v4)))
    print(t("summary_cc_ipv6", code=country_code, count=len(csv_v6)))
    print(t("summary_whitelist_ipv4", count=len(all_v4)))
    print(t("summary_whitelist_ipv6", count=len(all_v6)))
    print(t("summary_dirty_csv", count=dirty_csv))
    print(t("summary_dirty_json", count=dirty_json))
    print(t("summary_collapsed_ipv4", count=(len(csv_v4) + len(json_v4)) - len(all_v4)))
    print(t("summary_collapsed_ipv6", count=(len(csv_v6) + len(json_v6)) - len(all_v6)))
    print(t("summary_file_format"))
    print(t("summary_results", path=_rel(RESULT_DIR)))
    print("--------------------------------------------------")

    input(t("press_enter"))


if __name__ == "__main__":
    main()
