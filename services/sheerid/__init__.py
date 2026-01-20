"""
SheerID Verification Service

Unified service for all SheerID verification types.
Implements the standard "Waterfall" verification flow:
1. Data Generation (name, dob, email)
2. Submission (collectStudentPersonalInfo)
3. SSO Skip (DELETE /step/sso)
4. Document Upload (docUpload)
5. Completion (completeDocUpload)

Supports:
- YouTube Premium Student
- Spotify Premium Student
- Perplexity Pro Student
- Google One AI (Gemini)
- Bolt.new Teacher
- ChatGPT Plus K12 Teacher
- ChatGPT Plus Veterans
"""

import os
import re
import sys
import json
import time
import random
import hashlib
import base64
import uuid
from pathlib import Path
from io import BytesIO
from typing import Dict, Optional, Tuple, Any
from datetime import datetime

try:
    import httpx
except ImportError:
    httpx = None

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    Image = ImageDraw = ImageFont = None


# ============ CONFIGURATION ============

SHEERID_API_URL = "https://services.sheerid.com/rest/v2"
MIN_DELAY = 300
MAX_DELAY = 800

# Verification types with their configurations
VERIFY_TYPES = {
    'youtube': {
        'name': 'YouTube Premium Student',
        'cost': 5,
        'icon': '🎬',
        'strategy': 'student',
        'program_id': '67c8c14f5f17a83b745e3f82'
    },
    'spotify': {
        'name': 'Spotify Premium Student',
        'cost': 5,
        'icon': '🎵',
        'strategy': 'student',
        'program_id': '67c8c14f5f17a83b745e3f82'
    },
    'perplexity': {
        'name': 'Perplexity Pro Student',
        'cost': 8,
        'icon': '🤖',
        'strategy': 'student',
        'program_id': None  # Parsed from URL
    },
    'gemini': {
        'name': 'Google One AI Premium',
        'cost': 8,
        'icon': '✨',
        'strategy': 'student',
        'program_id': None
    },
    'boltnew': {
        'name': 'Bolt.new Teacher',
        'cost': 5,
        'icon': '⚡',
        'strategy': 'teacher',
        'program_id': None
    },
    'k12': {
        'name': 'ChatGPT Plus K12 Teacher',
        'cost': 10,
        'icon': '🏫',
        'strategy': 'k12',
        'program_id': None
    },
    'veterans': {
        'name': 'ChatGPT Plus Veterans',
        'cost': 10,
        'icon': '🎖️',
        'strategy': 'veterans',
        'program_id': None
    }
}


# ============ ANTI-DETECTION MODULE ============

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:134.0) Gecko/20100101 Firefox/134.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:134.0) Gecko/20100101 Firefox/134.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 Edg/132.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.2 Safari/605.1.15",
]

RESOLUTIONS = ["1920x1080", "1366x768", "1536x864", "1440x900", "1280x720", "2560x1440"]
LANGUAGES = ["en-US,en;q=0.9", "en-US,en;q=0.9,es;q=0.8", "en-GB,en;q=0.9"]
PLATFORMS = [
    ("Windows", '"Windows"', '"Chromium";v="132", "Google Chrome";v="132"'),
    ("macOS", '"macOS"', '"Chromium";v="132", "Google Chrome";v="132"'),
]


def get_random_user_agent() -> str:
    return random.choice(USER_AGENTS)


def generate_fingerprint() -> str:
    """Generate realistic browser fingerprint"""
    components = [
        str(int(time.time() * 1000)),
        str(random.random()),
        random.choice(RESOLUTIONS),
        str(random.choice([-8, -7, -6, -5, -4, 0, 1, 2, 3, 8, 9])),
        random.choice(LANGUAGES).split(",")[0],
        random.choice(["Win32", "MacIntel", "Linux x86_64"]),
        str(random.randint(2, 16)),
        str(random.randint(4, 32)),
        str(uuid.uuid4()),
    ]
    return hashlib.md5("|".join(components).encode()).hexdigest()


def generate_newrelic_headers() -> dict:
    """Generate NewRelic tracking headers required by SheerID API"""
    trace_id = uuid.uuid4().hex + uuid.uuid4().hex[:8]
    trace_id = trace_id[:32]
    span_id = uuid.uuid4().hex[:16]
    timestamp = int(time.time() * 1000)
    
    payload = {
        "v": [0, 1],
        "d": {
            "ty": "Browser",
            "ac": "364029",
            "ap": "134291347",
            "id": span_id,
            "tr": trace_id,
            "ti": timestamp
        }
    }
    
    return {
        "newrelic": base64.b64encode(json.dumps(payload).encode()).decode(),
        "traceparent": f"00-{trace_id}-{span_id}-01",
        "tracestate": f"364029@nr=0-1-364029-134291347-{span_id}----{timestamp}"
    }


def get_headers(for_sheerid: bool = True) -> dict:
    """Generate browser-like headers"""
    ua = get_random_user_agent()
    platform = random.choice(PLATFORMS)
    language = random.choice(LANGUAGES)
    
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": language,
        "cache-control": "no-cache",
        "pragma": "no-cache",
        "sec-ch-ua": platform[2],
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": platform[1],
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": ua,
    }
    
    if for_sheerid:
        nr_headers = generate_newrelic_headers()
        headers.update({
            "content-type": "application/json",
            "clientversion": "2.158.0",
            "clientname": "jslib",
            "origin": "https://services.sheerid.com",
            "referer": "https://services.sheerid.com/",
            **nr_headers
        })
    
    return headers


def random_delay():
    """Random delay to avoid detection"""
    time.sleep(random.randint(MIN_DELAY, MAX_DELAY) / 1000)


def create_session(proxy: str = None):
    """
    Create HTTP session with best available library
    Priority: curl_cffi > cloudscraper > httpx > requests
    """
    proxies = None
    if proxy:
        if "://" not in proxy:
            parts = proxy.split(":")
            if len(parts) == 2:
                proxy = f"http://{parts[0]}:{parts[1]}"
            elif len(parts) == 4:
                proxy = f"http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}"
        proxies = {"http": proxy, "https": proxy, "all://": proxy}
    
    # Try curl_cffi first (best TLS fingerprint spoofing)
    try:
        from curl_cffi import requests as curl_requests
        try:
            session = curl_requests.Session(proxies=proxies)
        except Exception:
            session = curl_requests.Session()
        return session, "curl_cffi"
    except ImportError:
        pass
    
    # Try cloudscraper (Cloudflare bypass)
    try:
        import cloudscraper
        session = cloudscraper.create_scraper(
            browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False}
        )
        if proxies:
            session.proxies = proxies
        return session, "cloudscraper"
    except ImportError:
        pass
    
    # Try httpx
    if httpx:
        proxy_url = proxies.get("all://") if proxies else None
        session = httpx.Client(timeout=30, proxy=proxy_url)
        return session, "httpx"
    
    # Fallback to requests
    import requests
    session = requests.Session()
    if proxies:
        session.proxies = proxies
    return session, "requests"


# ============ NAME GENERATION ============

FIRST_NAMES = [
    "James", "John", "Robert", "Michael", "William", "David", "Richard", "Joseph",
    "Thomas", "Christopher", "Charles", "Daniel", "Matthew", "Anthony", "Mark",
    "Mary", "Patricia", "Jennifer", "Linda", "Barbara", "Elizabeth", "Susan",
    "Jessica", "Sarah", "Karen", "Lisa", "Nancy", "Betty", "Margaret", "Sandra",
    "Emma", "Olivia", "Ava", "Isabella", "Sophia", "Mia", "Charlotte", "Amelia"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
    "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker"
]


def generate_name() -> Tuple[str, str]:
    return random.choice(FIRST_NAMES), random.choice(LAST_NAMES)


def generate_email(first: str, last: str, domain: str) -> str:
    patterns = [
        f"{first[0].lower()}{last.lower()}{random.randint(100, 999)}",
        f"{first.lower()}.{last.lower()}{random.randint(10, 99)}",
        f"{last.lower()}{first[0].lower()}{random.randint(100, 999)}"
    ]
    return f"{random.choice(patterns)}@{domain}"


def generate_birth_date(strategy: str = "student") -> str:
    """Generate birth date based on strategy"""
    if strategy == "teacher" or strategy == "k12":
        # Teachers are older (25-55 years)
        year = random.randint(1970, 2000)
    elif strategy == "veterans":
        # Veterans (18-50 years)
        year = random.randint(1975, 2005)
    else:
        # Students (18-24 years)
        year = random.randint(2000, 2006)
    
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    return f"{year}-{month:02d}-{day:02d}"


# ============ UNIVERSITY DATABASE ============

UNIVERSITIES = [
    # Vietnam
    {"id": 588731, "name": "Hanoi University of Science and Technology", "domain": "hust.edu.vn", "weight": 98},
    {"id": 588772, "name": "FPT University", "domain": "fpt.edu.vn", "weight": 97},
    {"id": 10066240, "name": "Vietnam National University Ho Chi Minh City", "domain": "vnuhcm.edu.vn", "weight": 95},
    {"id": 588740, "name": "Ton Duc Thang University", "domain": "tdtu.edu.vn", "weight": 91},
    
    # USA
    {"id": 2565, "name": "Pennsylvania State University-Main Campus", "domain": "psu.edu", "weight": 100},
    {"id": 3499, "name": "University of California, Los Angeles", "domain": "ucla.edu", "weight": 98},
    {"id": 3491, "name": "University of California, Berkeley", "domain": "berkeley.edu", "weight": 97},
    {"id": 2285, "name": "New York University", "domain": "nyu.edu", "weight": 96},
    {"id": 3568, "name": "University of Michigan", "domain": "umich.edu", "weight": 95},
    {"id": 378, "name": "Arizona State University", "domain": "asu.edu", "weight": 94},
    
    # Indonesia
    {"id": 10008577, "name": "University of Indonesia", "domain": "ui.ac.id", "weight": 90},
    {"id": 10008584, "name": "Institut Teknologi Bandung", "domain": "itb.ac.id", "weight": 88},
    {"id": 10008579, "name": "Gadjah Mada University", "domain": "ugm.ac.id", "weight": 87},
    
    # Japan
    {"id": 354085, "name": "The University of Tokyo", "domain": "u-tokyo.ac.jp", "weight": 85},
    {"id": 353961, "name": "Kyoto University", "domain": "kyoto-u.ac.jp", "weight": 84},
    
    # South Korea
    {"id": 356569, "name": "Seoul National University", "domain": "snu.ac.kr", "weight": 85},
    {"id": 356571, "name": "KAIST", "domain": "kaist.ac.kr", "weight": 86},
    
    # UK
    {"id": 273409, "name": "University of Oxford", "domain": "ox.ac.uk", "weight": 85},
    {"id": 273378, "name": "University of Cambridge", "domain": "cam.ac.uk", "weight": 85},
    
    # Singapore
    {"id": 356355, "name": "National University of Singapore", "domain": "nus.edu.sg", "weight": 82},
]

# Special university for Perplexity (Netherlands bypass)
GRONINGEN = {"id": 291085, "name": "University of Groningen", "domain": "rug.nl", "weight": 95}


def select_university(verify_type: str = None) -> Dict:
    """Weighted random selection based on success rates"""
    if verify_type == "perplexity":
        return {**GRONINGEN, "idExtended": str(GRONINGEN["id"])}
    
    weights = [uni["weight"] for uni in UNIVERSITIES]
    total = sum(weights)
    r = random.uniform(0, total)
    
    cumulative = 0
    for uni, weight in zip(UNIVERSITIES, weights):
        cumulative += weight
        if r <= cumulative:
            return {**uni, "idExtended": str(uni["id"])}
    return {**UNIVERSITIES[0], "idExtended": str(UNIVERSITIES[0]["id"])}


# ============ DOCUMENT GENERATION ============

def generate_student_id(first: str, last: str, school: str) -> bytes:
    """Generate fake student ID card"""
    if not Image:
        raise ImportError("Pillow not installed. Run: pip install Pillow")
    
    w, h = 650, 400
    img = Image.new("RGB", (w, h), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    try:
        font_lg = ImageFont.truetype("arial.ttf", 24)
        font_md = ImageFont.truetype("arial.ttf", 18)
        font_sm = ImageFont.truetype("arial.ttf", 14)
    except:
        font_lg = font_md = font_sm = ImageFont.load_default()
    
    # Header
    draw.rectangle([(0, 0), (w, 60)], fill=(0, 51, 102))
    draw.text((w//2, 30), "STUDENT IDENTIFICATION CARD", fill=(255, 255, 255), font=font_lg, anchor="mm")
    
    # School
    draw.text((w//2, 90), school[:50], fill=(0, 51, 102), font=font_md, anchor="mm")
    
    # Photo placeholder
    draw.rectangle([(30, 120), (150, 280)], outline=(180, 180, 180), width=2)
    draw.text((90, 200), "PHOTO", fill=(180, 180, 180), font=font_md, anchor="mm")
    
    # Info
    student_id = f"STU{random.randint(100000, 999999)}"
    y = 130
    for line in [f"Name: {first} {last}", f"ID: {student_id}", "Status: Full-time Student",
                 "Major: Computer Science", f"Valid: {time.strftime('%Y')}-{int(time.strftime('%Y'))+1}"]:
        draw.text((175, y), line, fill=(51, 51, 51), font=font_md)
        y += 28
    
    # Footer
    draw.rectangle([(0, h-40), (w, h)], fill=(0, 51, 102))
    draw.text((w//2, h-20), "Property of University", fill=(255, 255, 255), font=font_sm, anchor="mm")
    
    # Barcode
    for i in range(20):
        x = 480 + i * 7
        draw.rectangle([(x, 280), (x+3, 280+random.randint(30, 50))], fill=(0, 0, 0))
    
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def generate_teacher_certificate(first: str, last: str, school: str) -> bytes:
    """Generate teacher employment certificate"""
    if not Image:
        raise ImportError("Pillow not installed")
    
    w, h = 650, 500
    img = Image.new("RGB", (w, h), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    try:
        font_lg = ImageFont.truetype("arial.ttf", 24)
        font_md = ImageFont.truetype("arial.ttf", 18)
        font_sm = ImageFont.truetype("arial.ttf", 14)
    except:
        font_lg = font_md = font_sm = ImageFont.load_default()
    
    # Header
    draw.rectangle([(0, 0), (w, 70)], fill=(34, 87, 122))
    draw.text((w//2, 35), "CERTIFICATE OF EMPLOYMENT", fill=(255, 255, 255), font=font_lg, anchor="mm")
    
    # Content
    y = 100
    draw.text((w//2, y), school[:50], fill=(34, 87, 122), font=font_md, anchor="mm")
    
    y += 50
    draw.text((50, y), "This is to certify that:", fill=(51, 51, 51), font=font_md)
    
    y += 40
    draw.text((w//2, y), f"{first} {last}", fill=(0, 0, 0), font=font_lg, anchor="mm")
    
    y += 40
    lines = [
        "is currently employed as a full-time faculty member",
        f"at {school[:40]}.",
        "",
        f"Employee ID: TCH{random.randint(10000, 99999)}",
        f"Department: Computer Science",
        f"Start Date: {random.randint(2015, 2022)}-{random.randint(1, 12):02d}-01",
    ]
    for line in lines:
        draw.text((50, y), line, fill=(51, 51, 51), font=font_sm)
        y += 25
    
    # Signature
    y += 30
    draw.line([(400, y), (550, y)], fill=(0, 0, 0), width=1)
    draw.text((475, y + 10), "HR Director", fill=(51, 51, 51), font=font_sm, anchor="mm")
    
    # Date
    draw.text((50, h - 40), f"Date: {time.strftime('%B %d, %Y')}", fill=(51, 51, 51), font=font_sm)
    
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# ============ MAIN VERIFIER CLASS ============

class SheerIDVerifier:
    """
    Universal SheerID Verifier supporting all verification types.
    Implements the standard Waterfall verification flow.
    """
    
    def __init__(self, url: str, verify_type: str, proxy: str = None):
        self.url = url
        self.verify_type = verify_type
        self.config = VERIFY_TYPES.get(verify_type, VERIFY_TYPES['youtube'])
        self.vid = self._parse_verification_id(url)
        self.program_id = self._parse_program_id(url)
        self.fingerprint = generate_fingerprint()
        self.client, self.lib_name = create_session(proxy)
        self.org = None
        self.proxy = proxy
    
    def __del__(self):
        if hasattr(self, "client") and hasattr(self.client, "close"):
            try:
                self.client.close()
            except:
                pass
    
    @staticmethod
    def _parse_verification_id(url: str) -> Optional[str]:
        """Extract verification ID from URL"""
        # Format: verificationId=XXX
        match = re.search(r"verificationId=([a-f0-9]+)", url, re.IGNORECASE)
        if match:
            return match.group(1)
        # Format: /verification/XXX
        match = re.search(r"/verification/([a-f0-9]+)", url, re.IGNORECASE)
        if match:
            return match.group(1)
        return None
    
    @staticmethod
    def _parse_program_id(url: str) -> Optional[str]:
        """Extract program ID from URL"""
        match = re.search(r"/verify/([a-f0-9]+)/?", url, re.IGNORECASE)
        return match.group(1) if match else None
    
    def _request(self, method: str, endpoint: str, body: Dict = None) -> Tuple[Dict, int]:
        """Make HTTP request with anti-detection headers"""
        random_delay()
        try:
            headers = get_headers(for_sheerid=True)
            url = f"{SHEERID_API_URL}{endpoint}"
            
            if self.lib_name == "httpx":
                resp = self.client.request(method, url, json=body, headers=headers)
            else:
                if method.upper() == "GET":
                    resp = self.client.get(url, headers=headers)
                elif method.upper() == "POST":
                    resp = self.client.post(url, json=body, headers=headers)
                elif method.upper() == "PUT":
                    resp = self.client.put(url, json=body, headers=headers)
                elif method.upper() == "DELETE":
                    resp = self.client.delete(url, headers=headers)
                else:
                    resp = self.client.request(method, url, json=body, headers=headers)
            
            try:
                parsed = resp.json() if resp.text else {}
            except:
                parsed = {"_text": resp.text if hasattr(resp, 'text') else str(resp)}
            
            status = resp.status_code if hasattr(resp, 'status_code') else 200
            return parsed, status
        except Exception as e:
            return {"error": str(e)}, 500
    
    def _upload_document(self, upload_url: str, data: bytes) -> bool:
        """Upload document to S3"""
        try:
            headers = {"Content-Type": "image/png"}
            if self.lib_name == "httpx":
                resp = self.client.put(upload_url, content=data, headers=headers, timeout=60)
            else:
                resp = self.client.put(upload_url, data=data, headers=headers, timeout=60)
            
            status = resp.status_code if hasattr(resp, 'status_code') else 200
            return 200 <= status < 300
        except Exception as e:
            return False
    
    def check_link(self) -> Dict:
        """Check if verification link is valid"""
        if not self.vid:
            return {"valid": False, "error": "Invalid URL - cannot extract verification ID"}
        
        data, status = self._request("GET", f"/verification/{self.vid}")
        if status != 200:
            return {"valid": False, "error": f"HTTP {status}"}
        
        step = data.get("currentStep", "")
        valid_steps = ["collectStudentPersonalInfo", "collectTeacherPersonalInfo", "docUpload", "sso"]
        
        if step in valid_steps:
            return {"valid": True, "step": step, "data": data}
        elif step == "success":
            return {"valid": False, "error": "Already verified"}
        elif step == "pending":
            return {"valid": False, "error": "Already pending review"}
        
        return {"valid": False, "error": f"Invalid step: {step}"}
    
    def verify(self) -> Dict:
        """Run full verification flow"""
        if not self.vid:
            return {"success": False, "error": "Invalid verification URL"}
        
        strategy = self.config.get("strategy", "student")
        
        try:
            # Step 0: Check current step
            check_data, check_status = self._request("GET", f"/verification/{self.vid}")
            current_step = check_data.get("currentStep", "") if check_status == 200 else ""
            
            # Generate identity based on strategy
            first, last = generate_name()
            dob = generate_birth_date(strategy)
            self.org = select_university(self.verify_type)
            email = generate_email(first, last, self.org["domain"])
            
            result_data = {
                "student_name": f"{first} {last}",
                "student_email": email,
                "school_name": self.org["name"],
                "starting_step": current_step,
            }
            
            # Step 1: Generate document
            if strategy in ["teacher", "k12"]:
                doc = generate_teacher_certificate(first, last, self.org["name"])
            else:
                doc = generate_student_id(first, last, self.org["name"])
            
            # Step 2: Submit personal info (if needed)
            if current_step in ["collectStudentPersonalInfo", "collectTeacherPersonalInfo"]:
                endpoint = "collectTeacherPersonalInfo" if strategy in ["teacher", "k12"] else "collectStudentPersonalInfo"
                
                body = {
                    "firstName": first,
                    "lastName": last,
                    "birthDate": dob,
                    "email": email,
                    "phoneNumber": "",
                    "organization": {
                        "id": self.org["id"],
                        "idExtended": self.org["idExtended"],
                        "name": self.org["name"]
                    },
                    "deviceFingerprintHash": self.fingerprint,
                    "locale": "en-US",
                    "metadata": {
                        "marketConsentValue": False,
                        "verificationId": self.vid,
                    }
                }
                
                data, status = self._request("POST", f"/verification/{self.vid}/step/{endpoint}", body)
                
                if status != 200:
                    return {"success": False, "error": f"Submit failed: {status}", **result_data}
                
                if data.get("currentStep") == "error":
                    return {"success": False, "error": f"Error: {data.get('errorIds', [])}", **result_data}
                
                current_step = data.get("currentStep", "")
                
                # Check for instant success (K12/Veterans auto-approval)
                if current_step == "success":
                    return {
                        "success": True,
                        "message": "Instant verification via authoritative data!",
                        "redirect_url": data.get("redirectUrl"),
                        **result_data
                    }
            
            # Step 3: Skip SSO if needed
            if current_step in ["sso", "collectStudentPersonalInfo"]:
                self._request("DELETE", f"/verification/{self.vid}/step/sso")
            
            # Step 4: Upload document
            upload_body = {
                "files": [{
                    "fileName": "student_card.png" if strategy == "student" else "certificate.png",
                    "mimeType": "image/png",
                    "fileSize": len(doc)
                }]
            }
            data, status = self._request("POST", f"/verification/{self.vid}/step/docUpload", upload_body)
            
            if not data.get("documents"):
                return {"success": False, "error": "No upload URL received", **result_data}
            
            upload_url = data["documents"][0].get("uploadUrl")
            if not self._upload_document(upload_url, doc):
                return {"success": False, "error": "Document upload failed", **result_data}
            
            # Step 5: Complete upload
            data, status = self._request("POST", f"/verification/{self.vid}/step/completeDocUpload")
            
            final_step = data.get("currentStep", "pending")
            
            return {
                "success": True,
                "message": "Verification submitted! Wait 24-48h for review." if final_step == "pending" else f"Status: {final_step}",
                "redirect_url": data.get("redirectUrl"),
                "final_step": final_step,
                **result_data
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}


# ============ PUBLIC API ============

def get_verify_types() -> Dict:
    """Get all available verification types"""
    return VERIFY_TYPES


def check_sheerid_link(url: str, verify_type: str = "youtube") -> Dict:
    """Check if a SheerID link is valid"""
    verifier = SheerIDVerifier(url, verify_type)
    return verifier.check_link()


def run_verification(url: str, verify_type: str = "youtube", proxy: str = None) -> Dict:
    """Run SheerID verification"""
    verifier = SheerIDVerifier(url, verify_type, proxy)
    
    # First check if link is valid
    check = verifier.check_link()
    if not check.get("valid"):
        return {"success": False, "error": check.get("error", "Invalid link")}
    
    # Run verification
    return verifier.verify()


# ============ REAL-TIME STATUS CHECK ============

# Claim URLs for each verification type
CLAIM_URLS = {
    'youtube': 'https://www.youtube.com/premium/student',
    'spotify': 'https://www.spotify.com/us/student/',
    'perplexity': 'https://perplexity.ai/pro',
    'gemini': 'https://one.google.com/ai-student?g1_landing_page=75&utm_source=sheerid&utm_campaign=student',
    'boltnew': 'https://bolt.new/pricing',
    'k12': 'https://chat.openai.com/upgrade',
    'veterans': 'https://chat.openai.com/upgrade',
}


def get_verification_status(verification_id: str, proxy: str = None) -> Dict:
    """
    Check real-time verification status from SheerID API.
    
    Status mapping:
    - 'success' = APPROVED (verified!)
    - 'pending' = Under review (not approved yet)
    - 'docUpload' = Needs document upload
    - 'fraudReview' = Fraud review (failed)
    - 'error' = Error occurred (failed)
    - 'collectStudentPersonalInfo' = Need to submit info
    
    Only 'success' status = ACTUALLY APPROVED
    """
    if not verification_id:
        return {"success": False, "error": "No verification ID"}
    
    session, lib_name = create_session(proxy)
    
    try:
        headers = get_headers(for_sheerid=True)
        url = f"{SHEERID_API_URL}/verification/{verification_id}"
        
        if lib_name == "httpx":
            resp = session.get(url, headers=headers)
        else:
            resp = session.get(url, headers=headers)
        
        status_code = resp.status_code if hasattr(resp, 'status_code') else 200
        
        if status_code != 200:
            return {"success": False, "error": f"HTTP {status_code}"}
        
        try:
            data = resp.json()
        except:
            return {"success": False, "error": "Invalid response"}
        
        current_step = data.get("currentStep", "unknown")
        redirect_url = data.get("redirectUrl")
        
        # Parse status
        if current_step == "success":
            return {
                "success": True,
                "approved": True,
                "status": "success",
                "status_display": "✅ VERIFIED",
                "message": "VERIFICATION APPROVED!",
                "redirect_url": redirect_url,
                "credits": data.get("credits", 0)
            }
        elif current_step == "pending":
            return {
                "success": True,
                "approved": False,
                "status": "pending",
                "status_display": "⏳ PENDING",
                "message": "Under review (24-48 hours). Submit new link if not approved.",
                "redirect_url": None,
                "credits": data.get("credits", 0)
            }
        elif current_step == "fraudReview":
            return {
                "success": True,
                "approved": False,
                "status": "fraud_review",
                "status_display": "🚫 FRAUD REVIEW",
                "message": "Flagged for fraud review. Verification FAILED. Submit new link.",
                "redirect_url": None,
                "credits": data.get("credits", 0)
            }
        elif current_step == "docUpload":
            return {
                "success": True,
                "approved": False,
                "status": "doc_upload",
                "status_display": "📄 DOC REQUIRED",
                "message": "Document upload required. Verification incomplete.",
                "redirect_url": None,
                "credits": data.get("credits", 0)
            }
        elif current_step == "error":
            error_ids = data.get("errorIds", [])
            return {
                "success": True,
                "approved": False,
                "status": "error",
                "status_display": "❌ ERROR",
                "message": f"Verification error: {', '.join(error_ids)}. Submit new link.",
                "redirect_url": None,
                "credits": data.get("credits", 0)
            }
        else:
            return {
                "success": True,
                "approved": False,
                "status": current_step,
                "status_display": f"ℹ️ {current_step.upper()}",
                "message": f"Status: {current_step}",
                "redirect_url": redirect_url,
                "credits": data.get("credits", 0)
            }
    
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        try:
            session.close()
        except:
            pass


def get_claim_url(verify_type: str) -> str:
    """Get claim URL for verification type"""
    return CLAIM_URLS.get(verify_type, "")

