import psycopg2
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
import os
import logging
from datetime import datetime

# Import search functions for each news/security source
from search.search_cnn import search_cnn
from search.search_bbc import search_bbc
from search.search_krebs import search_krebs
from search.search_thn import search_thn
from search.search_cyberscoop import search_cyberscoop
from search.search_securityweek import search_securityweek
from search.search_microsoft import search_microsoft
from search.search_threatpost import search_threatpost
from search.search_cisa import search_cisa
from search.search_crowdstrike import search_crowdstrike
from search.search_cloudblog import search_cloudblog
from search.search_exploit_db import search_exploit_db
from search.search_sans import search_sans
from search.search_cisco import search_cisco
from search.search_aws import search_aws
from search.search_zdi_upcoming import search_zdi_upcoming
from search.search_zdi_published import search_zdi_published
from search.search_zdi import search_zdi
from search.search_dark_reading import search_dark_reading
from search.search_bleeping_computer import search_bleeping_computer
from search.search_the_record import search_the_record
from search.search_security_affairs import search_security_affairs
from search.search_ncsc import search_ncsc
from search.search_europol import search_europol
from search.search_fbi import search_fbi
from search.search_rapid7 import search_rapid7
from search.search_wired import search_wired
from search.search_kali import search_kali
from search.search_malwarebytes import search_malwarebytes
from search.search_palo_alto import search_palo_alto
from search.search_risky import search_risky
from search.search_eu_cert import search_eu_cert
from search.search_google_zero import search_google_zero
from search.search_japan_cert import search_japan_cert
from search.search_daily_swig import search_daily_swig
from search.search_darknet_diaries import search_darknet_diaries
from search.search_fortinet import search_fortinet
from search.search_vmware import search_vmware
from search.search_research_checkpoint import search_research_checkpoint
from search.search_security_boulevard import search_security_boulevard
from search.search_schneier import search_schneier
from search.search_ibm import search_ibm
from search.search_ncc import search_ncc
from search.search_trustedsec import search_trustedsec
from search.search_eset import search_eset
from search.search_kaspersky import search_kaspersky
from search.search_arstechnica import search_arstechnica
from search.search_realmode import search_realmode
from search.search_portswigger import search_portswigger
from search.search_mozilla import search_mozilla

load_dotenv()

# Configure logging — prints to terminal and writes to scraper.log
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(),                  # terminal
        logging.FileHandler("scraper.log")        # log file
    ]
)
log = logging.getLogger(__name__)

source_groups = {
    "Mainstream News": [
        "BBC", "CNN", "Wired", "Ars Technica"
    ],
    "Cybersecurity Blogs": [
        "The Hacker News", "Threatpost", "Security Week", "CyberScoop",
        "Krebs On Security", "Zero Day Initiative Blog", "DarkReading",
        "Bleeping Computer", "Security Affairs", "The Record",
        "Google Project Zero", "Google Cloud Security Blog",
        "Security Boulevard", "The Daily Swig", "Schneier",
        "Realmode Labs", "NCC Group Research Blog", "TrustedSec Blog",
        "PortSwigger Research"
    ],
    "Vendors & Feeds": [
        "CrowdStrike", "Microsoft Security", "AWS Security", "ExploitDB",
        "Cisco Talos Intelligence", "SANS Internet Storm Center",
        "Zero Day Initiative: Upcoming", "Zero Day Initiative: Published",
        "Rapid7", "Malwarebytes", "Kali Linux", "Palo Alto Networks",
        "Check Point Research Blog", "Fortinet Blog", "VMware Security Blog",
        "IBM X‑Force", "Kaspersky Securelist", "ESET WeLiveSecurity",
        "Mozilla Security Blog"
    ],
    "Government & Law Enforcement": [
        "FBI Newsroom", "Europol Newsroom", "NCSC (UK)",
        "CERT-US (CISA)", "CERT-EU", "CERT-Japan"
    ],
    "Community & Aggregators": [
        "Substack – Risky Biz", "Darknet Diaries"
    ]
}

source_function_map = {
    "BBC": search_bbc,
    "CNN": search_cnn,
    "Krebs On Security": search_krebs,
    "The Hacker News": search_thn,
    "CyberScoop": search_cyberscoop,
    "Security Week": search_securityweek,
    "Microsoft Security": search_microsoft,
    "Threatpost": search_threatpost,
    "CERT-US (CISA)": search_cisa,
    "CrowdStrike": search_crowdstrike,
    "Google Cloud": search_cloudblog,
    "ExploitDB": search_exploit_db,
    "SANS Internet Storm Center": search_sans,
    "Cisco Talos Intelligence": search_cisco,
    "AWS Security": search_aws,
    "Zero Day Initiative: Upcoming": search_zdi_upcoming,
    "Zero Day Initiative: Published": search_zdi_published,
    "Zero Day Initiative Blog": search_zdi,
    "The Record": search_the_record,
    "Bleeping Computer": search_bleeping_computer,
    "DarkReading": search_dark_reading,
    "Security Affairs": search_security_affairs,
    "FBI Newsroom": search_fbi,
    "Europol Newsroom": search_europol,
    "NCSC (UK)": search_ncsc,
    "Wired": search_wired,
    "Rapid7": search_rapid7,
    "Palo Alto Networks": search_palo_alto,
    "Kali Linux": search_kali,
    "Malwarebytes": search_malwarebytes,
    "Substack – Risky Biz": search_risky,
    "CERT-EU": search_eu_cert,
    "CERT-Japan": search_japan_cert,
    "Google Project Zero": search_google_zero,
    "The Daily Swig": search_daily_swig,
    "Darknet Diaries": search_darknet_diaries,
    "Fortinet Blog": search_fortinet,
    "Security Boulevard": search_security_boulevard,
    "VMware Security Blog": search_vmware,
    "Check Point Research Blog": search_research_checkpoint,
    "Schneier": search_schneier,
    "IBM X‑Force": search_ibm,
    "NCC Group Research Blog": search_ncc,
    "TrustedSec Blog": search_trustedsec,
    "ESET WeLiveSecurity": search_eset,
    "Kaspersky Securelist": search_kaspersky,
    "Ars Technica": search_arstechnica,
    "Realmode Labs": search_realmode,
    "PortSwigger Research": search_portswigger,
    "Mozilla Labs": search_mozilla
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(BASE_DIR, "blacklist.txt"), "r", encoding="utf-8") as f:
    url_blacklist = f.read().split("\n")

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS")
    )

def run_search(keyword, source, results, seen_links):
    for source_key, search_func in source_function_map.items():
        if source_key in source:
            return search_func(keyword, source, results, seen_links, url_blacklist)
    return results

def scrape_all():
    keywords = ["*"]
    total_sources = len(source_function_map)

    log.info("=" * 50)
    log.info(f"Scrape started — {total_sources} sources to process")
    log.info("=" * 50)

    conn = get_db_connection()
    cursor = conn.cursor()
    inserted = 0
    skipped = 0
    errors = 0

    for i, source in enumerate(source_function_map.keys(), start=1):
        log.info(f"[{i}/{total_sources}] Scraping: {source}")
        results = {}
        seen_links = set()

        try:
            with ThreadPoolExecutor(max_workers=8) as executor:
                futures = [executor.submit(run_search, kw, source, results, seen_links)
                           for kw in keywords]
                for f in futures:
                    f.result()

            source_inserted = 0
            source_skipped = 0

            for source_name, articles in results.items():
                for article in articles:
                    title, url, snippet, date, epoch = article
                    try:
                        cursor.execute("""
                            INSERT INTO articles (source, title, url, snippet, date, epoch)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            ON CONFLICT (url) DO NOTHING
                        """, (source_name, title, url, snippet, date, epoch))
                        if cursor.rowcount > 0:
                            inserted += 1
                            source_inserted += 1
                        else:
                            skipped += 1
                            source_skipped += 1
                    except Exception as e:
                        log.error(f"  DB insert error for '{title}': {e}")
                        errors += 1

            conn.commit()
            log.info(f"  ✓ {source_inserted} new, {source_skipped} duplicates")

        except Exception as e:
            log.error(f"  ✗ Failed to scrape {source}: {e}")
            errors += 1

    cursor.close()
    conn.close()

    log.info("=" * 50)
    log.info(f"Scrape complete — {inserted} new articles, {skipped} duplicates skipped, {errors} errors")
    log.info("=" * 50)

if __name__ == "__main__":
    scrape_all()