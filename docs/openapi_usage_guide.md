# Bitaxe OpenAPI Usage Guide

This guide explains how to use the OpenAPI specification for Bitaxe miners.

## 📁 File Location

Save the OpenAPI specification as:
```
docs/bitaxe-api.yaml
```

## 🛠️ Tools and Integration

### 1. Interactive Documentation (Swagger UI)

**Online Swagger Editor:**
```bash
# Visit: https://editor.swagger.io/
# Copy-paste the YAML content or upload the file
```

**Local Swagger UI:**
```bash
# Install swagger-ui-serve
npm install -g swagger-ui-serve

# Serve the documentation
swagger-ui-serve docs/bitaxe-api.yaml

# Opens in browser at http://localhost:3000
```

**Docker Swagger UI:**
```bash
docker run -p 8080:8080 -e SWAGGER_JSON=/app/bitaxe-api.yaml -v $(pwd)/docs:/app swaggerapi/swagger-ui
```

### 2. Code Generation

**Generate Python Client:**
```bash
# Install OpenAPI Generator
pip install openapi-generator-cli

# Generate Python client
openapi-generator-cli generate \
  -i docs/bitaxe-api.yaml \
  -g python \
  -o generated/python-client \
  --package-name bitaxe_client

# Usage example:
from bitaxe_client import ApiClient, SystemInformationApi

client = ApiClient()
client.configuration.host = "http://192.168.1.45"
api = SystemInformationApi(client)
system_info = api.get_system_info()
```

**Generate JavaScript Client:**
```bash
openapi-generator-cli generate \
  -i docs/bitaxe-api.yaml \
  -g javascript \
  -o generated/js-client

# Usage in Node.js:
const BitaxeApi = require('./generated/js-client');
const api = new BitaxeApi.SystemInformationApi();
api.getSystemInfo().then(data => console.log(data));
```

**Generate Go Client:**
```bash
openapi-generator-cli generate \
  -i docs/bitaxe-api.yaml \
  -g go \
  -o generated/go-client

# Usage in Go:
import "github.com/yourusername/bitaxe-client-go"

client := bitaxe.NewAPIClient(bitaxe.NewConfiguration())
ctx := context.Background()
info, _, err := client.SystemInformationApi.GetSystemInfo(ctx).Execute()
```

### 3. API Testing

**Postman Collection:**
```bash
# Generate Postman collection
openapi-generator-cli generate \
  -i docs/bitaxe-api.yaml \
  -g postman-collection \
  -o generated/postman

# Import the generated collection into Postman
```

**Insomnia Import:**
- Open Insomnia
- File → Import/Export → Import Data
- Select the YAML file
- All endpoints will be imported with examples

### 4. Mock Server

**Prism Mock Server:**
```bash
# Install Prism
npm install -g @stoplight/prism-cli

# Start mock server
prism mock docs/bitaxe-api.yaml --port 4010

# Test endpoints:
curl http://localhost:4010/api/system/info
```

**OpenAPI Mock Server:**
```bash
# Docker approach
docker run --rm -p 8000:8000 \
  -v $(pwd)/docs:/app \
  danielgtaylor/apisprout \
  /app/bitaxe-api.yaml

# Test with curl:
curl http://localhost:8000/api/system/info
```

## 🔧 Validation and Testing

### Schema Validation

**Python with jsonschema:**
```python
import yaml
import jsonschema
import requests

# Load OpenAPI spec
with open('docs/bitaxe-api.yaml', 'r') as f:
    spec = yaml.safe_load(f)

# Extract response schema
response_schema = spec['components']['schemas']['SystemInfo']

# Validate actual API response
response = requests.get('http://192.168.1.45/api/system/info')
data = response.json()

try:
    jsonschema.validate(data, response_schema)
    print("✅ API response matches schema")
except jsonschema.ValidationError as e:
    print(f"❌ Schema violation: {e.message}")
```

**JavaScript with Ajv:**
```javascript
const Ajv = require('ajv');
const yaml = require('js-yaml');
const fs = require('fs');
const axios = require('axios');

// Load schema
const spec = yaml.load(fs.readFileSync('docs/bitaxe-api.yaml', 'utf8'));
const schema = spec.components.schemas.SystemInfo;

// Validate response
const ajv = new Ajv();
const validate = ajv.compile(schema);

axios.get('http://192.168.1.45/api/system/info')
  .then(response => {
    const valid = validate(response.data);
    if (valid) {
      console.log('✅ API response matches schema');
    } else {
      console.log('❌ Schema violations:', validate.errors);
    }
  });
```

## 📚 Documentation Generation

### HTML Documentation

**ReDoc:**
```bash
# Install ReDoc CLI
npm install -g redoc-cli

# Generate HTML documentation
redoc-cli build docs/bitaxe-api.yaml --output docs/api-documentation.html

# Serve locally
redoc-cli serve docs/bitaxe-api.yaml --port 8080
```

**Swagger Codegen:**
```bash
# Generate HTML docs
swagger-codegen generate \
  -i docs/bitaxe-api.yaml \
  -l html2 \
  -o generated/html-docs
```

### PDF Documentation

**wkhtmltopdf approach:**
```bash
# First generate HTML with ReDoc
redoc-cli build docs/bitaxe-api.yaml --output temp-docs.html

# Convert to PDF
wkhtmltopdf temp-docs.html docs/bitaxe-api-documentation.pdf

# Cleanup
rm temp-docs.html
```

## 🔨 Custom Tools Integration

### Monitoring Script Integration

**Enhanced Monitor with OpenAPI:**
```python
# Add to bitaxe_monitor.py
import yaml
import jsonschema

class OpenAPIValidator:
    def __init__(self, spec_file):
        with open(spec_file, 'r') as f:
            self.spec = yaml.safe_load(f)
        self.response_schema = self.spec['components']['schemas']['SystemInfo']
    
    def validate_response(self, data):
        try:
            jsonschema.validate(data, self.response_schema)
            return True, None
        except jsonschema.ValidationError as e:
            return False, e.message

# Usage in monitor
validator = OpenAPIValidator('docs/bitaxe-api.yaml')
is_valid, error = validator.validate_response(api_response)
if not is_valid:
    logger.warning(f"API response validation failed: {error}")
```

### Configuration Generator

**Generate config from OpenAPI:**
```python
import yaml

def generate_config_from_openapi(spec_file):
    """Generate configuration template from OpenAPI spec"""
    with open(spec_file, 'r') as f:
        spec = yaml.safe_load(f)
    
    # Extract configurable parameters
    config_schema = spec['components']['schemas']['SystemConfigUpdate']
    
    template = {}
    for param, details in config_schema['properties'].items():
        template[param] = {
            'description': details.get('description', ''),
            'type': details.get('type', 'unknown'),
            'example': details.get('example'),
            'min': details.get('minimum'),
            'max': details.get('maximum'),
            'enum': details.get('enum')
        }
    
    return template

# Generate configuration documentation
config_template = generate_config_from_openapi('docs/bitaxe-api.yaml')
print(yaml.dump(config_template, default_flow_style=False))
```

## 🌐 Web Integration

### REST Client Libraries

**Python requests wrapper:**
```python
class BitaxeClient:
    def __init__(self, host, port=80):
        self.base_url = f"http://{host}:{port}"
    
    def get_system_info(self):
        """Get system information - matches OpenAPI spec"""
        response = requests.get(f"{self.base_url}/api/system/info")
        response.raise_for_status()
        return response.json()
    
    def restart_system(self):
        """Restart system - matches OpenAPI spec"""
        response = requests.post(f"{self.base_url}/api/system/restart")
        response.raise_for_status()
        return response.json()
    
    def update_config(self, **kwargs):
        """Update configuration - matches OpenAPI spec"""
        response = requests.patch(f"{self.base_url}/api/system", json=kwargs)
        response.raise_for_status()
        return response.json()

# Usage
client = BitaxeClient('192.168.1.45')
info = client.get_system_info()
client.update_config(fanspeed=75, frequency=550)
```

### TypeScript Definitions

**Generate TypeScript interfaces:**
```bash
# Generate TypeScript client
openapi-generator-cli generate \
  -i docs/bitaxe-api.yaml \
  -g typescript-axios \
  -o generated/typescript-client

# Usage in TypeScript:
import { SystemInformationApi, Configuration } from './generated/typescript-client';

const config = new Configuration({
  basePath: 'http://192.168.1.45'
});

const api = new SystemInformationApi(config);
const systemInfo = await api.getSystemInfo();
```

## 📋 Integration Checklist

- [ ] **Validate YAML syntax** - Use YAML validator
- [ ] **Test endpoints** - Verify all endpoints work with real hardware
- [ ] **Generate client code** - For your preferred programming language
- [ ] **Set up documentation** - Host API docs for team access
- [ ] **Validate responses** - Ensure API responses match schema
- [ ] **Create mock server** - For development and testing
- [ ] **Generate Postman collection** - For manual testing
- [ ] **Set up CI/CD validation** - Automatically validate API changes

## 🔄 Maintenance

### Updating the Specification

1. **Firmware Updates:**
   - Check for new API endpoints
   - Verify response format changes
   - Update version numbers

2. **Schema Updates:**
   - Validate with real API responses
   - Update examples with current data
   - Test generated code

3. **Version Control:**
   - Tag releases with semantic versioning
   - Maintain changelog for API changes
   - Document breaking changes

### Automated Validation Pipeline

```yaml
# .github/workflows/api-validation.yml
name: API Validation
on: [push, pull_request]

jobs:
  validate-openapi:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Validate OpenAPI spec
        uses: mbowman100/swagger-validator-action@master
        with:
          files: docs/bitaxe-api.yaml
      
      - name: Generate documentation
        run: |
          npm install -g redoc-cli
          redoc-cli build docs/bitaxe-api.yaml --output api-docs.html
      
      - name: Test mock server
        run: |
          npm install -g @stoplight/prism-cli
          prism mock docs/bitaxe-api.yaml --port 4010 &
          sleep 5
          curl -f http://localhost:4010/api/system/info
```

This OpenAPI specification provides a complete, standards-compliant description of the Bitaxe API that can be used for documentation, code generation, testing, and integration across multiple programming languages and tools.
