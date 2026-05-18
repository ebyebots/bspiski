#!/bin/bash

set -e

# ========================================
# НАСТРОЙКИ
# ========================================
DIR="/etc/iptables/bspiski"
IPV4_FILE="$DIR/ipv4.txt"
IPV6_FILE="$DIR/ipv6.txt"
DROP_IPV4_FILE="$DIR/drop_ipv4.txt"
DROP_IPV6_FILE="$DIR/drop_ipv6.txt"

HTTP_PORTS="80,443"
HTTP_LIMIT="30/second"
HTTP_BURST=60

# Настройки времени бана
WL_BAN_TIME=1800       # 30 minutes (for those on the white list, but have exceeded the connection limit)
GUEST_BAN_TIME=3600   # 1 hour (for everyone else who breaks into the site - no whitelists)
CONNLIMIT_VAL=12      # Maximum allowed number of parallel connections

WHITELIST_MAX=200000
BLACKLIST_MAX=300000
DROP_MAX=300000

echo "[*] Starting Firewall (WL Ban: 30m | Guest Ban: 1h)"

# ========================================
# 1. RESET
# ========================================
iptables -P INPUT ACCEPT
iptables -F
iptables -X
ip6tables -P INPUT ACCEPT
ip6tables -F 2>/dev/null || true
ip6tables -X 2>/dev/null || true

# Очистка ipset
ipset destroy whitelist4 2>/dev/null || true
ipset destroy whitelist6 2>/dev/null || true
ipset destroy blacklist4 2>/dev/null || true
ipset destroy blacklist6 2>/dev/null || true
ipset destroy droplist4 2>/dev/null || true
ipset destroy droplist6 2>/dev/null || true
ipset destroy conn_limit_ban4 2>/dev/null || true
ipset destroy conn_limit_ban6 2>/dev/null || true

# ========================================
# 2. IPSET CREATION
# ========================================
ipset create whitelist4 hash:net family inet hashsize 65536 maxelem $WHITELIST_MAX
ipset create whitelist6 hash:net family inet6 hashsize 65536 maxelem $WHITELIST_MAX

# Список для гостей (бан на 1 час)
ipset create blacklist4 hash:net family inet timeout $GUEST_BAN_TIME maxelem $BLACKLIST_MAX
ipset create blacklist6 hash:net family inet6 timeout $GUEST_BAN_TIME maxelem $BLACKLIST_MAX

# Список для нарушителей из WL (бан на 30 минут)
ipset create conn_limit_ban4 hash:net family inet timeout $WL_BAN_TIME maxelem $BLACKLIST_MAX
ipset create conn_limit_ban6 hash:net family inet6 timeout $WL_BAN_TIME maxelem $BLACKLIST_MAX

ipset create droplist4 hash:net family inet hashsize 65536 maxelem $DROP_MAX
ipset create droplist6 hash:net family inet6 hashsize 65536 maxelem $DROP_MAX

# ========================================
# 3. LOAD LISTS (FAST RESTORE)
# ========================================
[ -f "$DROP_IPV4_FILE" ] && { sed 's/\r//g' "$DROP_IPV4_FILE" | grep -vE '^#|^$' | sed 's/^/add droplist4 /' | ipset restore; }
[ -f "$DROP_IPV6_FILE" ] && { sed 's/\r//g' "$DROP_IPV6_FILE" | grep -vE '^#|^$' | sed 's/^/add droplist6 /' | ipset restore; }
[ -f "$IPV4_FILE" ] && { sed 's/\r//g' "$IPV4_FILE" | grep -vE '^#|^$' | sed 's/^/add whitelist4 /' | ipset restore; }
[ -f "$IPV6_FILE" ] && { sed 's/\r//g' "$IPV6_FILE" | grep -vE '^#|^$' | sed 's/^/add whitelist6 /' | ipset restore; }

# ========================================
# 4. BASIC RULES
# ========================================
iptables -A INPUT -i lo -j ACCEPT
ip6tables -A INPUT -i lo -j ACCEPT

iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
ip6tables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

iptables -A INPUT -p tcp --dport 22 -j ACCEPT
ip6tables -A INPUT -p tcp --dport 22 -j ACCEPT

# ========================================
# 5. BLOCKING LISTS (PRIORITY)
# ========================================
iptables -A INPUT -m set --match-set droplist4 src -j DROP
iptables -A INPUT -m set --match-set blacklist4 src -j DROP
iptables -A INPUT -m set --match-set conn_limit_ban4 src -j DROP

ip6tables -A INPUT -m set --match-set droplist6 src -j DROP
ip6tables -A INPUT -m set --match-set blacklist6 src -j DROP
ip6tables -A INPUT -m set --match-set conn_limit_ban6 src -j DROP

# ========================================
# 6. CONNLIMIT ДЛЯ БЕЛОГО СПИСКА (BAN 15 MIN)
# ========================================
iptables -A INPUT -p tcp -m multiport --dports $HTTP_PORTS \
  -m set --match-set whitelist4 src \
  -m connlimit --connlimit-above $CONNLIMIT_VAL --connlimit-mask 32 \
  -j SET --add-set conn_limit_ban4 src --timeout $WL_BAN_TIME

ip6tables -A INPUT -p tcp -m multiport --dports $HTTP_PORTS \
  -m set --match-set whitelist6 src \
  -m connlimit --connlimit-above $CONNLIMIT_VAL --connlimit-mask 128 \
  -j SET --add-set conn_limit_ban6 src --timeout $WL_BAN_TIME

# ========================================
# 7. WHITELIST PASS (RATE LIMIT)
# ========================================
iptables -A INPUT -p tcp -m multiport --dports $HTTP_PORTS \
  -m set --match-set whitelist4 src \
  -m conntrack --ctstate NEW \
  -m hashlimit --hashlimit $HTTP_LIMIT --hashlimit-burst $HTTP_BURST \
  --hashlimit-mode srcip --hashlimit-name http_limit \
  -j ACCEPT

ip6tables -A INPUT -p tcp -m multiport --dports $HTTP_PORTS \
  -m set --match-set whitelist6 src \
  -m conntrack --ctstate NEW \
  -m hashlimit --hashlimit $HTTP_LIMIT --hashlimit-burst $HTTP_BURST \
  --hashlimit-mode srcip --hashlimit-name http6_limit \
  -j ACCEPT

# ========================================
# 8. НЕИЗВЕСТНЫЕ IP -> ЧЕРНЫЙ СПИСОК (BAN 1 HOUR)
# ========================================
iptables -A INPUT -p tcp -m multiport --dports $HTTP_PORTS \
  -m set ! --match-set whitelist4 src \
  -j SET --add-set blacklist4 src --timeout $GUEST_BAN_TIME

ip6tables -A INPUT -p tcp -m multiport --dports $HTTP_PORTS \
  -m set ! --match-set whitelist6 src \
  -j SET --add-set blacklist6 src --timeout $GUEST_BAN_TIME

# ========================================
# 9. FINAL POLICY
# ========================================
iptables -P INPUT DROP
ip6tables -P INPUT DROP

# Считаем количество записей в каждом наборе ipset
COUNT4=$(ipset list whitelist4 | grep "Number of entries" | awk '{print $4}')
COUNT6=$(ipset list whitelist6 | grep "Number of entries" | awk '{print $4}')
DCOUNT4=$(ipset list droplist4 | grep "Number of entries" | awk '{print $4}')
DCOUNT6=$(ipset list droplist6 | grep "Number of entries" | awk '{print $4}')
BAN4=$(ipset list blacklist4 | grep "Number of entries" | awk '{print $4}')
CONNBAN=$(ipset list conn_limit_ban4 | grep "Number of entries" | awk '{print $4}')

# Финальный отчет
echo "--------------------------------------------------"
echo "[+] Firewall ACTIVE"
echo "[+] Guest Ban (Blacklist): 1 Hour"
echo "[+] Whitelist Conn-Limit Ban: 30 Minutes (Limit: $CONNLIMIT_VAL)"
echo "[+] IPv4 drop list: $DCOUNT4 entries"
echo "[+] IPv6 drop list: $DCOUNT6 entries"
echo "[+] IPv4 whitelist: $COUNT4 entries"
echo "[+] IPv6 whitelist: $COUNT6 entries"
echo "--------------------------------------------------"