# PostMini - Example API Specifications

This directory contains sample OpenAPI/Swagger specifications for testing the import functionality.

## 📁 **Files**

### **1. `sample_petstore_api.json`**
- **Format**: OpenAPI 3.0 (JSON)
- **Description**: Sample Pet Store API with 6 endpoints
- **Features Demonstrated**:
  - Path parameters (`/pet/{petId}`)
  - Query parameters (`/pet/findByStatus?status=`)
  - POST requests with JSON bodies
  - PUT, GET, DELETE methods
  - Object schemas with properties
  - Date-time fields
  - Email format fields

**Endpoints**:
- `POST /pet` - Add a new pet
- `PUT /pet` - Update an existing pet
- `GET /pet/{petId}` - Find pet by ID
- `DELETE /pet/{petId}` - Delete a pet
- `GET /pet/findByStatus` - Find pets by status
- `POST /store/order` - Place an order
- `POST /user` - Create user

### **2. `sample_api_swagger2.yaml`**
- **Format**: Swagger 2.0 (YAML)
- **Description**: Simple Store API with 4 endpoints
- **Features Demonstrated**:
  - Swagger 2.0 compatibility
  - YAML format support
  - Query parameters
  - Path parameters
  - Request body schemas

**Endpoints**:
- `GET /products` - List all products
- `POST /products` - Create a product
- `GET /products/{id}` - Get product by ID
- `DELETE /products/{id}` - Delete product

---

## 🚀 **How to Use**

### **Import into PostMini**

1. **Open PostMini**

2. **Click "📥 Import" dropdown** at the bottom-left

3. **Select "📋 Import OpenAPI/Swagger"**

4. **Choose a sample file:**
   - `sample_petstore_api.json` (OpenAPI 3.0, JSON)
   - `sample_api_swagger2.yaml` (Swagger 2.0, YAML)

5. **Review the Import Summary** showing:
   - API title and version
   - Base URL
   - Number of endpoints
   - Description

6. **Click "Import"**

7. **Enter a collection name** (or use the suggested name)

8. **Done!** The collection will be created with all requests ready to use

---

## ✅ **What Gets Imported**

For each endpoint, PostMini automatically creates:

- ✅ **HTTP Method** (GET, POST, PUT, DELETE, etc.)
- ✅ **Full URL** (base URL + path)
- ✅ **Path Parameters** (extracted to Params tab)
- ✅ **Query Parameters** (extracted to Params tab)
- ✅ **Request Body** (auto-generated from schema)
- ✅ **Example Data** (based on schema types and formats)
- ✅ **Authentication** (Bearer Token, API Key if defined)

---

## 🎨 **Example Data Generation**

PostMini generates realistic example data based on schema types:

| Schema Type | Example Generated |
|------------|-------------------|
| `string` | `"string"` |
| `string` (format: `email`) | `"user@example.com"` |
| `string` (format: `uuid`) | `"123e4567-e89b-12d3-a456-426614174000"` |
| `string` (format: `date-time`) | `"2023-01-01T00:00:00Z"` |
| `integer` | `0` |
| `number` | `0.0` |
| `boolean` | `true` |
| `enum` | First enum value |

---

## 📝 **Creating Your Own Specs**

You can import your own OpenAPI/Swagger specifications:

### **Supported Formats**
- ✅ OpenAPI 3.0
- ✅ OpenAPI 3.1
- ✅ Swagger 2.0
- ✅ JSON files (`.json`)
- ✅ YAML files (`.yaml`, `.yml`)

### **Example Minimal Spec**

```yaml
openapi: 3.0.0
info:
  title: My API
  version: 1.0.0
servers:
  - url: https://api.myapp.com
paths:
  /users:
    get:
      summary: Get all users
      responses:
        '200':
          description: Success
```

---

## 🔗 **More Resources**

- **OpenAPI Specification**: https://swagger.io/specification/
- **Swagger Editor**: https://editor.swagger.io/
- **OpenAPI Examples**: https://github.com/OAI/OpenAPI-Specification/tree/main/examples

---

**Last Updated**: October 17, 2025  
**PostMini Version**: 1.4.0+

