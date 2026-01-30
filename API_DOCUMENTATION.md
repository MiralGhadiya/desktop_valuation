# Desktop Valuation API Documentation

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Base URL](#base-url)
4. [User Authentication APIs](#user-authentication-apis)
5. [Valuation APIs](#valuation-apis)
6. [Subscription APIs](#subscription-apis)
7. [Payment APIs](#payment-apis)
8. [Feedback APIs](#feedback-apis)
9. [Admin Authentication APIs](#admin-authentication-apis)
10. [Admin User Management APIs](#admin-user-management-apis)
11. [Admin Subscription Plan APIs](#admin-subscription-plan-apis)
12. [Admin User Subscription APIs](#admin-user-subscription-apis)
13. [Admin Valuation APIs](#admin-valuation-apis)
14. [Admin Dashboard APIs](#admin-dashboard-apis)
15. [Admin Feedback APIs](#admin-feedback-apis)

---

## Overview

The Desktop Valuation API is a FastAPI-based RESTful service that provides property valuation services, subscription management, payment processing, and user feedback capabilities. The API supports both regular users and administrative users with different permission levels.

### Key Features

- User registration and authentication with email verification
- Property valuation request creation and management
- Subscription plan management with country-specific pricing
- Payment processing via Razorpay
- User feedback system
- Comprehensive admin panel for managing users, subscriptions, valuations, and feedback

---

## Authentication

Most endpoints require authentication using Bearer tokens. The authentication flow is as follows:

1. **Register/Login**: Obtain `access_token` and `refresh_token`
2. **Access Protected Endpoints**: Include `Authorization: Bearer <access_token>` header
3. **Refresh Token**: When access token expires, use refresh token to get new tokens

### Authentication Headers

```
Authorization: Bearer <access_token>
```

### Token Types

- **Access Token**: Short-lived token for API access (typically expires in 15 minutes to 1 hour)
- **Refresh Token**: Long-lived token (7 days) used to obtain new access tokens

---

## Base URL

```
http://localhost:8000
```

For production, replace with your production domain.

---

## User Authentication APIs

### 1. Register User

Register a new user account.

**Endpoint:** `POST /register`

**Authentication:** Not required

**Request Body:**

```json
{
  "email": "user@example.com",
  "username": "johndoe",
  "mobile_number": "+1234567890",
  "password": "SecurePassword123!"
}
```

**Request Schema:**
- `email` (string, required): Valid email address
- `username` (string, required): Unique username
- `mobile_number` (string, required): Mobile number with country code
- `password` (string, required): User password

**Response:** `200 OK`

```json
{
  "message": "Registration successful. Please verify your email."
}
```

**Error Responses:**

- `400 Bad Request`: Email or mobile number already registered
- `500 Internal Server Error`: Registration failed

**Usage Example:**

```bash
curl -X POST "http://localhost:8000/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "johndoe",
    "mobile_number": "+1234567890",
    "password": "SecurePassword123!"
  }'
```

```python
import requests

response = requests.post(
    "http://localhost:8000/register",
    json={
        "email": "user@example.com",
        "username": "johndoe",
        "mobile_number": "+1234567890",
        "password": "SecurePassword123!"
    }
)
print(response.json())
```

**Notes:**
- Automatically assigns a FREE subscription plan if available for the user's country
- Sends verification email with token (valid for 30 minutes)
- Country is automatically detected from mobile number dial code

---

### 2. Verify Email

Verify user email address using verification token.

**Endpoint:** `GET /verify-email`

**Authentication:** Not required

**Query Parameters:**
- `token` (string, required): Email verification token from verification link

**Response:** `200 OK`

```json
{
  "message": "Email verified successfully"
}
```

**Error Responses:**

- `400 Bad Request`: Invalid or expired verification link
- `500 Internal Server Error`: Email verification failed

**Usage Example:**

```bash
curl "http://localhost:8000/verify-email?token=VERIFICATION_TOKEN_HERE"
```

**Notes:**
- Token expires after 30 minutes
- Each token can only be used once

---

### 3. Resend Verification Email

Resend email verification link to user.

**Endpoint:** `POST /resend-verification`

**Authentication:** Not required

**Request Body:**

```json
{
  "email": "user@example.com"
}
```

**Response:** `200 OK`

```json
{
  "message": "Verification email sent successfully"
}
```

**Error Responses:**

- `400 Bad Request`: Email is already verified
- `500 Internal Server Error`: Failed to resend verification email

**Usage Example:**

```bash
curl -X POST "http://localhost:8000/resend-verification" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com"}'
```

---

### 4. User Login

Authenticate user and receive access and refresh tokens.

**Endpoint:** `POST /login`

**Authentication:** Not required

**Request Body:**

```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Response:** `200 OK`

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Error Responses:**

- `401 Unauthorized`: Invalid credentials
- `403 Forbidden`: Email not verified
- `500 Internal Server Error`: Login failed

**Usage Example:**

```bash
curl -X POST "http://localhost:8000/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePassword123!"
  }'
```

```python
import requests

response = requests.post(
    "http://localhost:8000/login",
    json={
        "email": "user@example.com",
        "password": "SecurePassword123!"
    }
)
tokens = response.json()
access_token = tokens["access_token"]
```

**Notes:**
- Email must be verified before login
- Refresh token is stored in database and valid for 7 days
- All previous refresh tokens are revoked when user logs out

---

### 5. Refresh Access Token

Obtain new access token using refresh token.

**Endpoint:** `POST /refresh`

**Authentication:** Not required

**Request Body:**

```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response:** `200 OK`

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Error Responses:**

- `401 Unauthorized`: Invalid or expired refresh token
- `500 Internal Server Error`: Failed to rotate refresh token

**Usage Example:**

```bash
curl -X POST "http://localhost:8000/refresh" \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "REFRESH_TOKEN_HERE"}'
```

**Notes:**
- Refresh token rotation: old refresh token is revoked and new one is issued
- This prevents token reuse attacks

---

### 6. Get User Profile

Get current authenticated user's profile information.

**Endpoint:** `GET /profile`

**Authentication:** Required (Bearer token)

**Response:** `200 OK`

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "username": "johndoe",
  "email": "user@example.com",
  "mobile_number": "+1234567890",
  "country": "United States"
}
```

**Usage Example:**

```bash
curl "http://localhost:8000/profile" \
  -H "Authorization: Bearer ACCESS_TOKEN_HERE"
```

```python
import requests

headers = {"Authorization": f"Bearer {access_token}"}
response = requests.get("http://localhost:8000/profile", headers=headers)
profile = response.json()
```

---

### 7. Update User Profile

Update current user's profile information.

**Endpoint:** `PUT /edit-profile`

**Authentication:** Required (Bearer token)

**Request Body:**

```json
{
  "username": "newusername",
  "email": "newemail@example.com",
  "mobile_number": "+9876543210"
}
```

**Request Schema:**
- `username` (string, optional): New username
- `email` (string, optional): New email address
- `mobile_number` (string, optional): New mobile number

**Response:** `200 OK`

```json
{
  "message": "Profile updated successfully",
  "user": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "username": "newusername",
    "email": "newemail@example.com",
    "mobile_number": "+9876543210"
  }
}
```

**Error Responses:**

- `400 Bad Request`: Email or mobile number already in use
- `500 Internal Server Error`: Failed to update profile

**Usage Example:**

```bash
curl -X PUT "http://localhost:8000/edit-profile" \
  -H "Authorization: Bearer ACCESS_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newusername",
    "email": "newemail@example.com"
  }'
```

**Notes:**
- If email is changed, user must verify the new email
- Email verification status is reset when email changes

---

### 8. Change Password

Change user's password.

**Endpoint:** `POST /change-password`

**Authentication:** Required (Bearer token)

**Request Body:**

```json
{
  "old_password": "OldPassword123!",
  "new_password": "NewPassword456!",
  "confirm_password": "NewPassword456!"
}
```

**Response:** `200 OK`

```json
{
  "message": "Password changed successfully"
}
```

**Error Responses:**

- `400 Bad Request`: Passwords do not match
- `401 Unauthorized`: Old password is incorrect
- `500 Internal Server Error`: Failed to change password

**Usage Example:**

```bash
curl -X POST "http://localhost:8000/change-password" \
  -H "Authorization: Bearer ACCESS_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "old_password": "OldPassword123!",
    "new_password": "NewPassword456!",
    "confirm_password": "NewPassword456!"
  }'
```

---

### 9. Forgot Password

Request password reset link via email.

**Endpoint:** `POST /forgot-password`

**Authentication:** Not required

**Request Body:**

```json
{
  "email": "user@example.com"
}
```

**Response:** `200 OK`

```json
{
  "message": "reset link sent to email"
}
```

**Error Responses:**

- `404 Not Found`: Email is not registered
- `500 Internal Server Error`: Failed to initiate password reset

**Usage Example:**

```bash
curl -X POST "http://localhost:8000/forgot-password" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com"}'
```

**Notes:**
- Reset token expires after 30 minutes
- Reset link is sent to user's email

---

### 10. Reset Password

Reset password using token from email.

**Endpoint:** `POST /reset-password`

**Authentication:** Not required

**Request Body:**

```json
{
  "token": "RESET_TOKEN_FROM_EMAIL",
  "new_password": "NewPassword123!",
  "confirm_password": "NewPassword123!"
}
```

**Response:** `200 OK`

```json
{
  "message": "Password reset successful"
}
```

**Error Responses:**

- `400 Bad Request`: Invalid or expired token, or passwords do not match
- `500 Internal Server Error`: Password reset failed

**Usage Example:**

```bash
curl -X POST "http://localhost:8000/reset-password" \
  -H "Content-Type: application/json" \
  -d '{
    "token": "RESET_TOKEN_HERE",
    "new_password": "NewPassword123!",
    "confirm_password": "NewPassword123!"
  }'
```

---

### 11. Logout User

Logout user from all devices (revoke all refresh tokens).

**Endpoint:** `POST /logout`

**Authentication:** Required (Bearer token)

**Response:** `200 OK`

```json
{
  "message": "Logged out successfully"
}
```

**Error Responses:**

- `500 Internal Server Error`: Logout failed

**Usage Example:**

```bash
curl -X POST "http://localhost:8000/logout" \
  -H "Authorization: Bearer ACCESS_TOKEN_HERE"
```

**Notes:**
- Revokes all refresh tokens for the user
- User will need to login again to get new tokens

---

## Valuation APIs

### 1. Create Valuation Request

Create a new property valuation request.

**Endpoint:** `POST /create`

**Authentication:** Required (Bearer token)

**Content-Type:** `multipart/form-data`

**Form Data:**
- `subscription_id` (UUID, required): Active subscription ID to use for this valuation
- `country` (string, required): Country name
- `city_location` (string, required): City or location
- `full_address` (string, required): Complete property address
- `property_type` (string, required): Type of property (e.g., "residential", "commercial", "land")
- `land_area` (string, required): Land area
- `built_up_area` (string, optional): Built-up area
- `year_built` (string, optional): Year the property was built
- `estimated_market_value` (string, optional): Estimated market value
- `purpose_of_valuation` (string, required): Purpose of valuation
- `full_name` (string, required): Full name of requester
- `email` (string, required): Email address
- `contact_number` (string, required): Contact number
- `attachment` (file, optional): Optional file attachment

**Response:** `200 OK`

```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "queued",
  "message": "Valuation job queued successfully"
}
```

**Error Responses:**

- `400 Bad Request`: Invalid valuation input or invalid property type
- `403 Forbidden`: Subscription limit exceeded or subscription not active
- `404 Not Found`: Subscription not found
- `503 Service Unavailable`: Valuation service unavailable

**Usage Example:**

```bash
curl -X POST "http://localhost:8000/create" \
  -H "Authorization: Bearer ACCESS_TOKEN_HERE" \
  -F "subscription_id=123e4567-e89b-12d3-a456-426614174000" \
  -F "country=United States" \
  -F "city_location=New York" \
  -F "full_address=123 Main St, New York, NY 10001" \
  -F "property_type=residential" \
  -F "land_area=1000 sq ft" \
  -F "built_up_area=800 sq ft" \
  -F "year_built=2020" \
  -F "purpose_of_valuation=Sale" \
  -F "full_name=John Doe" \
  -F "email=john@example.com" \
  -F "contact_number=+1234567890" \
  -F "attachment=@/path/to/file.pdf"
```

```python
import requests

files = {
    'attachment': open('/path/to/file.pdf', 'rb')
}
data = {
    'subscription_id': '123e4567-e89b-12d3-a456-426614174000',
    'country': 'United States',
    'city_location': 'New York',
    'full_address': '123 Main St, New York, NY 10001',
    'property_type': 'residential',
    'land_area': '1000 sq ft',
    'built_up_area': '800 sq ft',
    'year_built': '2020',
    'purpose_of_valuation': 'Sale',
    'full_name': 'John Doe',
    'email': 'john@example.com',
    'contact_number': '+1234567890'
}

headers = {"Authorization": f"Bearer {access_token}"}
response = requests.post(
    "http://localhost:8000/create",
    headers=headers,
    data=data,
    files=files
)
print(response.json())
```

**Notes:**
- Valuation is processed asynchronously via Celery
- Use the `job_id` to check status via `/jobs/{job_id}` endpoint
- Subscription usage is enforced (checks max_reports limit)
- Country code is automatically detected from user's country or IP address

---

### 2. List My Valuations

Get paginated list of user's valuations.

**Endpoint:** `GET /my-valuations`

**Authentication:** Required (Bearer token)

**Query Parameters:**
- `page` (integer, optional, default: 1): Page number (min: 1)
- `limit` (integer, optional, default: 10): Items per page (min: 1, max: 100)
- `search` (string, optional): Search in valuation_id, category, or country_code
- `category` (string, optional): Filter by property category
- `from_date` (datetime, optional): Filter valuations from this date
- `to_date` (datetime, optional): Filter valuations to this date

**Response:** `200 OK`

```json
{
  "data": [
    {
      "valuation_id": "VAL-2024-001",
      "category": "residential",
      "country_code": "US",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 25
  }
}
```

**Usage Example:**

```bash
curl "http://localhost:8000/my-valuations?page=1&limit=10&category=residential" \
  -H "Authorization: Bearer ACCESS_TOKEN_HERE"
```

```python
import requests

headers = {"Authorization": f"Bearer {access_token}"}
params = {
    "page": 1,
    "limit": 10,
    "category": "residential",
    "from_date": "2024-01-01T00:00:00Z",
    "to_date": "2024-01-31T23:59:59Z"
}
response = requests.get(
    "http://localhost:8000/my-valuations",
    headers=headers,
    params=params
)
print(response.json())
```

---

### 3. Get Valuation Details

Get detailed information about a specific valuation.

**Endpoint:** `GET /valuation/{valuation_id}`

**Authentication:** Required (Bearer token)

**Path Parameters:**
- `valuation_id` (string, required): Valuation ID

**Response:** `200 OK`

```json
{
  "valuation_id": "VAL-2024-001",
  "category": "residential",
  "country_code": "US",
  "user_fields": {
    "country": "United States",
    "city_location": "New York",
    "full_address": "123 Main St",
    "property_type": "residential",
    "land_area": "1000 sq ft"
  },
  "ai_response": {
    "estimated_value": "$500,000",
    "market_analysis": "..."
  },
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Error Responses:**

- `404 Not Found`: Valuation not found or doesn't belong to user

**Usage Example:**

```bash
curl "http://localhost:8000/valuation/VAL-2024-001" \
  -H "Authorization: Bearer ACCESS_TOKEN_HERE"
```

---

### 4. Download Valuation PDF

Download the PDF report for a valuation.

**Endpoint:** `GET /valuation/{valuation_id}/download`

**Authentication:** Required (Bearer token)

**Path Parameters:**
- `valuation_id` (string, required): Valuation ID

**Response:** `200 OK` (PDF file)

**Response Headers:**
- `Content-Type: application/pdf`
- `Content-Disposition: attachment; filename="VAL-2024-001.pdf"`

**Error Responses:**

- `404 Not Found`: Valuation not found or PDF not available

**Usage Example:**

```bash
curl "http://localhost:8000/valuation/VAL-2024-001/download" \
  -H "Authorization: Bearer ACCESS_TOKEN_HERE" \
  -o valuation_report.pdf
```

```python
import requests

headers = {"Authorization": f"Bearer {access_token}"}
response = requests.get(
    "http://localhost:8000/valuation/VAL-2024-001/download",
    headers=headers
)

with open('valuation_report.pdf', 'wb') as f:
    f.write(response.content)
```

---

### 5. Get Valuation Job Status

Get the status of an asynchronous valuation job.

**Endpoint:** `GET /jobs/{job_id}`

**Authentication:** Required (Bearer token)

**Path Parameters:**
- `job_id` (string, required): Job ID returned from create valuation endpoint

**Response:** `200 OK`

```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "completed",
  "valuation_id": "VAL-2024-001",
  "error": null
}
```

**Status Values:**
- `queued`: Job is waiting to be processed
- `processing`: Job is currently being processed
- `completed`: Job completed successfully
- `failed`: Job failed with error

**Error Responses:**

- `404 Not Found`: Job not found or doesn't belong to user
- `500 Internal Server Error`: Could not retrieve job status

**Usage Example:**

```bash
curl "http://localhost:8000/jobs/123e4567-e89b-12d3-a456-426614174000" \
  -H "Authorization: Bearer ACCESS_TOKEN_HERE"
```

**Notes:**
- Poll this endpoint to check when valuation is ready
- When status is "completed", use `valuation_id` to access the valuation

---

## Subscription APIs

### 1. List Subscription Plans

Get available subscription plans for user's country.

**Endpoint:** `GET /subscription/plans`

**Authentication:** Required (Bearer token)

**Response:** `200 OK`

```json
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "name": "PREMIUM",
    "country_code": "US",
    "price": 99.99,
    "currency": "USD",
    "max_reports": 10,
    "allowed_categories": ["residential", "commercial"],
    "is_active": true
  }
]
```

**Notes:**
- Plans are filtered by user's country (from IP or user profile)
- If no country-specific plans exist, returns USD plans with currency conversion
- Prices are automatically converted to user's currency if exchange rate is available

**Usage Example:**

```bash
curl "http://localhost:8000/subscription/plans" \
  -H "Authorization: Bearer ACCESS_TOKEN_HERE"
```

---

### 2. Get My Active Plans

Get user's currently active subscription plans.

**Endpoint:** `GET /subscription/my-plans`

**Authentication:** Required (Bearer token)

**Response:** `200 OK`

```json
[
  {
    "subscription_id": "123e4567-e89b-12d3-a456-426614174000",
    "plan_name": "PREMIUM",
    "country": "US",
    "price": 99.99,
    "currency": "USD",
    "max_reports": 10,
    "reports_used": 3,
    "remaining": 7,
    "start_date": "2024-01-01T00:00:00Z",
    "end_date": "2024-01-31T23:59:59Z"
  }
]
```

**Usage Example:**

```bash
curl "http://localhost:8000/subscription/my-plans" \
  -H "Authorization: Bearer ACCESS_TOKEN_HERE"
```

---

### 3. Get Subscription History

Get paginated history of user's subscriptions.

**Endpoint:** `GET /subscription/plan-history`

**Authentication:** Required (Bearer token)

**Query Parameters:**
- `page` (integer, optional, default: 1): Page number
- `limit` (integer, optional, default: 10): Items per page
- `search` (string, optional): Search in plan name
- `is_active` (boolean, optional): Filter by active status
- `from_date` (datetime, optional): Filter from date
- `to_date` (datetime, optional): Filter to date

**Response:** `200 OK`

```json
{
  "data": [
    {
      "subscription_id": "123e4567-e89b-12d3-a456-426614174000",
      "plan_name": "PREMIUM",
      "country": "US",
      "price": 99.99,
      "currency": "USD",
      "max_reports": 10,
      "reports_used": 3,
      "start_date": "2024-01-01T00:00:00Z",
      "end_date": "2024-01-31T23:59:59Z",
      "is_active": true,
      "expired": false,
      "purchased_on": "2024-01-01T00:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 5
  }
}
```

**Usage Example:**

```bash
curl "http://localhost:8000/subscription/plan-history?page=1&limit=10&is_active=true" \
  -H "Authorization: Bearer ACCESS_TOKEN_HERE"
```

---

### 4. Get Default Subscription

Get the default active subscription (highest price, most recent).

**Endpoint:** `GET /subscription/default`

**Authentication:** Required (Bearer token)

**Response:** `200 OK`

```json
{
  "subscription_id": "123e4567-e89b-12d3-a456-426614174000",
  "plan": "PREMIUM",
  "remaining": 7
}
```

**Error Responses:**

- `404 Not Found`: No active subscription

**Usage Example:**

```bash
curl "http://localhost:8000/subscription/default" \
  -H "Authorization: Bearer ACCESS_TOKEN_HERE"
```

---

### 5. Get Subscription Usage

Get usage details for a specific subscription.

**Endpoint:** `GET /subscription/{subscription_id}/usage`

**Authentication:** Required (Bearer token)

**Path Parameters:**
- `subscription_id` (UUID, required): Subscription ID

**Response:** `200 OK`

```json
{
  "subscription_id": "123e4567-e89b-12d3-a456-426614174000",
  "plan_name": "PREMIUM",
  "max_reports": 10,
  "reports_used": 3,
  "remaining": 7,
  "expires_at": "2024-01-31T23:59:59Z",
  "is_active": true
}
```

**Error Responses:**

- `404 Not Found`: Subscription not found

**Usage Example:**

```bash
curl "http://localhost:8000/subscription/123e4567-e89b-12d3-a456-426614174000/usage" \
  -H "Authorization: Bearer ACCESS_TOKEN_HERE"
```

---

### 6. Cancel Subscription

Cancel a subscription (will end at period end).

**Endpoint:** `POST /subscription/{subscription_id}/cancel`

**Authentication:** Required (Bearer token)

**Path Parameters:**
- `subscription_id` (UUID, required): Subscription ID

**Response:** `200 OK`

```json
{
  "message": "Subscription will cancel at period end",
  "ends_on": "2024-01-31T23:59:59Z"
}
```

**Error Responses:**

- `404 Not Found`: Active subscription not found

**Usage Example:**

```bash
curl -X POST "http://localhost:8000/subscription/123e4567-e89b-12d3-a456-426614174000/cancel" \
  -H "Authorization: Bearer ACCESS_TOKEN_HERE"
```

**Notes:**
- Sets `auto_renew` to false
- Subscription remains active until end_date

---

### 7. Renew Subscription

Renew a subscription by creating a new payment order.

**Endpoint:** `POST /subscription/{subscription_id}/renew`

**Authentication:** Required (Bearer token)

**Path Parameters:**
- `subscription_id` (UUID, required): Subscription ID

**Response:** `200 OK`

```json
{
  "order_id": "order_ABC123",
  "razorpay_key": "rzp_test_...",
  "amount": 9999,
  "currency": "USD",
  "subscription_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

**Error Responses:**

- `404 Not Found`: Subscription not found

**Usage Example:**

```bash
curl -X POST "http://localhost:8000/subscription/123e4567-e89b-12d3-a456-426614174000/renew" \
  -H "Authorization: Bearer ACCESS_TOKEN_HERE"
```

**Notes:**
- Creates a new payment order for the subscription's plan
- See Payment APIs for payment verification

---

## Payment APIs

### 1. Create Payment Order

Create a Razorpay payment order for a subscription plan.

**Endpoint:** `POST /payment/create-order/{plan_id}`

**Authentication:** Required (Bearer token)

**Path Parameters:**
- `plan_id` (UUID, required): Subscription plan ID

**Response:** `200 OK`

```json
{
  "order_id": "order_ABC123",
  "razorpay_key": "rzp_test_...",
  "amount": 9999,
  "currency": "USD",
  "subscription_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

**Error Responses:**

- `400 Bad Request`: Invalid payment request or currency not supported
- `404 Not Found`: Plan not found
- `502 Bad Gateway`: Payment gateway unavailable
- `500 Internal Server Error`: Unable to create payment order

**Usage Example:**

```bash
curl -X POST "http://localhost:8000/payment/create-order/123e4567-e89b-12d3-a456-426614174000" \
  -H "Authorization: Bearer ACCESS_TOKEN_HERE"
```

**Notes:**
- Amount is in smallest currency unit (e.g., cents for USD)
- Currency is automatically determined based on plan or user's country
- Removes any existing pending orders for the same plan
- Subscription is created with `is_active=false` and `payment_status=PENDING`

---

### 2. Verify Payment

Verify Razorpay payment and activate subscription.

**Endpoint:** `POST /payment/verify`

**Authentication:** Required (Bearer token)

**Request Body:**

```json
{
  "razorpay_order_id": "order_ABC123",
  "razorpay_payment_id": "pay_XYZ789",
  "razorpay_signature": "signature_hash_here"
}
```

**Response:** `200 OK`

```json
{
  "message": "Payment successful & subscription activated"
}
```

**Error Responses:**

- `400 Bad Request`: Invalid payment signature
- `404 Not Found`: Subscription not found
- `500 Internal Server Error`: Payment verification failed

**Usage Example:**

```bash
curl -X POST "http://localhost:8000/payment/verify" \
  -H "Authorization: Bearer ACCESS_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "razorpay_order_id": "order_ABC123",
    "razorpay_payment_id": "pay_XYZ789",
    "razorpay_signature": "signature_hash_here"
  }'
```

```javascript
// Frontend example (after Razorpay payment)
const response = await fetch('http://localhost:8000/payment/verify', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    razorpay_order_id: razorpayResponse.razorpay_order_id,
    razorpay_payment_id: razorpayResponse.razorpay_payment_id,
    razorpay_signature: razorpayResponse.razorpay_signature
  })
});
```

**Notes:**
- Verifies payment signature using Razorpay SDK
- Expires all existing active subscriptions for the user
- Activates the new subscription with 30-day validity
- Sets `payment_status=PAID` and `is_active=true`

---

## Feedback APIs

### 1. Create Feedback

Submit user feedback.

**Endpoint:** `POST /feedback`

**Authentication:** Required (Bearer token)

**Request Body:**

```json
{
  "type": "GENERAL",
  "subject": "Feature Request",
  "message": "I would like to see more property types",
  "rating": 4,
  "valuation_id": "VAL-2024-001",
  "subscription_id": 123
}
```

**Request Schema:**
- `type` (string, required): One of "GENERAL", "VALUATION", "PAYMENT", "SUBSCRIPTION"
- `subject` (string, required): Feedback subject
- `message` (string, required): Feedback message
- `rating` (integer, optional): Rating from 1 to 5
- `valuation_id` (string, optional): Related valuation ID
- `subscription_id` (integer, optional): Related subscription ID

**Response:** `200 OK`

```json
{
  "message": "Feedback submitted successfully"
}
```

**Error Responses:**

- `500 Internal Server Error`: Failed to submit feedback

**Usage Example:**

```bash
curl -X POST "http://localhost:8000/feedback" \
  -H "Authorization: Bearer ACCESS_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "GENERAL",
    "subject": "Feature Request",
    "message": "I would like to see more property types",
    "rating": 4
  }'
```

**Notes:**
- Sends notification email to admin
- Status is set to "OPEN" by default

---

### 2. Get My Feedback

Get paginated list of user's feedback.

**Endpoint:** `GET /feedback/my`

**Authentication:** Required (Bearer token)

**Query Parameters:**
- `page` (integer, optional, default: 1): Page number
- `limit` (integer, optional, default: 10): Items per page
- `search` (string, optional): Search in subject or message
- `status` (string, optional): Filter by status
- `type` (string, optional): Filter by type

**Response:** `200 OK`

```json
{
  "data": [
    {
      "id": 1,
      "type": "GENERAL",
      "subject": "Feature Request",
      "message": "I would like to see more property types",
      "rating": 4,
      "status": "OPEN",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 5
  }
}
```

**Usage Example:**

```bash
curl "http://localhost:8000/feedback/my?page=1&limit=10&status=OPEN" \
  -H "Authorization: Bearer ACCESS_TOKEN_HERE"
```

---

### 3. Get Feedback by ID

Get specific feedback details.

**Endpoint:** `GET /feedback/{feedback_id}`

**Authentication:** Required (Bearer token)

**Path Parameters:**
- `feedback_id` (UUID, required): Feedback ID

**Response:** `200 OK`

```json
{
  "id": 1,
  "type": "GENERAL",
  "subject": "Feature Request",
  "message": "I would like to see more property types",
  "rating": 4,
  "status": "OPEN",
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Error Responses:**

- `404 Not Found`: Feedback not found

**Usage Example:**

```bash
curl "http://localhost:8000/feedback/1" \
  -H "Authorization: Bearer ACCESS_TOKEN_HERE"
```

---

### 4. Update Feedback

Update user's own feedback (only if status is OPEN).

**Endpoint:** `PATCH /feedback/update/{feedback_id}`

**Authentication:** Required (Bearer token)

**Path Parameters:**
- `feedback_id` (UUID, required): Feedback ID

**Request Body:**

```json
{
  "subject": "Updated Subject",
  "message": "Updated message",
  "rating": 5
}
```

**Request Schema:**
- `subject` (string, optional, max: 255): Updated subject
- `message` (string, optional): Updated message
- `rating` (integer, optional): Updated rating (1-5)

**Response:** `200 OK`

```json
{
  "id": 1,
  "type": "GENERAL",
  "subject": "Updated Subject",
  "message": "Updated message",
  "rating": 5,
  "status": "OPEN",
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Error Responses:**

- `400 Bad Request`: Feedback can no longer be edited (status is not OPEN)
- `404 Not Found`: Feedback not found

**Usage Example:**

```bash
curl -X PATCH "http://localhost:8000/feedback/update/1" \
  -H "Authorization: Bearer ACCESS_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Updated Subject",
    "message": "Updated message"
  }'
```

---

### 5. Reply to Feedback

Add a user reply to feedback thread.

**Endpoint:** `POST /feedback/{feedback_id}/messages`

**Authentication:** Required (Bearer token)

**Path Parameters:**
- `feedback_id` (UUID, required): Feedback ID

**Request Body:**

```json
{
  "message": "Thank you for the update!"
}
```

**Response:** `200 OK`

```json
{
  "message": "Reply sent"
}
```

**Error Responses:**

- `404 Not Found`: Feedback not found

**Usage Example:**

```bash
curl -X POST "http://localhost:8000/feedback/1/messages" \
  -H "Authorization: Bearer ACCESS_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{"message": "Thank you for the update!"}'
```

---

## Admin Authentication APIs

### 1. Admin Login

Authenticate admin user.

**Endpoint:** `POST /admin/login`

**Authentication:** Not required

**Request Body:**

```json
{
  "email": "admin@example.com",
  "password": "AdminPassword123!"
}
```

**Response:** `200 OK`

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Error Responses:**

- `401 Unauthorized`: Invalid credentials
- `403 Forbidden`: Admin access denied or account disabled

**Usage Example:**

```bash
curl -X POST "http://localhost:8000/admin/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "AdminPassword123!"
  }'
```

**Notes:**
- User must have `is_superuser=true`
- User must be active
- Token includes role claim: `{"sub": "user_id", "role": "superuser"}`

---

### 2. Get Admin Profile

Get current admin user's profile.

**Endpoint:** `GET /admin/me`

**Authentication:** Required (Admin Bearer token)

**Response:** `200 OK`

```json
{
  "id": 1,
  "email": "admin@example.com",
  "username": "admin"
}
```

**Usage Example:**

```bash
curl "http://localhost:8000/admin/me" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN_HERE"
```

---

### 3. Admin Logout

Logout admin user (revoke all refresh tokens).

**Endpoint:** `POST /admin/logout`

**Authentication:** Required (Admin Bearer token)

**Response:** `200 OK`

```json
{
  "message": "Admin logged out successfully"
}
```

**Usage Example:**

```bash
curl -X POST "http://localhost:8000/admin/logout" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN_HERE"
```

---

### 4. Change Admin Password

Change admin user's password.

**Endpoint:** `POST /admin/change-password`

**Authentication:** Required (Admin Bearer token)

**Request Body:**

```json
{
  "old_password": "OldPassword123!",
  "new_password": "NewPassword456!",
  "confirm_password": "NewPassword456!"
}
```

**Response:** `200 OK`

```json
{
  "message": "Admin password changed successfully"
}
```

**Error Responses:**

- `400 Bad Request`: Passwords do not match
- `401 Unauthorized`: Old password is incorrect
- `500 Internal Server Error`: Error changing password

**Usage Example:**

```bash
curl -X POST "http://localhost:8000/admin/change-password" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "old_password": "OldPassword123!",
    "new_password": "NewPassword456!",
    "confirm_password": "NewPassword456!"
  }'
```

---

## Admin User Management APIs

### 1. List All Users

Get paginated list of all users with filtering options.

**Endpoint:** `GET /admin/users`

**Authentication:** Required (Admin Bearer token)

**Query Parameters:**
- `page` (integer, optional, default: 1): Page number
- `limit` (integer, optional, default: 10): Items per page
- `search` (string, optional): Search in username, email, or mobile_number
- `is_active` (boolean, optional): Filter by active status
- `is_email_verified` (boolean, optional): Filter by email verification status
- `is_superuser` (boolean, optional): Filter by superuser status
- `country_id` (integer, optional): Filter by country ID
- `verified_from` (datetime, optional): Email verified from date
- `verified_to` (datetime, optional): Email verified to date
- `verified_within_days` (integer, optional): Email verified within last N days (1-365)
- `sort_by` (string, optional, default: "id"): Sort field (id, email, username, email_verified_at)
- `order` (string, optional, default: "desc"): Sort order (asc, desc)

**Response:** `200 OK`

```json
{
  "data": [
    {
      "id": 1,
      "email": "user@example.com",
      "username": "johndoe",
      "mobile_number": "+1234567890",
      "is_active": true,
      "is_email_verified": true,
      "is_superuser": false
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 100
  }
}
```

**Usage Example:**

```bash
curl "http://localhost:8000/admin/users?page=1&limit=10&is_active=true&sort_by=email&order=asc" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN_HERE"
```

---

### 2. Get User Details

Get detailed information about a specific user.

**Endpoint:** `GET /admin/users/{user_id}`

**Authentication:** Required (Admin Bearer token)

**Path Parameters:**
- `user_id` (UUID, required): User ID

**Response:** `200 OK`

```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "johndoe",
  "mobile_number": "+1234567890",
  "is_active": true,
  "is_email_verified": true,
  "is_superuser": false
}
```

**Error Responses:**

- `404 Not Found`: User not found

**Usage Example:**

```bash
curl "http://localhost:8000/admin/users/123e4567-e89b-12d3-a456-426614174000" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN_HERE"
```

---

### 3. Toggle User Active Status

Enable or disable a user account.

**Endpoint:** `PATCH /admin/users/{user_id}/toggle-active`

**Authentication:** Required (Admin Bearer token)

**Path Parameters:**
- `user_id` (UUID, required): User ID

**Response:** `200 OK`

```json
{
  "message": "User status updated",
  "is_active": false
}
```

**Error Responses:**

- `404 Not Found`: User not found
- `500 Internal Server Error`: Update failed

**Usage Example:**

```bash
curl -X PATCH "http://localhost:8000/admin/users/123e4567-e89b-12d3-a456-426614174000/toggle-active" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN_HERE"
```

**Notes:**
- If user is deactivated, all refresh tokens are revoked
- User will be logged out from all devices

---

### 4. Force Logout User

Force logout user from all devices.

**Endpoint:** `POST /admin/users/{user_id}/logout`

**Authentication:** Required (Admin Bearer token)

**Path Parameters:**
- `user_id` (UUID, required): User ID

**Response:** `200 OK`

```json
{
  "message": "User logged out from all sessions"
}
```

**Error Responses:**

- `404 Not Found`: User not found

**Usage Example:**

```bash
curl -X POST "http://localhost:8000/admin/users/123e4567-e89b-12d3-a456-426614174000/logout" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN_HERE"
```

**Notes:**
- Revokes all refresh tokens for the user

---

### 5. Manually Verify User Email

Manually verify a user's email address.

**Endpoint:** `POST /admin/users/{user_id}/verify-email`

**Authentication:** Required (Admin Bearer token)

**Path Parameters:**
- `user_id` (UUID, required): User ID

**Response:** `200 OK`

```json
{
  "message": "User email verified"
}
```

**Error Responses:**

- `404 Not Found`: User not found
- `500 Internal Server Error`: Email verification failed

**Usage Example:**

```bash
curl -X POST "http://localhost:8000/admin/users/123e4567-e89b-12d3-a456-426614174000/verify-email" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN_HERE"
```

**Notes:**
- Sets `is_email_verified=true` and `email_verified_at=now()`
- Returns success message if already verified

---

### 6. Reset User Password

Reset a user's password (admin action).

**Endpoint:** `POST /admin/users/{user_id}/reset-password`

**Authentication:** Required (Admin Bearer token)

**Path Parameters:**
- `user_id` (UUID, required): User ID

**Request Body:**

```json
{
  "new_password": "NewPassword123!",
  "confirm_password": "NewPassword123!"
}
```

**Response:** `200 OK`

```json
{
  "message": "User password reset successfully"
}
```

**Error Responses:**

- `400 Bad Request`: Passwords do not match
- `404 Not Found`: User not found
- `500 Internal Server Error`: Password reset failed

**Usage Example:**

```bash
curl -X POST "http://localhost:8000/admin/users/123e4567-e89b-12d3-a456-426614174000/reset-password" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "new_password": "NewPassword123!",
    "confirm_password": "NewPassword123!"
  }'
```

**Notes:**
- Revokes all refresh tokens after password reset
- User must login again with new password

---

## Admin Subscription Plan APIs

### 1. List Subscription Plans

Get paginated list of all subscription plans with filtering.

**Endpoint:** `GET /admin/subscription-plans`

**Authentication:** Required (Admin Bearer token)

**Query Parameters:**
- `page` (integer, optional, default: 1): Page number
- `limit` (integer, optional, default: 10): Items per page
- `search` (string, optional): Search in plan name
- `country_code` (string, optional): Filter by country code
- `is_active` (boolean, optional): Filter by active status
- `min_price` (integer, optional): Minimum price filter
- `max_price` (integer, optional): Maximum price filter
- `currency` (string, optional): Filter by currency
- `min_reports` (integer, optional): Minimum max_reports filter
- `max_reports` (integer, optional): Maximum max_reports filter
- `category` (string, optional): Filter by allowed category
- `created_from` (datetime, optional): Created from date
- `created_to` (datetime, optional): Created to date

**Response:** `200 OK`

```json
{
  "data": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "name": "PREMIUM",
      "country_code": "US",
      "price": 99.99,
      "currency": "USD",
      "max_reports": 10,
      "allowed_categories": ["residential", "commercial"],
      "is_active": true
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 20
  }
}
```

**Usage Example:**

```bash
curl "http://localhost:8000/admin/subscription-plans?country_code=US&is_active=true" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN_HERE"
```

---

### 2. Get Subscription Plan Details

Get detailed information about a specific subscription plan.

**Endpoint:** `GET /admin/subscription-plans/{plan_id}`

**Authentication:** Required (Admin Bearer token)

**Path Parameters:**
- `plan_id` (UUID, required): Plan ID

**Response:** `200 OK`

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "PREMIUM",
  "country_code": "US",
  "price": 99.99,
  "currency": "USD",
  "max_reports": 10,
  "allowed_categories": ["residential", "commercial"],
  "is_active": true
}
```

**Error Responses:**

- `404 Not Found`: Subscription plan not found

**Usage Example:**

```bash
curl "http://localhost:8000/admin/subscription-plans/123e4567-e89b-12d3-a456-426614174000" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN_HERE"
```

---

### 3. Create Subscription Plan

Create a new subscription plan.

**Endpoint:** `POST /admin/subscription-plans`

**Authentication:** Required (Admin Bearer token)

**Request Body:**

```json
{
  "name": "PREMIUM",
  "country_code": "US",
  "price": 99.99,
  "currency": "USD",
  "max_reports": 10,
  "allowed_categories": ["residential", "commercial"]
}
```

**Request Schema:**
- `name` (string, required): Plan name (will be converted to uppercase)
- `country_code` (string, required): Country code (will be converted to uppercase)
- `price` (integer, required): Price in smallest currency unit
- `currency` (string, required): Currency code (will be converted to uppercase)
- `max_reports` (integer, optional): Maximum number of reports (null for unlimited)
- `allowed_categories` (array of strings, required): Allowed property categories

**Response:** `200 OK`

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "PREMIUM",
  "country_code": "US",
  "price": 99.99,
  "currency": "USD",
  "max_reports": 10,
  "allowed_categories": ["residential", "commercial"],
  "is_active": true
}
```

**Error Responses:**

- `500 Internal Server Error`: Creation failed

**Usage Example:**

```bash
curl -X POST "http://localhost:8000/admin/subscription-plans" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "PREMIUM",
    "country_code": "US",
    "price": 99.99,
    "currency": "USD",
    "max_reports": 10,
    "allowed_categories": ["residential", "commercial"]
  }'
```

**Notes:**
- Plan is created with `is_active=true` by default

---

### 4. Update Subscription Plan

Update an existing subscription plan.

**Endpoint:** `PUT /admin/subscription-plans/{plan_id}`

**Authentication:** Required (Admin Bearer token)

**Path Parameters:**
- `plan_id` (UUID, required): Plan ID

**Request Body:**

```json
{
  "name": "PREMIUM_PLUS",
  "price": 149.99,
  "max_reports": 20,
  "allowed_categories": ["residential", "commercial", "industrial"]
}
```

**Request Schema:**
- All fields are optional (only provided fields will be updated)

**Response:** `200 OK`

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "PREMIUM_PLUS",
  "country_code": "US",
  "price": 149.99,
  "currency": "USD",
  "max_reports": 20,
  "allowed_categories": ["residential", "commercial", "industrial"],
  "is_active": true
}
```

**Error Responses:**

- `404 Not Found`: Subscription plan not found
- `500 Internal Server Error`: Update failed

**Usage Example:**

```bash
curl -X PUT "http://localhost:8000/admin/subscription-plans/123e4567-e89b-12d3-a456-426614174000" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "price": 149.99,
    "max_reports": 20
  }'
```

---

### 5. Toggle Subscription Plan Status

Enable or disable a subscription plan.

**Endpoint:** `PATCH /admin/subscription-plans/{plan_id}/toggle`

**Authentication:** Required (Admin Bearer token)

**Path Parameters:**
- `plan_id` (UUID, required): Plan ID

**Response:** `200 OK`

```json
{
  "message": "Plan status updated",
  "is_active": false
}
```

**Error Responses:**

- `404 Not Found`: Subscription plan not found
- `500 Internal Server Error`: Update failed

**Usage Example:**

```bash
curl -X PATCH "http://localhost:8000/admin/subscription-plans/123e4567-e89b-12d3-a456-426614174000/toggle" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN_HERE"
```

**Notes:**
- Toggles `is_active` status
- Inactive plans won't be shown to users

---

## Admin User Subscription APIs

### 1. List All User Subscriptions

Get paginated list of all user subscriptions with filtering.

**Endpoint:** `GET /admin/user-subscriptions`

**Authentication:** Required (Admin Bearer token)

**Query Parameters:**
- `page` (integer, optional, default: 1): Page number
- `limit` (integer, optional, default: 10): Items per page
- `search` (string, optional): Search in plan name
- `user_id` (integer, optional): Filter by user ID
- `plan_id` (integer, optional): Filter by plan ID
- `is_active` (boolean, optional): Filter by active status
- `is_expired` (boolean, optional): Filter by expired status
- `payment_status` (string, optional): Filter by payment status
- `pricing_country_code` (string, optional): Filter by pricing country
- `ip_country_code` (string, optional): Filter by IP country
- `payment_country_code` (string, optional): Filter by payment country
- `plan_country_code` (string, optional): Filter by plan country
- `start_from` (datetime, optional): Start date from
- `start_to` (datetime, optional): Start date to
- `end_from` (datetime, optional): End date from
- `end_to` (datetime, optional): End date to
- `purchased_within_days` (integer, optional): Purchased within last N days (1-365)

**Response:** `200 OK`

```json
{
  "data": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "user_id": 1,
      "plan_id": 2,
      "plan_name": "PREMIUM",
      "pricing_country_code": "US",
      "start_date": "2024-01-01T00:00:00Z",
      "end_date": "2024-01-31T23:59:59Z",
      "reports_used": 3,
      "is_active": true
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 50
  }
}
```

**Usage Example:**

```bash
curl "http://localhost:8000/admin/user-subscriptions?is_active=true&payment_status=PAID" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN_HERE"
```

---

### 2. Get User's Subscriptions

Get paginated list of subscriptions for a specific user.

**Endpoint:** `GET /admin/users/{user_id}/subscriptions`

**Authentication:** Required (Admin Bearer token)

**Path Parameters:**
- `user_id` (UUID, required): User ID

**Query Parameters:**
- `page` (integer, optional, default: 1): Page number
- `limit` (integer, optional, default: 10): Items per page
- `search` (string, optional): Search in plan name
- `payment_status` (string, optional): Filter by payment status
- `is_active` (boolean, optional): Filter by active status
- `country_code` (string, optional): Filter by pricing country code
- `start_from` (datetime, optional): Start date from
- `start_to` (datetime, optional): Start date to

**Response:** `200 OK`

```json
{
  "data": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "user_id": 1,
      "plan_id": 2,
      "plan_name": "PREMIUM",
      "pricing_country_code": "US",
      "start_date": "2024-01-01T00:00:00Z",
      "end_date": "2024-01-31T23:59:59Z",
      "reports_used": 3,
      "is_active": true
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 5
  }
}
```

**Error Responses:**

- `404 Not Found`: User not found

**Usage Example:**

```bash
curl "http://localhost:8000/admin/users/123e4567-e89b-12d3-a456-426614174000/subscriptions" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN_HERE"
```

---

### 3. Assign Subscription to User

Manually assign a subscription to a user (admin action).

**Endpoint:** `POST /admin/users/{user_id}/assign-subscription`

**Authentication:** Required (Admin Bearer token)

**Path Parameters:**
- `user_id` (UUID, required): User ID

**Request Body:**

```json
{
  "plan_id": "123e4567-e89b-12d3-a456-426614174000",
  "duration_days": 30,
  "pricing_country_code": "US"
}
```

**Request Schema:**
- `plan_id` (integer, required): Subscription plan ID
- `duration_days` (integer, optional, default: 30): Subscription duration in days
- `pricing_country_code` (string, optional): Pricing country code (defaults to plan's country_code)

**Response:** `200 OK`

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "user_id": 1,
  "plan_id": 2,
  "plan_name": "PREMIUM",
  "pricing_country_code": "US",
  "start_date": "2024-01-15T10:30:00Z",
  "end_date": "2024-02-14T10:30:00Z",
  "reports_used": 0,
  "is_active": true
}
```

**Error Responses:**

- `404 Not Found`: User or plan not found
- `500 Internal Server Error`: Subscription assignment failed

**Usage Example:**

```bash
curl -X POST "http://localhost:8000/admin/users/123e4567-e89b-12d3-a456-426614174000/assign-subscription" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "plan_id": 2,
    "duration_days": 30,
    "pricing_country_code": "US"
  }'
```

**Notes:**
- Subscription is created with `is_active=true`
- Plan must be active
- Start date is set to current time

---

### 4. Update User Subscription

Update a user subscription (extend, reset usage, deactivate).

**Endpoint:** `PATCH /admin/user-subscriptions/{subscription_id}`

**Authentication:** Required (Admin Bearer token)

**Path Parameters:**
- `subscription_id` (UUID, required): Subscription ID

**Request Body:**

```json
{
  "extend_days": 30,
  "reset_reports_used": true,
  "deactivate": false
}
```

**Request Schema:**
- `extend_days` (integer, optional): Number of days to extend subscription
- `reset_reports_used` (boolean, optional): Reset reports_used to 0
- `deactivate` (boolean, optional): Deactivate subscription

**Response:** `200 OK`

```json
{
  "message": "Subscription updated successfully"
}
```

**Error Responses:**

- `404 Not Found`: Subscription not found
- `500 Internal Server Error`: Update failed

**Usage Example:**

```bash
curl -X PATCH "http://localhost:8000/admin/user-subscriptions/123e4567-e89b-12d3-a456-426614174000" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "extend_days": 30,
    "reset_reports_used": true
  }'
```

---

### 5. Cancel User Subscription

Cancel a user subscription (admin action).

**Endpoint:** `POST /admin/user-subscriptions/{subscription_id}/cancel`

**Authentication:** Required (Admin Bearer token)

**Path Parameters:**
- `subscription_id` (UUID, required): Subscription ID

**Response:** `200 OK`

```json
{
  "message": "Subscription cancelled"
}
```

**Error Responses:**

- `404 Not Found`: Subscription not found
- `500 Internal Server Error`: Cancel failed

**Usage Example:**

```bash
curl -X POST "http://localhost:8000/admin/user-subscriptions/123e4567-e89b-12d3-a456-426614174000/cancel" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN_HERE"
```

**Notes:**
- Sets `is_active=false` and `end_date=now()`

---

## Admin Valuation APIs

### 1. List All Valuations

Get paginated list of all valuations with filtering.

**Endpoint:** `GET /admin/valuations`

**Authentication:** Required (Admin Bearer token)

**Query Parameters:**
- `page` (integer, optional, default: 1): Page number
- `limit` (integer, optional, default: 10): Items per page
- `search` (string, optional): Search in valuation_id, category, or country_code
- `user_id` (integer, optional): Filter by user ID
- `country_code` (string, optional): Filter by country code
- `category` (string, optional): Filter by property category
- `from_date` (datetime, optional): Filter from date
- `to_date` (datetime, optional): Filter to date
- `sort_by` (string, optional, default: "created_at"): Sort field (created_at, valuation_id, category, country_code)
- `order` (string, optional, default: "desc"): Sort order (asc, desc)

**Response:** `200 OK`

```json
{
  "data": [
    {
      "id": 1,
      "valuation_id": "VAL-2024-001",
      "user_id": 1,
      "category": "residential",
      "country_code": "US",
      "subscription_id": 2,
      "created_at": "2024-01-15T10:30:00Z",
      "pdf_path": "/path/to/report.pdf"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 100
  }
}
```

**Usage Example:**

```bash
curl "http://localhost:8000/admin/valuations?page=1&limit=10&category=residential&sort_by=created_at&order=desc" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN_HERE"
```

---

### 2. Get Valuation Details

Get detailed information about a specific valuation.

**Endpoint:** `GET /admin/valuations/{valuation_id}`

**Authentication:** Required (Admin Bearer token)

**Path Parameters:**
- `valuation_id` (string, required): Valuation ID

**Response:** `200 OK`

```json
{
  "id": 1,
  "valuation_id": "VAL-2024-001",
  "user_id": 1,
  "category": "residential",
  "country_code": "US",
  "subscription_id": 2,
  "created_at": "2024-01-15T10:30:00Z",
  "pdf_path": "/path/to/report.pdf",
  "user_fields": {
    "country": "United States",
    "city_location": "New York",
    "full_address": "123 Main St",
    "property_type": "residential"
  },
  "ai_response": {
    "estimated_value": "$500,000",
    "market_analysis": "..."
  },
  "report_context": {
    "property_identification": {
      "valuation_id": "VAL-2024-001"
    }
  }
}
```

**Error Responses:**

- `404 Not Found`: Valuation not found

**Usage Example:**

```bash
curl "http://localhost:8000/admin/valuations/VAL-2024-001" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN_HERE"
```

---

### 3. Get User's Valuations

Get paginated list of valuations for a specific user.

**Endpoint:** `GET /admin/users/{user_id}/valuations`

**Authentication:** Required (Admin Bearer token)

**Path Parameters:**
- `user_id` (UUID, required): User ID

**Query Parameters:**
- `page` (integer, optional, default: 1): Page number
- `limit` (integer, optional, default: 10): Items per page
- `search` (string, optional): Search in valuation_id

**Response:** `200 OK`

```json
{
  "data": [
    {
      "id": 1,
      "valuation_id": "VAL-2024-001",
      "user_id": 1,
      "category": "residential",
      "country_code": "US",
      "subscription_id": 2,
      "created_at": "2024-01-15T10:30:00Z",
      "pdf_path": "/path/to/report.pdf"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 25
  }
}
```

**Error Responses:**

- `404 Not Found`: User not found

**Usage Example:**

```bash
curl "http://localhost:8000/admin/users/123e4567-e89b-12d3-a456-426614174000/valuations" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN_HERE"
```

---

### 4. Delete Valuation

Delete a valuation (admin action).

**Endpoint:** `DELETE /admin/valuations/{valuation_id}/delete`

**Authentication:** Required (Admin Bearer token)

**Path Parameters:**
- `valuation_id` (string, required): Valuation ID

**Response:** `200 OK`

```json
{
  "message": "Valuation deleted successfully"
}
```

**Error Responses:**

- `404 Not Found`: Valuation not found
- `500 Internal Server Error`: Deletion failed

**Usage Example:**

```bash
curl -X DELETE "http://localhost:8000/admin/valuations/VAL-2024-001/delete" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN_HERE"
```

**Notes:**
- Permanently deletes the valuation record
- PDF file is not automatically deleted (may need manual cleanup)

---

## Admin Dashboard APIs

### 1. Dashboard Overview

Get overview statistics for admin dashboard.

**Endpoint:** `GET /admin/dashboard/overview`

**Authentication:** Required (Admin Bearer token)

**Response:** `200 OK`

```json
{
  "users": {
    "total": 1000,
    "active": 950
  },
  "subscriptions": {
    "total": 500,
    "active": 450
  },
  "valuations": {
    "total": 2500
  }
}
```

**Usage Example:**

```bash
curl "http://localhost:8000/admin/dashboard/overview" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN_HERE"
```

---

### 2. User Statistics

Get user-related statistics.

**Endpoint:** `GET /admin/dashboard/users`

**Authentication:** Required (Admin Bearer token)

**Response:** `200 OK`

```json
{
  "email_verified": 900,
  "email_unverified": 100,
  "inactive_users": 50,
  "new_users_last_30_days": 150
}
```

**Usage Example:**

```bash
curl "http://localhost:8000/admin/dashboard/users" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN_HERE"
```

---

### 3. Subscription Breakdown

Get subscription statistics broken down by country and plan.

**Endpoint:** `GET /admin/dashboard/subscriptions`

**Authentication:** Required (Admin Bearer token)

**Response:** `200 OK`

```json
[
  {
    "country": "US",
    "plan": "PREMIUM",
    "currency": "USD",
    "price": 99.99,
    "subscriptions": {
      "total": 200,
      "active": 180
    },
    "revenue": {
      "total": 19998.0,
      "active": 17998.2
    }
  }
]
```

**Usage Example:**

```bash
curl "http://localhost:8000/admin/dashboard/subscriptions" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN_HERE"
```

---

### 4. Valuation Statistics

Get valuation-related statistics.

**Endpoint:** `GET /admin/dashboard/valuations`

**Authentication:** Required (Admin Bearer token)

**Response:** `200 OK`

```json
{
  "by_category": [
    {
      "category": "residential",
      "count": 1500
    },
    {
      "category": "commercial",
      "count": 800
    },
    {
      "category": "land",
      "count": 200
    }
  ],
  "last_30_days": 250
}
```

**Usage Example:**

```bash
curl "http://localhost:8000/admin/dashboard/valuations" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN_HERE"
```

---

### 5. Country-wise Statistics

Get statistics broken down by country.

**Endpoint:** `GET /admin/dashboard/countries`

**Authentication:** Required (Admin Bearer token)

**Response:** `200 OK`

```json
{
  "subscriptions": [
    {
      "country": "US",
      "count": 300
    },
    {
      "country": "IN",
      "count": 200
    }
  ],
  "valuations": [
    {
      "country": "US",
      "count": 1500
    },
    {
      "country": "IN",
      "count": 1000
    }
  ]
}
```

**Usage Example:**

```bash
curl "http://localhost:8000/admin/dashboard/countries" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN_HERE"
```

---

### 6. Feedback Statistics

Get feedback-related statistics.

**Endpoint:** `GET /admin/dashboard/feedback`

**Authentication:** Required (Admin Bearer token)

**Response:** `200 OK`

```json
{
  "total_feedback": 150,
  "open_feedback": 25,
  "avg_rating": 4.2
}
```

**Usage Example:**

```bash
curl "http://localhost:8000/admin/dashboard/feedback" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN_HERE"
```

---

## Admin Feedback APIs

### 1. List All Feedback

Get paginated list of all feedback with filtering.

**Endpoint:** `GET /admin/feedback`

**Authentication:** Required (Admin Bearer token)

**Query Parameters:**
- `page` (integer, optional, default: 1): Page number
- `limit` (integer, optional, default: 10): Items per page
- `search` (string, optional): Search in subject, message, or valuation_id
- `user_id` (integer, optional): Filter by user ID
- `status` (string, optional): Filter by status (OPEN, IN_PROGRESS, RESOLVED, CLOSED)
- `type` (string, optional): Filter by type (GENERAL, VALUATION, PAYMENT, SUBSCRIPTION)
- `rating` (integer, optional): Filter by rating (1-5)
- `valuation_id` (string, optional): Filter by valuation ID
- `subscription_id` (integer, optional): Filter by subscription ID

**Response:** `200 OK`

```json
{
  "data": [
    {
      "id": 1,
      "type": "GENERAL",
      "subject": "Feature Request",
      "message": "I would like to see more property types",
      "rating": 4,
      "status": "OPEN",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 50
  }
}
```

**Usage Example:**

```bash
curl "http://localhost:8000/admin/feedback?status=OPEN&type=GENERAL" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN_HERE"
```

---

### 2. Get Feedback Details

Get detailed information about a specific feedback.

**Endpoint:** `GET /admin/feedback/{feedback_id}`

**Authentication:** Required (Admin Bearer token)

**Path Parameters:**
- `feedback_id` (integer, required): Feedback ID

**Response:** `200 OK`

```json
{
  "id": 1,
  "type": "GENERAL",
  "subject": "Feature Request",
  "message": "I would like to see more property types",
  "rating": 4,
  "status": "OPEN",
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Error Responses:**

- `404 Not Found`: Feedback not found

**Usage Example:**

```bash
curl "http://localhost:8000/admin/feedback/1" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN_HERE"
```

---

### 3. Admin Action on Feedback

Perform admin action on feedback (reply, update status, add note).

**Endpoint:** `POST /admin/feedback/{feedback_id}/action`

**Authentication:** Required (Admin Bearer token)

**Path Parameters:**
- `feedback_id` (integer, required): Feedback ID

**Request Body:**

```json
{
  "status": "IN_PROGRESS",
  "reply": "Thank you for your feedback. We will consider this feature.",
  "notify_user": true,
  "admin_note": "High priority feature request"
}
```

**Request Schema:**
- `status` (string, optional): New status (OPEN, IN_PROGRESS, RESOLVED, CLOSED)
- `reply` (string, optional): Admin reply message
- `notify_user` (boolean, optional, default: false): Send email notification to user
- `admin_note` (string, optional): Internal admin note

**Response:** `200 OK`

```json
{
  "message": "Feedback updated successfully",
  "email_sent": true
}
```

**Error Responses:**

- `404 Not Found`: Feedback not found

**Usage Example:**

```bash
curl -X POST "http://localhost:8000/admin/feedback/1/action" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "IN_PROGRESS",
    "reply": "Thank you for your feedback.",
    "notify_user": true
  }'
```

**Notes:**
- If reply is provided and status is not specified, status is set to "IN_PROGRESS"
- Reply is stored as a FeedbackMessage with sender="ADMIN"
- Email notification is sent if `notify_user=true`

---

### 4. Delete Feedback

Delete a feedback (admin action).

**Endpoint:** `DELETE /admin/feedback/{feedback_id}`

**Authentication:** Required (Admin Bearer token)

**Path Parameters:**
- `feedback_id` (integer, required): Feedback ID

**Response:** `200 OK`

```json
{
  "message": "Feedback deleted successfully"
}
```

**Error Responses:**

- `404 Not Found`: Feedback not found

**Usage Example:**

```bash
curl -X DELETE "http://localhost:8000/admin/feedback/1" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN_HERE"
```

---

## Error Handling

### Standard Error Response Format

All error responses follow this format:

```json
{
  "detail": "Error message description"
}
```

### Common HTTP Status Codes

- `200 OK`: Request successful
- `400 Bad Request`: Invalid request parameters or validation error
- `401 Unauthorized`: Authentication required or invalid token
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error
- `502 Bad Gateway`: External service unavailable (e.g., payment gateway)
- `503 Service Unavailable`: Service temporarily unavailable

### Authentication Errors

- `401 Unauthorized`: Missing or invalid access token
- `403 Forbidden`: Email not verified or user inactive
- `403 Forbidden`: Superuser access required (for admin endpoints)

---

## Rate Limiting

Currently, the API does not implement rate limiting. However, it's recommended to:
- Implement rate limiting in production
- Use appropriate request throttling
- Monitor API usage patterns

---

## Pagination

Most list endpoints support pagination with the following parameters:

- `page` (integer, default: 1): Page number (minimum: 1)
- `limit` (integer, default: 10): Items per page (minimum: 1, maximum: 100)

**Response Format:**

```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 100
  }
}
```

---

## Date Formats

All date/time fields use ISO 8601 format:

- Format: `YYYY-MM-DDTHH:MM:SSZ` or `YYYY-MM-DDTHH:MM:SS+00:00`
- Example: `2024-01-15T10:30:00Z`

---

## UUID Format

All UUID fields use standard UUID v4 format:

- Format: `xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx`
- Example: `123e4567-e89b-12d3-a456-426614174000`

---

## Notes

1. **Base URL**: Replace `http://localhost:8000` with your production URL
2. **Authentication**: Always include the `Authorization: Bearer <token>` header for protected endpoints
3. **Content-Type**: Use `application/json` for JSON requests, `multipart/form-data` for file uploads
4. **Token Expiration**: Access tokens expire; use refresh token endpoint to obtain new tokens
5. **Email Verification**: Users must verify their email before accessing protected endpoints
6. **Subscription Limits**: Valuation creation enforces subscription limits (max_reports)
7. **Country Detection**: Country is automatically detected from user profile or IP address
8. **Currency Conversion**: Subscription plans are automatically converted to user's currency when available

---

## Support

For API support or questions, please contact the development team or refer to the project repository.

---

*Last Updated: January 2024*
