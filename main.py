
import os
import sys
import logging
import requests
import json
from datetime import datetime, timezone
from typing import List, Dict, Optional
from urllib.parse import urljoin
import uuid
import time

import pymongo
from pymongo import MongoClient
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

class ETLConfig:
    """Configuration class for ETL process"""
    
    def __init__(self):
        self.WEB_URL = os.getenv('WEB_URL', 'http://52.0.216.22:7080')
        self.MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://etl_user:etl_pass123@52.0.216.22:27017/etl_tracker')
        self.API_BASE_URL = os.getenv('API_BASE_URL', 'http://52.0.216.22:7300')
        self.LOG_LEVEL = os.getenv('LOG_LEVEL', 'info')
        self.RETRY_ATTEMPTS = int(os.getenv('RETRY_ATTEMPTS', '3'))
        self.PROCESO_DESCRIPCION = os.getenv('PROCESO_DESCRIPCION', 'Extracción contactos empresariales - Empresas Tech')
        
        # Filter criteria
        self.TECH_KEYWORDS = ['Tech', 'Data', 'Cloud', 'Digital', 'Software', 'System']
        self.EXECUTIVE_ROLES = ['CEO', 'CTO', 'Director', 'VP', 'Chief', 'Vice President', 'President']

class ContactExtractor:
    """Web scraper for extracting contact data"""
    
    def __init__(self, config: ETLConfig):
        self.config = config
        self.session = self._create_session()
    
    def _create_session(self):
        """Create requests session with retry strategy"""
        session = requests.Session()
        retry_strategy = Retry(
            total=self.config.RETRY_ATTEMPTS,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session
    
    def extract_contacts(self) -> List[Dict]:
        """Extract contacts from web page"""
        try:
            logger.info(f"Fetching data from {self.config.WEB_URL}")
            response = self.session.get(self.config.WEB_URL, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            contacts = []
            
            # Find table with contact data
            table = soup.find('table')
            if not table:
                logger.error("No table found on the page")
                return []
            
            rows = table.find_all('tr')[1:]  # Skip header row
            logger.info(f"Found {len(rows)} rows in table")
            
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 6:
                    contact = {
                        'empresa': cells[0].get_text(strip=True),
                        'nombre': cells[1].get_text(strip=True),
                        'apellido': cells[2].get_text(strip=True),
                        'puesto': cells[3].get_text(strip=True),
                        'email': cells[4].get_text(strip=True),
                        'primer_contacto': cells[5].get_text(strip=True)
                    }
                    
                    # Basic data validation
                    if all([contact['empresa'], contact['nombre'], contact['email']]):
                        contacts.append(contact)
            
            logger.info(f"Extracted {len(contacts)} valid contacts")
            return contacts
            
        except Exception as e:
            logger.error(f"Error extracting contacts: {str(e)}")
            raise

class ContactFilter:
    """Filter contacts based on business criteria"""
    
    def __init__(self, config: ETLConfig):
        self.config = config
    
    def is_tech_company(self, company_name: str) -> bool:
        """Check if company is tech-related"""
        return any(keyword.lower() in company_name.lower() 
                  for keyword in self.config.TECH_KEYWORDS)
    
    def is_executive_role(self, position: str) -> bool:
        """Check if position is executive level"""
        return any(role.lower() in position.lower() 
                  for role in self.config.EXECUTIVE_ROLES)
    
    def filter_contacts(self, contacts: List[Dict]) -> List[Dict]:
        """Filter contacts based on criteria"""
        filtered = []
        company_contact_count = {}
        
        # Count contacts per company
        for contact in contacts:
            company = contact['empresa']
            if company not in company_contact_count:
                company_contact_count[company] = 0
            company_contact_count[company] += 1
        
        # Filter contacts
        for contact in contacts:
            company = contact['empresa']
            position = contact['puesto']
            
            # Apply filters
            if (self.is_tech_company(company) and 
                self.is_executive_role(position) and 
                company_contact_count[company] >= 2):
                filtered.append(contact)
        
        logger.info(f"Filtered {len(filtered)} contacts from {len(contacts)} total")
        return filtered

class MongoDBHandler:
    """Handle MongoDB operations"""
    
    def __init__(self, config: ETLConfig):
        self.config = config
        self.client = None
        self.db = None
        self.collection = None
    
    def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = MongoClient(self.config.MONGODB_URI)
            self.db = self.client.get_default_database()
            self.collection = self.db['contactos_empresariales']
            
            # Test connection
            self.client.admin.command('ismaster')
            logger.info("Successfully connected to MongoDB")
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise
    
    def insert_contacts(self, contacts: List[Dict], proceso_id: str) -> int:
        """Insert contacts into MongoDB"""
        if not contacts:
            return 0
        
        documents = []
        current_time = datetime.now(timezone.utc)
        
        for contact in contacts:
            # Parse date
            try:
                fecha_primer_contacto = datetime.fromisoformat(contact['primer_contacto']).replace(tzinfo=timezone.utc)
            except:
                # Fallback for different date formats
                fecha_primer_contacto = current_time
            
            doc = {
                'empresa': contact['empresa'],
                'contacto': {
                    'nombre': contact['nombre'],
                    'apellido': contact['apellido'],
                    'puesto': contact['puesto'],
                    'email': contact['email']
                },
                'fechaPrimerContacto': fecha_primer_contacto,
                'fechaInsercion': current_time,
                'procesoId': proceso_id
            }
            documents.append(doc)
        
        try:
            # Check for duplicates and insert
            inserted_count = 0
            for doc in documents:
                # Check if contact already exists
                existing = self.collection.find_one({
                    'contacto.email': doc['contacto']['email'],
                    'empresa': doc['empresa']
                })
                
                if not existing:
                    self.collection.insert_one(doc)
                    inserted_count += 1
                else:
                    logger.info(f"Skipping duplicate contact: {doc['contacto']['email']}")
            
            logger.info(f"Inserted {inserted_count} new contacts into MongoDB")
            return inserted_count
            
        except Exception as e:
            logger.error(f"Error inserting contacts: {str(e)}")
            raise
    
    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()

class ETLTracker:
    """Track ETL processes via API"""
    
    def __init__(self, config: ETLConfig):
        self.config = config
        self.session = self._create_session()
    
    def _create_session(self):
        """Create requests session with retry strategy"""
        session = requests.Session()
        retry_strategy = Retry(
            total=self.config.RETRY_ATTEMPTS,
            status_forcelist=[429, 500, 502, 503, 504],
            method_whitelist=["HEAD", "GET", "POST", "OPTIONS"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session
    
    def register_etl_process(self, cantidad_datos: int, descripcion: str = None) -> bool:
        """Register ETL process execution"""
        if descripcion is None:
            descripcion = self.config.PROCESO_DESCRIPCION
        
        payload = {
            'cantidadDatos': cantidad_datos,
            'fechaEjecucion': datetime.now(timezone.utc).isoformat(),
            'descripcion': descripcion
        }
        
        try:
            url = urljoin(self.config.API_BASE_URL, '/api/etl')
            logger.info(f"Registering ETL process at {url}")
            
            response = self.session.post(
                url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 201:
                logger.info("ETL process registered successfully")
                logger.info(f"API Response: {response.json()}")
                return True
            else:
                logger.error(f"Failed to register ETL process: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error registering ETL process: {str(e)}")
            return False

class ETLProcessor:
    """Main ETL processor orchestrating the entire process"""
    
    def __init__(self):
        self.config = ETLConfig()
        self.extractor = ContactExtractor(self.config)
        self.filter = ContactFilter(self.config)
        self.db_handler = MongoDBHandler(self.config)
        self.tracker = ETLTracker(self.config)
        self.proceso_id = str(uuid.uuid4())
    
    def run(self) -> bool:
        """Run the complete ETL process"""
        start_time = datetime.now()
        logger.info(f"Starting ETL process with ID: {self.proceso_id}")
        
        try:
            # Step 1: Extract data from web
            logger.info("Step 1: Extracting contact data from web...")
            raw_contacts = self.extractor.extract_contacts()
            
            if not raw_contacts:
                logger.warning("No contacts extracted, ending process")
                return False
            
            # Step 2: Filter contacts
            logger.info("Step 2: Filtering contacts based on criteria...")
            filtered_contacts = self.filter.filter_contacts(raw_contacts)
            
            if not filtered_contacts:
                logger.warning("No contacts match filtering criteria")
                # Still register the process with 0 records
                self.tracker.register_etl_process(0, "No contacts matched filtering criteria")
                return True
            
            # Step 3: Connect to MongoDB and insert data
            logger.info("Step 3: Connecting to MongoDB and inserting data...")
            self.db_handler.connect()
            inserted_count = self.db_handler.insert_contacts(filtered_contacts, self.proceso_id)
            
            # Step 4: Register ETL process
            logger.info("Step 4: Registering ETL process via API...")
            registration_success = self.tracker.register_etl_process(
                inserted_count, 
                f"ETL Process {self.proceso_id} - Inserted {inserted_count} contacts"
            )
            
            # Step 5: Summary
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            logger.info(f"ETL process completed successfully!")
            logger.info(f"Process ID: {self.proceso_id}")
            logger.info(f"Raw contacts extracted: {len(raw_contacts)}")
            logger.info(f"Contacts after filtering: {len(filtered_contacts)}")
            logger.info(f"Contacts inserted: {inserted_count}")
            logger.info(f"Duration: {duration:.2f} seconds")
            logger.info(f"API registration: {'Success' if registration_success else 'Failed'}")
            
            return True
            
        except Exception as e:
            logger.error(f"ETL process failed: {str(e)}")
            return False
        
        finally:
            # Clean up
            self.db_handler.close()

def main():
    """Main entry point"""
    logger.info("ETL Business Contacts Scraper Starting...")
    
    processor = ETLProcessor()
    success = processor.run()
    
    if success:
        logger.info("ETL process completed successfully!")
        sys.exit(0)
    else:
        logger.error("ETL process failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()