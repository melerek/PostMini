"""
Dynamic Variables Module

Provides Postman-compatible dynamic variables for API testing.
Supports $variable syntax for auto-generated values.
"""

import uuid
import time
import random
import string
from datetime import datetime
from typing import Callable, Dict


class DynamicVariables:
    """
    Generate dynamic variable values for API requests.
    
    Supports Postman-compatible variables like:
    - $guid, $timestamp, $isoTimestamp
    - $randomInt, $randomString, $randomEmail
    - And 20+ more...
    """
    
    # Sample data for random generation
    _FIRST_NAMES = [
        'James', 'Mary', 'John', 'Patricia', 'Robert', 'Jennifer', 'Michael', 'Linda',
        'William', 'Barbara', 'David', 'Elizabeth', 'Richard', 'Susan', 'Joseph', 'Jessica',
        'Thomas', 'Sarah', 'Charles', 'Karen', 'Christopher', 'Nancy', 'Daniel', 'Lisa',
        'Matthew', 'Betty', 'Anthony', 'Margaret', 'Mark', 'Sandra', 'Donald', 'Ashley',
        'Steven', 'Kimberly', 'Paul', 'Emily', 'Andrew', 'Donna', 'Joshua', 'Michelle'
    ]
    
    _LAST_NAMES = [
        'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis',
        'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson',
        'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin', 'Lee', 'Perez', 'Thompson',
        'White', 'Harris', 'Sanchez', 'Clark', 'Ramirez', 'Lewis', 'Robinson', 'Walker',
        'Young', 'Allen', 'King', 'Wright', 'Scott', 'Torres', 'Nguyen', 'Hill', 'Flores'
    ]
    
    _CITIES = [
        'New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix', 'Philadelphia',
        'San Antonio', 'San Diego', 'Dallas', 'San Jose', 'Austin', 'Jacksonville',
        'Fort Worth', 'Columbus', 'Charlotte', 'San Francisco', 'Indianapolis', 'Seattle',
        'Denver', 'Washington', 'Boston', 'Nashville', 'Detroit', 'Portland', 'Memphis',
        'Oklahoma City', 'Las Vegas', 'Louisville', 'Baltimore', 'Milwaukee', 'Albuquerque',
        'Tucson', 'Fresno', 'Sacramento', 'Kansas City', 'Mesa', 'Atlanta', 'Omaha', 'Miami'
    ]
    
    _COUNTRIES = [
        'United States', 'Canada', 'United Kingdom', 'Australia', 'Germany', 'France',
        'Japan', 'China', 'India', 'Brazil', 'Mexico', 'Spain', 'Italy', 'Netherlands',
        'Sweden', 'Norway', 'Denmark', 'Finland', 'Poland', 'Belgium', 'Switzerland',
        'Austria', 'Ireland', 'New Zealand', 'Singapore', 'South Korea', 'Thailand',
        'Vietnam', 'Malaysia', 'Indonesia', 'Philippines', 'Argentina', 'Chile', 'Colombia'
    ]
    
    _STREET_SUFFIXES = [
        'Street', 'Avenue', 'Boulevard', 'Lane', 'Road', 'Drive', 'Court', 'Place',
        'Way', 'Circle', 'Parkway', 'Terrace', 'Trail'
    ]
    
    _COLORS = [
        'red', 'blue', 'green', 'yellow', 'orange', 'purple', 'pink', 'brown',
        'black', 'white', 'gray', 'cyan', 'magenta', 'lime', 'navy', 'teal',
        'silver', 'gold', 'maroon', 'olive', 'aqua', 'fuchsia'
    ]
    
    def __init__(self):
        """Initialize the dynamic variables resolver."""
        self._generators: Dict[str, Callable[[], str]] = {
            # UUID / GUID
            '$guid': self._gen_guid,
            '$randomUUID': self._gen_guid,
            
            # Timestamps
            '$timestamp': self._gen_timestamp,
            '$isoTimestamp': self._gen_iso_timestamp,
            
            # Numbers
            '$randomInt': self._gen_random_int,
            
            # Strings
            '$randomString': self._gen_random_string,
            '$randomAlphaNumeric': self._gen_random_alphanumeric,
            
            # Common Data
            '$randomEmail': self._gen_random_email,
            '$randomUserName': self._gen_random_username,
            '$randomFirstName': self._gen_random_first_name,
            '$randomLastName': self._gen_random_last_name,
            '$randomFullName': self._gen_random_full_name,
            '$randomNamePrefix': self._gen_random_name_prefix,
            '$randomNameSuffix': self._gen_random_name_suffix,
            
            # Contact
            '$randomPhoneNumber': self._gen_random_phone,
            '$randomPhoneNumberExt': self._gen_random_phone_ext,
            
            # Location
            '$randomCity': self._gen_random_city,
            '$randomCountry': self._gen_random_country,
            '$randomCountryCode': self._gen_random_country_code,
            '$randomStreetName': self._gen_random_street_name,
            '$randomStreetAddress': self._gen_random_street_address,
            
            # Internet
            '$randomIP': self._gen_random_ip,
            '$randomIPV6': self._gen_random_ipv6,
            '$randomMACAddress': self._gen_random_mac,
            '$randomPassword': self._gen_random_password,
            '$randomUrl': self._gen_random_url,
            '$randomDomainName': self._gen_random_domain,
            
            # Colors
            '$randomColor': self._gen_random_color,
            '$randomHexColor': self._gen_random_hex_color,
            
            # Finance
            '$randomPrice': self._gen_random_price,
            '$randomCreditCardNumber': self._gen_random_credit_card,
            
            # Business
            '$randomCompanyName': self._gen_random_company_name,
            '$randomCompanySuffix': self._gen_random_company_suffix,
            '$randomJobTitle': self._gen_random_job_title,
            
            # Boolean
            '$randomBoolean': self._gen_random_boolean,
        }
    
    def resolve(self, var_name: str) -> str:
        """
        Resolve a dynamic variable to its generated value.
        
        Args:
            var_name: Variable name (e.g., '$guid', '$timestamp')
            
        Returns:
            Generated value as string, or original var_name if not found
        """
        generator = self._generators.get(var_name)
        if generator:
            return generator()
        return var_name
    
    def get_all_variables(self) -> list[str]:
        """Get list of all supported dynamic variables."""
        return sorted(self._generators.keys())
    
    # Generator methods
    
    @staticmethod
    def _gen_guid() -> str:
        """Generate a UUID v4."""
        return str(uuid.uuid4())
    
    @staticmethod
    def _gen_timestamp() -> str:
        """Generate Unix timestamp (seconds since epoch)."""
        return str(int(time.time()))
    
    @staticmethod
    def _gen_iso_timestamp() -> str:
        """Generate ISO 8601 timestamp."""
        return datetime.now().isoformat()
    
    @staticmethod
    def _gen_random_int() -> str:
        """Generate random integer between 1 and 1000."""
        return str(random.randint(1, 1000))
    
    @staticmethod
    def _gen_random_string() -> str:
        """Generate random 10-character alphanumeric string."""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    
    @staticmethod
    def _gen_random_alphanumeric() -> str:
        """Generate random 10-character alphanumeric string."""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    
    def _gen_random_email(self) -> str:
        """Generate random email address."""
        username = self._gen_random_string().lower()
        domains = ['example.com', 'test.com', 'demo.com', 'sample.com']
        return f"{username}@{random.choice(domains)}"
    
    def _gen_random_username(self) -> str:
        """Generate random username."""
        return self._gen_random_string().lower()
    
    def _gen_random_first_name(self) -> str:
        """Generate random first name."""
        return random.choice(self._FIRST_NAMES)
    
    def _gen_random_last_name(self) -> str:
        """Generate random last name."""
        return random.choice(self._LAST_NAMES)
    
    def _gen_random_full_name(self) -> str:
        """Generate random full name."""
        return f"{self._gen_random_first_name()} {self._gen_random_last_name()}"
    
    @staticmethod
    def _gen_random_name_prefix() -> str:
        """Generate random name prefix."""
        return random.choice(['Mr.', 'Mrs.', 'Ms.', 'Dr.', 'Prof.'])
    
    @staticmethod
    def _gen_random_name_suffix() -> str:
        """Generate random name suffix."""
        return random.choice(['Jr.', 'Sr.', 'II', 'III', 'IV'])
    
    @staticmethod
    def _gen_random_phone() -> str:
        """Generate random phone number."""
        area = random.randint(200, 999)
        prefix = random.randint(200, 999)
        line = random.randint(1000, 9999)
        return f"+1-{area}-{prefix}-{line}"
    
    @staticmethod
    def _gen_random_phone_ext() -> str:
        """Generate random phone number with extension."""
        phone = DynamicVariables._gen_random_phone()
        ext = random.randint(1000, 9999)
        return f"{phone} ext. {ext}"
    
    def _gen_random_city(self) -> str:
        """Generate random city name."""
        return random.choice(self._CITIES)
    
    def _gen_random_country(self) -> str:
        """Generate random country name."""
        return random.choice(self._COUNTRIES)
    
    @staticmethod
    def _gen_random_country_code() -> str:
        """Generate random 2-letter country code."""
        return ''.join(random.choices(string.ascii_uppercase, k=2))
    
    def _gen_random_street_name(self) -> str:
        """Generate random street name."""
        name = random.choice(self._LAST_NAMES)
        suffix = random.choice(self._STREET_SUFFIXES)
        return f"{name} {suffix}"
    
    def _gen_random_street_address(self) -> str:
        """Generate random street address."""
        number = random.randint(1, 9999)
        return f"{number} {self._gen_random_street_name()}"
    
    @staticmethod
    def _gen_random_ip() -> str:
        """Generate random IPv4 address."""
        return '.'.join(str(random.randint(0, 255)) for _ in range(4))
    
    @staticmethod
    def _gen_random_ipv6() -> str:
        """Generate random IPv6 address."""
        return ':'.join(f'{random.randint(0, 65535):x}' for _ in range(8))
    
    @staticmethod
    def _gen_random_mac() -> str:
        """Generate random MAC address."""
        return ':'.join(f'{random.randint(0, 255):02x}' for _ in range(6))
    
    @staticmethod
    def _gen_random_password() -> str:
        """Generate random password."""
        chars = string.ascii_letters + string.digits + '!@#$%^&*'
        return ''.join(random.choices(chars, k=16))
    
    def _gen_random_url(self) -> str:
        """Generate random URL."""
        protocol = random.choice(['http', 'https'])
        domain = self._gen_random_domain()
        return f"{protocol}://{domain}"
    
    @staticmethod
    def _gen_random_domain() -> str:
        """Generate random domain name."""
        name = ''.join(random.choices(string.ascii_lowercase, k=8))
        tld = random.choice(['com', 'org', 'net', 'io', 'co'])
        return f"{name}.{tld}"
    
    def _gen_random_color(self) -> str:
        """Generate random color name."""
        return random.choice(self._COLORS)
    
    @staticmethod
    def _gen_random_hex_color() -> str:
        """Generate random hex color code."""
        return f"#{random.randint(0, 0xFFFFFF):06x}"
    
    @staticmethod
    def _gen_random_price() -> str:
        """Generate random price."""
        dollars = random.randint(1, 999)
        cents = random.randint(0, 99)
        return f"{dollars}.{cents:02d}"
    
    @staticmethod
    def _gen_random_credit_card() -> str:
        """Generate random credit card number (fake, for testing only)."""
        # Generate 16-digit number (not a real card)
        return ''.join(str(random.randint(0, 9)) for _ in range(16))
    
    def _gen_random_company_name(self) -> str:
        """Generate random company name."""
        name = random.choice(self._LAST_NAMES)
        suffix = self._gen_random_company_suffix()
        return f"{name} {suffix}"
    
    @staticmethod
    def _gen_random_company_suffix() -> str:
        """Generate random company suffix."""
        return random.choice(['Inc.', 'LLC', 'Corp.', 'Ltd.', 'Group', 'Solutions'])
    
    @staticmethod
    def _gen_random_job_title() -> str:
        """Generate random job title."""
        level = random.choice(['Junior', 'Senior', 'Lead', 'Principal', 'Chief'])
        role = random.choice(['Developer', 'Engineer', 'Analyst', 'Manager', 'Designer'])
        return f"{level} {role}"
    
    @staticmethod
    def _gen_random_boolean() -> str:
        """Generate random boolean."""
        return random.choice(['true', 'false'])


# Global instance for easy access
_dynamic_vars = DynamicVariables()


def resolve_dynamic_variable(var_name: str) -> str:
    """
    Convenience function to resolve a dynamic variable.
    
    Args:
        var_name: Variable name (e.g., '$guid')
        
    Returns:
        Generated value as string
    """
    return _dynamic_vars.resolve(var_name)


def get_all_dynamic_variables() -> list[str]:
    """Get list of all supported dynamic variables."""
    return _dynamic_vars.get_all_variables()

