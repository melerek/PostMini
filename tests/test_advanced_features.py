"""
Tests for pm.cookies API, require('lodash'), and require('uuid')

Tests cookie management and utility libraries.
"""

import pytest
from src.features.script_engine import ScriptEngine


class TestPmCookies:
    """Test pm.cookies API."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.engine = ScriptEngine()
        self.env = {}
        self.collection_vars = {}
    
    def test_cookies_set_and_get(self):
        """Test setting and getting cookies."""
        script = """
        pm.cookies.set('sessionId', 'abc123');
        pm.cookies.set('userId', '456');
        
        const session = pm.cookies.get('sessionId');
        const user = pm.cookies.get('userId');
        
        pm.environment.set('session', session);
        pm.environment.set('user', user);
        """
        
        result = self.engine.execute_pre_request_script(
            script=script,
            url="https://example.com",
            method="GET",
            headers={},
            body="",
            params={},
            environment=self.env,
            collection_vars=self.collection_vars
        )
        
        assert result['environment']['session'] == 'abc123'
        assert result['environment']['user'] == '456'
    
    def test_cookies_has(self):
        """Test checking if cookie exists."""
        script = """
        pm.cookies.set('token', 'xyz');
        
        const hasToken = pm.cookies.has('token');
        const hasOther = pm.cookies.has('other');
        
        pm.environment.set('hasToken', String(hasToken));
        pm.environment.set('hasOther', String(hasOther));
        """
        
        result = self.engine.execute_pre_request_script(
            script=script,
            url="https://example.com",
            method="GET",
            headers={},
            body="",
            params={},
            environment=self.env,
            collection_vars=self.collection_vars
        )
        
        assert result['environment']['hasToken'] == 'true'
        assert result['environment']['hasOther'] == 'false'
    
    def test_cookies_clear(self):
        """Test clearing cookies."""
        script = """
        pm.cookies.set('temp', 'value');
        pm.environment.set('before', String(pm.cookies.has('temp')));
        
        pm.cookies.clear('temp');
        pm.environment.set('after', String(pm.cookies.has('temp')));
        """
        
        result = self.engine.execute_pre_request_script(
            script=script,
            url="https://example.com",
            method="GET",
            headers={},
            body="",
            params={},
            environment=self.env,
            collection_vars=self.collection_vars
        )
        
        assert result['environment']['before'] == 'true'
        assert result['environment']['after'] == 'false'
    
    def test_cookies_toObject(self):
        """Test getting all cookies as object."""
        script = """
        pm.cookies.set('cookie1', 'value1');
        pm.cookies.set('cookie2', 'value2');
        
        const allCookies = pm.cookies.toObject();
        pm.environment.set('count', String(Object.keys(allCookies).length));
        pm.environment.set('has1', String('cookie1' in allCookies));
        pm.environment.set('has2', String('cookie2' in allCookies));
        """
        
        result = self.engine.execute_pre_request_script(
            script=script,
            url="https://example.com",
            method="GET",
            headers={},
            body="",
            params={},
            environment=self.env,
            collection_vars=self.collection_vars
        )
        
        assert result['environment']['count'] == '2'
        assert result['environment']['has1'] == 'true'
        assert result['environment']['has2'] == 'true'


class TestRequireLodash:
    """Test require('lodash') support."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.engine = ScriptEngine()
        self.env = {}
        self.collection_vars = {}
    
    def test_lodash_import(self):
        """Test importing lodash."""
        script = """
        const _ = require('lodash');
        pm.environment.set('imported', String(typeof _ === 'object'));
        """
        
        result = self.engine.execute_pre_request_script(
            script=script,
            url="https://example.com",
            method="GET",
            headers={},
            body="",
            params={},
            environment=self.env,
            collection_vars=self.collection_vars
        )
        
        assert result['environment']['imported'] == 'true'
    
    def test_lodash_array_methods(self):
        """Test lodash array utility methods."""
        script = """
        const _ = require('lodash');
        
        // chunk
        const chunked = _.chunk([1, 2, 3, 4, 5], 2);
        pm.environment.set('chunkLength', String(chunked.length));
        
        // compact
        const compacted = _.compact([0, 1, false, 2, '', 3]);
        pm.environment.set('compactLength', String(compacted.length));
        
        // uniq
        const unique = _.uniq([1, 2, 2, 3, 3, 3]);
        pm.environment.set('uniqueLength', String(unique.length));
        
        // flatten
        const flattened = _.flatten([1, [2, 3], [4]]);
        pm.environment.set('flatLength', String(flattened.length));
        """
        
        result = self.engine.execute_pre_request_script(
            script=script,
            url="https://example.com",
            method="GET",
            headers={},
            body="",
            params={},
            environment=self.env,
            collection_vars=self.collection_vars
        )
        
        assert result['environment']['chunkLength'] == '3'  # [[1,2], [3,4], [5]]
        assert result['environment']['compactLength'] == '3'  # [1, 2, 3]
        assert result['environment']['uniqueLength'] == '3'  # [1, 2, 3]
        assert result['environment']['flatLength'] == '4'  # [1, 2, 3, 4]
    
    def test_lodash_collection_methods(self):
        """Test lodash collection methods."""
        script = """
        const _ = require('lodash');
        
        const data = [
            { name: 'Alice', age: 30 },
            { name: 'Bob', age: 25 },
            { name: 'Charlie', age: 35 }
        ];
        
        // map
        const names = _.map(data, item => item.name);
        pm.environment.set('namesLength', String(names.length));
        
        // filter
        const adults = _.filter(data, item => item.age >= 30);
        pm.environment.set('adultsCount', String(adults.length));
        
        // find
        const bob = _.find(data, item => item.name === 'Bob');
        pm.environment.set('bobAge', String(bob.age));
        
        // size
        pm.environment.set('dataSize', String(_.size(data)));
        """
        
        result = self.engine.execute_pre_request_script(
            script=script,
            url="https://example.com",
            method="GET",
            headers={},
            body="",
            params={},
            environment=self.env,
            collection_vars=self.collection_vars
        )
        
        assert result['environment']['namesLength'] == '3'
        assert result['environment']['adultsCount'] == '2'
        assert result['environment']['bobAge'] == '25'
        assert result['environment']['dataSize'] == '3'
    
    def test_lodash_object_methods(self):
        """Test lodash object manipulation methods."""
        script = """
        const _ = require('lodash');
        
        const user = {
            name: 'John',
            address: {
                city: 'NYC',
                zip: '10001'
            }
        };
        
        // get
        const city = _.get(user, 'address.city');
        const missing = _.get(user, 'address.country', 'USA');
        pm.environment.set('city', city);
        pm.environment.set('country', missing);
        
        // has
        const hasCity = _.has(user, 'address.city');
        const hasCountry = _.has(user, 'address.country');
        pm.environment.set('hasCity', String(hasCity));
        pm.environment.set('hasCountry', String(hasCountry));
        
        // keys and values
        const keys = _.keys(user);
        pm.environment.set('keysCount', String(keys.length));
        
        // pick
        const picked = _.pick(user, 'name');
        pm.environment.set('pickedKeys', Object.keys(picked).join(','));
        """
        
        result = self.engine.execute_pre_request_script(
            script=script,
            url="https://example.com",
            method="GET",
            headers={},
            body="",
            params={},
            environment=self.env,
            collection_vars=self.collection_vars
        )
        
        assert result['environment']['city'] == 'NYC'
        assert result['environment']['country'] == 'USA'
        assert result['environment']['hasCity'] == 'true'
        assert result['environment']['hasCountry'] == 'false'
        assert result['environment']['keysCount'] == '2'
        assert result['environment']['pickedKeys'] == 'name'
    
    def test_lodash_string_methods(self):
        """Test lodash string methods."""
        script = """
        const _ = require('lodash');
        
        const str = 'hello world';
        
        pm.environment.set('capitalized', _.capitalize(str));
        pm.environment.set('upper', _.upperCase(str));
        pm.environment.set('lower', _.lowerCase('HELLO'));
        
        const startsH = _.startsWith(str, 'hello');
        const endsD = _.endsWith(str, 'world');
        pm.environment.set('startsH', String(startsH));
        pm.environment.set('endsD', String(endsD));
        """
        
        result = self.engine.execute_pre_request_script(
            script=script,
            url="https://example.com",
            method="GET",
            headers={},
            body="",
            params={},
            environment=self.env,
            collection_vars=self.collection_vars
        )
        
        assert result['environment']['capitalized'] == 'Hello world'
        assert result['environment']['upper'] == 'HELLO WORLD'
        assert result['environment']['lower'] == 'hello'
        assert result['environment']['startsH'] == 'true'
        assert result['environment']['endsD'] == 'true'
    
    def test_lodash_utility_methods(self):
        """Test lodash utility methods."""
        script = """
        const _ = require('lodash');
        
        pm.environment.set('isArray', String(_.isArray([1, 2, 3])));
        pm.environment.set('isObject', String(_.isObject({a: 1})));
        pm.environment.set('isString', String(_.isString('test')));
        pm.environment.set('isNumber', String(_.isNumber(42)));
        pm.environment.set('isEmpty', String(_.isEmpty([])));
        pm.environment.set('isEmptyObj', String(_.isEmpty({a: 1})));
        
        const obj = {a: 1, b: {c: 2}};
        const cloned = _.cloneDeep(obj);
        cloned.b.c = 999;
        pm.environment.set('originalC', String(obj.b.c));
        pm.environment.set('clonedC', String(cloned.b.c));
        """
        
        result = self.engine.execute_pre_request_script(
            script=script,
            url="https://example.com",
            method="GET",
            headers={},
            body="",
            params={},
            environment=self.env,
            collection_vars=self.collection_vars
        )
        
        assert result['environment']['isArray'] == 'true'
        assert result['environment']['isObject'] == 'true'
        assert result['environment']['isString'] == 'true'
        assert result['environment']['isNumber'] == 'true'
        assert result['environment']['isEmpty'] == 'true'
        assert result['environment']['isEmptyObj'] == 'false'
        assert result['environment']['originalC'] == '2'
        assert result['environment']['clonedC'] == '999'


class TestRequireUuid:
    """Test require('uuid') support."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.engine = ScriptEngine()
        self.env = {}
        self.collection_vars = {}
    
    def test_uuid_import(self):
        """Test importing uuid module."""
        script = """
        const uuid = require('uuid');
        pm.environment.set('imported', String(typeof uuid === 'object'));
        """
        
        result = self.engine.execute_pre_request_script(
            script=script,
            url="https://example.com",
            method="GET",
            headers={},
            body="",
            params={},
            environment=self.env,
            collection_vars=self.collection_vars
        )
        
        assert result['environment']['imported'] == 'true'
    
    def test_uuid_v4_generation(self):
        """Test UUID v4 generation."""
        script = """
        const uuid = require('uuid');
        
        const id1 = uuid.v4();
        const id2 = uuid.v4();
        
        pm.environment.set('id1', id1);
        pm.environment.set('id2', id2);
        
        // Check format (8-4-4-4-12)
        const regex = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;
        pm.environment.set('validFormat', String(regex.test(id1)));
        pm.environment.set('unique', String(id1 !== id2));
        """
        
        result = self.engine.execute_pre_request_script(
            script=script,
            url="https://example.com",
            method="GET",
            headers={},
            body="",
            params={},
            environment=self.env,
            collection_vars=self.collection_vars
        )
        
        assert result['environment']['validFormat'] == 'true'
        assert result['environment']['unique'] == 'true'
        # UUID should be 36 characters (32 hex + 4 hyphens)
        assert len(result['environment']['id1']) == 36
    
    def test_uuid_v1_generation(self):
        """Test UUID v1 generation."""
        script = """
        const uuid = require('uuid');
        
        const id = uuid.v1();
        pm.environment.set('id', id);
        
        // Check it's a valid UUID format
        const regex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
        pm.environment.set('validFormat', String(regex.test(id)));
        """
        
        result = self.engine.execute_pre_request_script(
            script=script,
            url="https://example.com",
            method="GET",
            headers={},
            body="",
            params={},
            environment=self.env,
            collection_vars=self.collection_vars
        )
        
        assert result['environment']['validFormat'] == 'true'
        assert len(result['environment']['id']) == 36
    
    def test_uuid_in_request(self):
        """Test using UUID in request body."""
        script = """
        const uuid = require('uuid');
        
        const requestId = uuid.v4();
        const body = {
            requestId: requestId,
            timestamp: new Date().toISOString()
        };
        
        pm.request.body.raw = JSON.stringify(body);
        pm.environment.set('requestId', requestId);
        """
        
        result = self.engine.execute_pre_request_script(
            script=script,
            url="https://example.com",
            method="POST",
            headers={},
            body="",
            params={},
            environment=self.env,
            collection_vars=self.collection_vars
        )
        
        import json
        body = json.loads(result['body'])
        assert 'requestId' in body
        assert body['requestId'] == result['environment']['requestId']
        assert 'timestamp' in body


class TestIntegrationScenarios:
    """Integration tests combining multiple features."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.engine = ScriptEngine()
    
    def test_lodash_with_response_processing(self):
        """Test using lodash to process response data."""
        script = """
        const _ = require('lodash');
        const response = pm.response.json();
        
        pm.test("Process users with lodash", function() {
            // Get all adult users
            const adults = _.filter(response.users, user => user.age >= 18);
            pm.expect(adults.length).to.equal(2);
            
            // Get user names
            const names = _.map(adults, 'name');
            pm.expect(names).to.have.members(['Alice', 'Bob']);
            
            // Check for specific user
            const alice = _.find(response.users, {name: 'Alice'});
            pm.expect(alice.age).to.equal(30);
        });
        """
        
        result = self.engine.execute_post_response_script(
            script=script,
            response_status=200,
            response_headers={'Content-Type': 'application/json'},
            response_body='{"users": [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}, {"name": "Charlie", "age": 15}]}',
            response_time_ms=100,
            environment={},
            collection_vars={}
        )
        
        assert len(result['test_results']) == 1
        assert result['test_results'][0]['passed'] is True
    
    def test_uuid_with_cookies(self):
        """Test using UUID with cookie management."""
        script = """
        const uuid = require('uuid');
        
        // Generate session ID if not exists
        if (!pm.cookies.has('sessionId')) {
            pm.cookies.set('sessionId', uuid.v4());
        }
        
        const sessionId = pm.cookies.get('sessionId');
        pm.environment.set('sessionId', sessionId);
        
        // Validate format
        const regex = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;
        pm.environment.set('valid', String(regex.test(sessionId)));
        """
        
        result = self.engine.execute_pre_request_script(
            script=script,
            url="https://example.com",
            method="GET",
            headers={},
            body="",
            params={},
            environment={},
            collection_vars={}
        )
        
        assert result['environment']['valid'] == 'true'
        assert len(result['environment']['sessionId']) == 36
    
    def test_complete_workflow(self):
        """Test complete workflow using cookies, lodash, and uuid."""
        script = """
        const _ = require('lodash');
        const uuid = require('uuid');
        
        // Setup request
        const requestId = uuid.v4();
        pm.cookies.set('requestId', requestId);
        
        const userData = {
            id: requestId,
            name: 'Test User',
            email: 'test@example.com'
        };
        
        // Use lodash to pick only needed fields
        const payload = _.pick(userData, ['id', 'name']);
        pm.request.body.raw = JSON.stringify(payload);
        
        // Store for verification
        pm.environment.set('sentId', requestId);
        pm.environment.set('hasEmail', String(_.has(payload, 'email')));
        """
        
        result = self.engine.execute_pre_request_script(
            script=script,
            url="https://example.com",
            method="POST",
            headers={},
            body="",
            params={},
            environment={},
            collection_vars={}
        )
        
        import json
        body = json.loads(result['body'])
        assert 'id' in body
        assert 'name' in body
        assert 'email' not in body  # Should be omitted by _.pick
        assert result['environment']['hasEmail'] == 'false'
