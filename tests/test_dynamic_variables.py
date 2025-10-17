"""
Tests for Dynamic Variables Feature

Tests the dynamic variable generation and substitution system.
"""

import pytest
import re
import uuid
import time
from src.features.dynamic_variables import (
    DynamicVariables,
    resolve_dynamic_variable,
    get_all_dynamic_variables
)


class TestDynamicVariables:
    """Test dynamic variable generation."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.dv = DynamicVariables()
    
    def test_guid_generation(self):
        """Test $guid generation."""
        guid = self.dv.resolve('$guid')
        # UUID format: 8-4-4-4-12 hex digits
        assert re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', guid)
        
        # Test uniqueness
        guid2 = self.dv.resolve('$guid')
        assert guid != guid2
    
    def test_random_uuid_generation(self):
        """Test $randomUUID generation."""
        uuid_val = self.dv.resolve('$randomUUID')
        assert re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', uuid_val)
    
    def test_timestamp_generation(self):
        """Test $timestamp generation."""
        before = int(time.time())
        timestamp = self.dv.resolve('$timestamp')
        after = int(time.time())
        
        assert timestamp.isdigit()
        ts_int = int(timestamp)
        assert before <= ts_int <= after
    
    def test_iso_timestamp_generation(self):
        """Test $isoTimestamp generation."""
        iso_ts = self.dv.resolve('$isoTimestamp')
        # ISO format: YYYY-MM-DDTHH:MM:SS.ffffff
        assert 'T' in iso_ts
        assert len(iso_ts) > 10
    
    def test_random_int_generation(self):
        """Test $randomInt generation."""
        random_int = self.dv.resolve('$randomInt')
        assert random_int.isdigit()
        value = int(random_int)
        assert 1 <= value <= 1000
    
    def test_random_string_generation(self):
        """Test $randomString generation."""
        random_str = self.dv.resolve('$randomString')
        assert len(random_str) == 10
        assert random_str.isalnum()
    
    def test_random_alphanumeric_generation(self):
        """Test $randomAlphaNumeric generation."""
        random_str = self.dv.resolve('$randomAlphaNumeric')
        assert len(random_str) == 10
        assert random_str.isalnum()
    
    def test_random_email_generation(self):
        """Test $randomEmail generation."""
        email = self.dv.resolve('$randomEmail')
        assert '@' in email
        assert '.' in email
        # Check valid email format
        assert re.match(r'^[a-z0-9]+@[a-z]+\.[a-z]+$', email)
    
    def test_random_username_generation(self):
        """Test $randomUserName generation."""
        username = self.dv.resolve('$randomUserName')
        assert len(username) == 10
        assert username.islower()
        assert username.isalnum()
    
    def test_random_first_name_generation(self):
        """Test $randomFirstName generation."""
        first_name = self.dv.resolve('$randomFirstName')
        assert len(first_name) > 2
        assert first_name.isalpha()
        assert first_name[0].isupper()
    
    def test_random_last_name_generation(self):
        """Test $randomLastName generation."""
        last_name = self.dv.resolve('$randomLastName')
        assert len(last_name) > 2
        assert last_name.isalpha()
        assert last_name[0].isupper()
    
    def test_random_full_name_generation(self):
        """Test $randomFullName generation."""
        full_name = self.dv.resolve('$randomFullName')
        assert ' ' in full_name
        parts = full_name.split()
        assert len(parts) == 2
        assert parts[0][0].isupper()
        assert parts[1][0].isupper()
    
    def test_random_name_prefix_generation(self):
        """Test $randomNamePrefix generation."""
        prefix = self.dv.resolve('$randomNamePrefix')
        assert prefix in ['Mr.', 'Mrs.', 'Ms.', 'Dr.', 'Prof.']
    
    def test_random_name_suffix_generation(self):
        """Test $randomNameSuffix generation."""
        suffix = self.dv.resolve('$randomNameSuffix')
        assert suffix in ['Jr.', 'Sr.', 'II', 'III', 'IV']
    
    def test_random_phone_generation(self):
        """Test $randomPhoneNumber generation."""
        phone = self.dv.resolve('$randomPhoneNumber')
        assert phone.startswith('+1-')
        # Format: +1-XXX-XXX-XXXX
        assert re.match(r'^\+1-\d{3}-\d{3}-\d{4}$', phone)
    
    def test_random_phone_ext_generation(self):
        """Test $randomPhoneNumberExt generation."""
        phone_ext = self.dv.resolve('$randomPhoneNumberExt')
        assert 'ext.' in phone_ext
        assert phone_ext.startswith('+1-')
    
    def test_random_city_generation(self):
        """Test $randomCity generation."""
        city = self.dv.resolve('$randomCity')
        assert len(city) > 2
        # Should be from known list
        assert city in self.dv._CITIES
    
    def test_random_country_generation(self):
        """Test $randomCountry generation."""
        country = self.dv.resolve('$randomCountry')
        assert len(country) > 2
        assert country in self.dv._COUNTRIES
    
    def test_random_country_code_generation(self):
        """Test $randomCountryCode generation."""
        code = self.dv.resolve('$randomCountryCode')
        assert len(code) == 2
        assert code.isupper()
        assert code.isalpha()
    
    def test_random_street_name_generation(self):
        """Test $randomStreetName generation."""
        street = self.dv.resolve('$randomStreetName')
        assert ' ' in street
        # Should end with a street suffix
        assert any(suffix in street for suffix in self.dv._STREET_SUFFIXES)
    
    def test_random_street_address_generation(self):
        """Test $randomStreetAddress generation."""
        address = self.dv.resolve('$randomStreetAddress')
        parts = address.split(' ', 1)
        assert len(parts) == 2
        assert parts[0].isdigit()  # Number part
    
    def test_random_ip_generation(self):
        """Test $randomIP generation."""
        ip = self.dv.resolve('$randomIP')
        # IPv4 format: X.X.X.X
        assert re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', ip)
        parts = ip.split('.')
        assert all(0 <= int(p) <= 255 for p in parts)
    
    def test_random_ipv6_generation(self):
        """Test $randomIPV6 generation."""
        ipv6 = self.dv.resolve('$randomIPV6')
        # IPv6 format: X:X:X:X:X:X:X:X
        assert ipv6.count(':') == 7
        parts = ipv6.split(':')
        assert len(parts) == 8
    
    def test_random_mac_generation(self):
        """Test $randomMACAddress generation."""
        mac = self.dv.resolve('$randomMACAddress')
        # MAC format: XX:XX:XX:XX:XX:XX
        assert re.match(r'^[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}$', mac)
    
    def test_random_password_generation(self):
        """Test $randomPassword generation."""
        password = self.dv.resolve('$randomPassword')
        assert len(password) == 16
        # Should contain letters, digits, and special chars
        assert any(c.isalpha() for c in password)
        assert any(c.isdigit() for c in password)
    
    def test_random_url_generation(self):
        """Test $randomUrl generation."""
        url = self.dv.resolve('$randomUrl')
        assert url.startswith('http://') or url.startswith('https://')
        assert '.' in url
    
    def test_random_domain_generation(self):
        """Test $randomDomainName generation."""
        domain = self.dv.resolve('$randomDomainName')
        assert '.' in domain
        parts = domain.split('.')
        assert len(parts) == 2
        assert parts[1] in ['com', 'org', 'net', 'io', 'co']
    
    def test_random_color_generation(self):
        """Test $randomColor generation."""
        color = self.dv.resolve('$randomColor')
        assert color in self.dv._COLORS
    
    def test_random_hex_color_generation(self):
        """Test $randomHexColor generation."""
        hex_color = self.dv.resolve('$randomHexColor')
        assert hex_color.startswith('#')
        assert len(hex_color) == 7
        assert re.match(r'^#[0-9a-f]{6}$', hex_color)
    
    def test_random_price_generation(self):
        """Test $randomPrice generation."""
        price = self.dv.resolve('$randomPrice')
        assert '.' in price
        parts = price.split('.')
        assert len(parts) == 2
        assert parts[0].isdigit()
        assert len(parts[1]) == 2
    
    def test_random_credit_card_generation(self):
        """Test $randomCreditCardNumber generation."""
        cc = self.dv.resolve('$randomCreditCardNumber')
        assert len(cc) == 16
        assert cc.isdigit()
    
    def test_random_company_name_generation(self):
        """Test $randomCompanyName generation."""
        company = self.dv.resolve('$randomCompanyName')
        assert ' ' in company
        assert any(suffix in company for suffix in ['Inc.', 'LLC', 'Corp.', 'Ltd.', 'Group', 'Solutions'])
    
    def test_random_company_suffix_generation(self):
        """Test $randomCompanySuffix generation."""
        suffix = self.dv.resolve('$randomCompanySuffix')
        assert suffix in ['Inc.', 'LLC', 'Corp.', 'Ltd.', 'Group', 'Solutions']
    
    def test_random_job_title_generation(self):
        """Test $randomJobTitle generation."""
        job = self.dv.resolve('$randomJobTitle')
        assert ' ' in job
        parts = job.split()
        assert len(parts) == 2
    
    def test_random_boolean_generation(self):
        """Test $randomBoolean generation."""
        boolean = self.dv.resolve('$randomBoolean')
        assert boolean in ['true', 'false']
    
    def test_invalid_variable(self):
        """Test handling of invalid variable."""
        result = self.dv.resolve('$invalidVariable')
        assert result == '$invalidVariable'  # Returns original if not found
    
    def test_get_all_variables(self):
        """Test getting all supported variables."""
        all_vars = self.dv.get_all_variables()
        assert len(all_vars) > 30
        assert '$guid' in all_vars
        assert '$timestamp' in all_vars
        assert '$randomEmail' in all_vars
    
    def test_convenience_function(self):
        """Test convenience function resolve_dynamic_variable."""
        guid = resolve_dynamic_variable('$guid')
        assert re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', guid)
    
    def test_get_all_convenience_function(self):
        """Test convenience function get_all_dynamic_variables."""
        all_vars = get_all_dynamic_variables()
        assert len(all_vars) > 30


class TestDynamicVariablesIntegration:
    """Test dynamic variables integration with variable substitution."""
    
    def test_substitution_in_url(self):
        """Test dynamic variable substitution in URL."""
        from src.features.variable_substitution import VariableSubstitution
        
        url = "https://api.example.com/users/$guid/orders"
        result, unresolved = VariableSubstitution.substitute(url, {})
        
        # $guid should be replaced
        assert '$guid' not in result
        assert 'https://api.example.com/users/' in result
        assert '/orders' in result
        # UUID should be present
        assert re.search(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', result)
    
    def test_substitution_in_body(self):
        """Test dynamic variable substitution in request body."""
        from src.features.variable_substitution import VariableSubstitution
        
        body = '{"id": "$guid", "email": "$randomEmail", "timestamp": "$timestamp"}'
        result, unresolved = VariableSubstitution.substitute(body, {})
        
        # All variables should be replaced
        assert '$guid' not in result
        assert '$randomEmail' not in result
        assert '$timestamp' not in result
        
        # Check if valid JSON
        import json
        data = json.loads(result)
        assert 'id' in data
        assert 'email' in data
        assert 'timestamp' in data
        assert '@' in data['email']
    
    def test_mixed_variables(self):
        """Test mixing dynamic variables and environment variables."""
        from src.features.variable_substitution import VariableSubstitution
        
        text = "{{baseUrl}}/users/$guid?timestamp=$timestamp"
        env_vars = {'baseUrl': 'https://api.example.com'}
        
        result, unresolved = VariableSubstitution.substitute(text, env_vars)
        
        # Both types should be replaced
        assert '{{baseUrl}}' not in result
        assert '$guid' not in result
        assert '$timestamp' not in result
        assert 'https://api.example.com/users/' in result
    
    def test_multiple_same_variables(self):
        """Test multiple occurrences of same variable get different values."""
        from src.features.variable_substitution import VariableSubstitution
        
        text = "First: $guid, Second: $guid"
        result, unresolved = VariableSubstitution.substitute(text, {})
        
        # Extract both GUIDs
        guids = re.findall(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', result)
        assert len(guids) == 2
        # Each call should generate a unique GUID
        assert guids[0] != guids[1]
    
    def test_unresolved_dynamic_variable(self):
        """Test that invalid dynamic variables are reported as unresolved."""
        from src.features.variable_substitution import VariableSubstitution
        
        text = "Valid: $guid, Invalid: $notAVariable"
        result, unresolved = VariableSubstitution.substitute(text, {})
        
        assert '$notAVariable' in unresolved
        assert '$guid' not in unresolved


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

