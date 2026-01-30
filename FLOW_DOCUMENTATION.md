# Desktop Valuation API - Flow Documentation

## Table of Contents

1. [Overview](#overview)
2. [User Flows](#user-flows)
   - [User Registration Flow](#1-user-registration-flow)
   - [User Login Flow](#2-user-login-flow)
   - [Subscription Purchase Flow](#3-subscription-purchase-flow)
   - [Create Valuation Request Flow](#4-create-valuation-request-flow)
   - [View and Download Valuation Flow](#5-view-and-download-valuation-flow)
   - [Profile Management Flow](#6-profile-management-flow)
   - [Password Reset Flow](#7-password-reset-flow)
   - [Feedback Submission Flow](#8-feedback-submission-flow)
3. [Admin Flows](#admin-flows)
   - [Admin Login Flow](#1-admin-login-flow)
   - [User Management Flow](#2-user-management-flow)
   - [Subscription Plan Management Flow](#3-subscription-plan-management-flow)
   - [User Subscription Management Flow](#4-user-subscription-management-flow)
   - [Valuation Management Flow](#5-valuation-management-flow)
   - [Feedback Management Flow](#6-feedback-management-flow)
   - [Dashboard Overview Flow](#7-dashboard-overview-flow)
4. [System Background Processes](#system-background-processes)
   - [Valuation Processing Flow](#valuation-processing-flow)
   - [Subscription Expiry Flow](#subscription-expiry-flow)

---

## Overview

This document describes the complete workflows for both users and administrators in the Desktop Valuation API system. Each flow includes step-by-step processes, decision points, API calls, and system behaviors.

---

## User Flows

### 1. User Registration Flow

**Objective:** Register a new user account and verify email address.

**Flow Steps:**

1. **User Initiates Registration**
   - User provides: email, username, mobile_number, password
   - API Endpoint: `POST /register`

2. **System Validates Input**
   - Checks if email already exists
   - Checks if mobile number already exists
   - Validates email format
   - Validates password strength

3. **System Processes Registration**
   - Extracts country code from mobile number dial code
   - Creates or retrieves country record
   - Creates user account with hashed password
   - Sets `is_email_verified = false`
   - Sets `is_active = true`

4. **System Assigns Free Subscription** (if available)
   - Searches for FREE plan matching user's country
   - If found, creates UserSubscription with:
     - `start_date = now()`
     - `end_date = now() + 365 days`
     - `is_active = true`

5. **System Generates Verification Token**
   - Creates EmailVerificationToken with:
     - `token_hash` (hashed random token)
     - `expires_at = now() + 30 minutes`
     - `used = false`

6. **System Sends Verification Email**
   - Email contains verification link: `{BASE_URL}/verify-email?token={raw_token}`
   - If email sending fails, registration still succeeds (logged as warning)

7. **Response to User**
   - Returns: `{"message": "Registration successful. Please verify your email."}`

8. **User Verifies Email**
   - User clicks link in email
   - API Endpoint: `GET /verify-email?token={token}`
   - System validates token (not used, not expired)
   - System updates user:
     - `is_email_verified = true`
     - `email_verified_at = now()`
   - Marks token as used

**Decision Points:**
- ❌ Email already exists → `400 Bad Request`
- ❌ Mobile number already exists → `400 Bad Request`
- ❌ Invalid email format → Validation error
- ❌ Database error → `500 Internal Server Error`
- ❌ Invalid/expired token → `400 Bad Request`

**Related Endpoints:**
- `POST /register`
- `GET /verify-email`
- `POST /resend-verification`

---

### 2. User Login Flow

**Objective:** Authenticate user and obtain access tokens.

**Flow Steps:**

1. **User Initiates Login**
   - User provides: email, password
   - API Endpoint: `POST /login`

2. **System Validates Credentials**
   - Retrieves user by email
   - Verifies password hash
   - Checks if user exists

3. **System Checks User Status**
   - ✅ `is_email_verified = true` (required)
   - ✅ `is_active = true` (required)

4. **System Generates Tokens**
   - Creates access token (JWT) with payload: `{"sub": user_id, "type": "access"}`
   - Creates refresh token (JWT) with payload: `{"sub": user_id, "type": "refresh"}`
   - Access token expires in 15 minutes - 1 hour (configurable)
   - Refresh token expires in 7 days

5. **System Stores Refresh Token**
   - Creates RefreshToken record with:
     - `token_hash` (hashed refresh token)
     - `user_id`
     - `expires_at = now() + 7 days`
     - `is_revoked = false`

6. **Response to User**
   - Returns: `{"access_token": "...", "refresh_token": "..."}`

**Decision Points:**
- ❌ User not found → `401 Unauthorized`
- ❌ Invalid password → `401 Unauthorized`
- ❌ Email not verified → `403 Forbidden`
- ❌ User inactive → `401 Unauthorized`

**Token Usage:**
- Access token: Include in `Authorization: Bearer {access_token}` header for protected endpoints
- Refresh token: Use when access token expires to get new tokens

**Related Endpoints:**
- `POST /login`
- `POST /refresh`
- `POST /logout`

---

### 3. Subscription Purchase Flow

**Objective:** Purchase a subscription plan and activate it.

**Flow Steps:**

1. **User Views Available Plans**
   - API Endpoint: `GET /subscription/plans`
   - System determines pricing country from:
     - IP address country (if available)
     - User's registered country
   - Returns plans filtered by country
   - If no country-specific plans, returns USD plans with currency conversion

2. **User Selects Plan**
   - User chooses a subscription plan
   - User may check current subscriptions: `GET /subscription/my-plans`

3. **User Creates Payment Order**
   - API Endpoint: `POST /payment/create-order/{plan_id}`
   - System validates plan exists and is active
   - System determines payment amount:
     - If plan.country_code == "DEFAULT": Converts price using exchange rate
     - Otherwise: Uses plan price directly
   - System removes any existing pending orders for same plan
   - System creates Razorpay order
   - System creates UserSubscription with:
     - `payment_status = "PENDING"`
     - `is_active = false`
     - `razorpay_order_id = order_id`
   - Returns: `{"order_id": "...", "razorpay_key": "...", "amount": ..., "currency": "...", "subscription_id": "..."}`

4. **User Completes Payment** (Frontend)
   - User redirected to Razorpay payment page
   - User enters payment details
   - Razorpay processes payment
   - Payment callback returns: `razorpay_order_id`, `razorpay_payment_id`, `razorpay_signature`

5. **User Verifies Payment**
   - API Endpoint: `POST /payment/verify`
   - System verifies payment signature using Razorpay SDK
   - System retrieves subscription by `razorpay_order_id`
   - System checks if already paid and active

6. **System Activates Subscription**
   - Expires all existing active subscriptions for user
   - Updates subscription:
     - `payment_status = "PAID"`
     - `is_active = true`
     - `is_expired = false`
     - `start_date = now()`
     - `end_date = now() + 30 days`
     - Stores `razorpay_payment_id` and `razorpay_signature`

7. **Response to User**
   - Returns: `{"message": "Payment successful & subscription activated"}`

**Decision Points:**
- ❌ Plan not found → `404 Not Found`
- ❌ Currency not supported → `400 Bad Request`
- ❌ Invalid payment signature → `400 Bad Request`
- ❌ Payment gateway unavailable → `502 Bad Gateway`

**Related Endpoints:**
- `GET /subscription/plans`
- `GET /subscription/my-plans`
- `POST /payment/create-order/{plan_id}`
- `POST /payment/verify`
- `GET /subscription/{subscription_id}/usage`

---

### 4. Create Valuation Request Flow

**Objective:** Create a property valuation request and receive report.

**Flow Steps:**

1. **User Checks Subscription**
   - API Endpoint: `GET /subscription/default` or `GET /subscription/my-plans`
   - User verifies they have an active subscription
   - User checks remaining reports: `GET /subscription/{subscription_id}/usage`

2. **User Prepares Valuation Data**
   - Collects property information:
     - Country, city, full address
     - Property type (residential, commercial, land, etc.)
     - Land area, built-up area, year built
     - Purpose of valuation
     - Contact information
   - Optional: Attach supporting documents

3. **User Submits Valuation Request**
   - API Endpoint: `POST /create`
   - Content-Type: `multipart/form-data`
   - Includes: `subscription_id`, form fields, optional attachment

4. **System Validates Request**
   - Validates subscription exists and belongs to user
   - Validates subscription is active and not expired
   - Validates subscription has remaining reports (if max_reports is set)
   - Validates property type/category

5. **System Creates Valuation Job**
   - Creates ValuationJob record with:
     - `status = "queued"`
     - `user_id`, `subscription_id`, `category`, `country_code`
     - `request_payload` (form data as JSON)
   - Determines country_code from user profile or IP address

6. **System Queues Job for Processing**
   - Submits job to Celery task queue
   - Returns immediately: `{"job_id": "...", "status": "queued", "message": "Valuation job queued successfully"}`

7. **User Monitors Job Status** (Polling)
   - API Endpoint: `GET /jobs/{job_id}`
   - Status values: `queued` → `processing` → `completed` or `failed`
   - User polls this endpoint until status is `completed` or `failed`

8. **Background Processing** (Celery Worker)
   - Updates job status to `processing`
   - Calls OpenAI API to generate valuation report
   - Generates forecast data
   - Builds report context
   - Renders HTML template
   - Generates PDF from HTML
   - Sends PDF via email to user
   - Saves ValuationReport to database
   - Increments subscription `reports_used` counter
   - Updates job: `status = "completed"`, `valuation_id = ...`, `pdf_path = ...`

9. **User Receives Email**
   - Email contains PDF attachment
   - Subject: "Your Desktop Valuation Report"

10. **User Accesses Valuation**
    - API Endpoint: `GET /valuation/{valuation_id}` - View details
    - API Endpoint: `GET /valuation/{valuation_id}/download` - Download PDF

**Decision Points:**
- ❌ No active subscription → `404 Not Found`
- ❌ Subscription expired → `403 Forbidden`
- ❌ Report limit exceeded → `403 Forbidden`
- ❌ Invalid property type → `400 Bad Request`
- ❌ Queue unavailable → `503 Service Unavailable`
- ❌ Job processing fails → Status set to `failed`, error_message stored

**Related Endpoints:**
- `GET /subscription/default`
- `GET /subscription/{subscription_id}/usage`
- `POST /create`
- `GET /jobs/{job_id}`
- `GET /valuation/{valuation_id}`
- `GET /valuation/{valuation_id}/download`
- `GET /my-valuations`

---

### 5. View and Download Valuation Flow

**Objective:** View valuation details and download PDF reports.

**Flow Steps:**

1. **User Lists Valuations**
   - API Endpoint: `GET /my-valuations`
   - Optional filters: `category`, `from_date`, `to_date`, `search`
   - Returns paginated list with: `valuation_id`, `category`, `country_code`, `created_at`

2. **User Selects Valuation**
   - User chooses a valuation from the list

3. **User Views Valuation Details**
   - API Endpoint: `GET /valuation/{valuation_id}`
   - System validates valuation belongs to user
   - Returns:
     - `valuation_id`, `category`, `country_code`
     - `user_fields` (original form data)
     - `ai_response` (AI-generated valuation data)
     - `created_at`

4. **User Downloads PDF** (Optional)
   - API Endpoint: `GET /valuation/{valuation_id}/download`
   - System validates valuation belongs to user
   - System checks if PDF file exists
   - Returns PDF file with:
     - `Content-Type: application/pdf`
     - `Content-Disposition: attachment; filename="{valuation_id}.pdf"`

**Decision Points:**
- ❌ Valuation not found → `404 Not Found`
- ❌ Valuation doesn't belong to user → `404 Not Found`
- ❌ PDF file not found → `404 Not Found`

**Related Endpoints:**
- `GET /my-valuations`
- `GET /valuation/{valuation_id}`
- `GET /valuation/{valuation_id}/download`

---

### 6. Profile Management Flow

**Objective:** View and update user profile information.

**Flow Steps:**

1. **User Views Profile**
   - API Endpoint: `GET /profile`
   - Returns: `id`, `username`, `email`, `mobile_number`, `country`

2. **User Updates Profile** (Optional)
   - API Endpoint: `PUT /edit-profile`
   - User can update: `username`, `email`, `mobile_number`
   - System validates:
     - New email not already in use
     - New mobile number not already in use
   - If email changes:
     - Sets `is_email_verified = false`
     - User must verify new email

3. **User Changes Password** (Optional)
   - API Endpoint: `POST /change-password`
   - User provides: `old_password`, `new_password`, `confirm_password`
   - System validates:
     - Old password is correct
     - New password matches confirmation
   - System updates password hash

**Decision Points:**
- ❌ Email already in use → `400 Bad Request`
- ❌ Mobile number already in use → `400 Bad Request`
- ❌ Old password incorrect → `401 Unauthorized`
- ❌ Passwords don't match → `400 Bad Request`

**Related Endpoints:**
- `GET /profile`
- `PUT /edit-profile`
- `POST /change-password`

---

### 7. Password Reset Flow

**Objective:** Reset forgotten password via email.

**Flow Steps:**

1. **User Requests Password Reset**
   - API Endpoint: `POST /forgot-password`
   - User provides: `email`
   - System validates email exists

2. **System Generates Reset Token**
   - Creates PasswordResetToken with:
     - `token_hash` (hashed random token)
     - `expires_at = now() + 30 minutes`
     - `used = false`

3. **System Sends Reset Email**
   - Email contains reset link: `{BASE_URL}/reset-password?token={raw_token}`
   - Returns: `{"message": "reset link sent to email"}`

4. **User Clicks Reset Link**
   - User navigates to reset password page
   - API Endpoint: `GET /reset-password` (returns HTML page)

5. **User Submits New Password**
   - API Endpoint: `POST /reset-password`
   - User provides: `token`, `new_password`, `confirm_password`
   - System validates:
     - Token is valid (not used, not expired)
     - Passwords match

6. **System Updates Password**
   - Updates user's password hash
   - Marks token as used
   - Returns: `{"message": "Password reset successful"}`

**Decision Points:**
- ❌ Email not registered → `404 Not Found`
- ❌ Invalid/expired token → `400 Bad Request`
- ❌ Passwords don't match → `400 Bad Request`

**Related Endpoints:**
- `POST /forgot-password`
- `GET /reset-password`
- `POST /reset-password`

---

### 8. Feedback Submission Flow

**Objective:** Submit feedback and communicate with support.

**Flow Steps:**

1. **User Submits Feedback**
   - API Endpoint: `POST /feedback`
   - User provides:
     - `type`: "GENERAL", "VALUATION", "PAYMENT", or "SUBSCRIPTION"
     - `subject`: Feedback subject
     - `message`: Feedback message
     - `rating`: Optional rating (1-5)
     - `valuation_id`: Optional (if related to valuation)
     - `subscription_id`: Optional (if related to subscription)

2. **System Creates Feedback**
   - Creates Feedback record with:
     - `status = "OPEN"`
     - `user_id` (from authenticated user)
   - Sends notification email to admin

3. **User Views Feedback**
   - API Endpoint: `GET /feedback/my`
   - Optional filters: `status`, `type`, `search`
   - Returns paginated list of user's feedback

4. **User Updates Feedback** (if status is OPEN)
   - API Endpoint: `PATCH /feedback/update/{feedback_id}`
   - User can update: `subject`, `message`, `rating`
   - Only allowed if `status == "OPEN"`

5. **User Replies to Feedback** (if admin has responded)
   - API Endpoint: `POST /feedback/{feedback_id}/messages`
   - User adds message to feedback thread
   - Creates FeedbackMessage with `sender = "USER"`

**Decision Points:**
- ❌ Feedback not found → `404 Not Found`
- ❌ Feedback status not OPEN → `400 Bad Request` (for updates)

**Related Endpoints:**
- `POST /feedback`
- `GET /feedback/my`
- `GET /feedback/{feedback_id}`
- `PATCH /feedback/update/{feedback_id}`
- `POST /feedback/{feedback_id}/messages`

---

## Admin Flows

### 1. Admin Login Flow

**Objective:** Authenticate admin user and obtain admin access token.

**Flow Steps:**

1. **Admin Initiates Login**
   - API Endpoint: `POST /admin/login`
   - Admin provides: `email`, `password`

2. **System Validates Admin**
   - Retrieves user by email
   - Verifies password
   - Checks: `is_superuser = true`
   - Checks: `is_active = true`

3. **System Generates Admin Token**
   - Creates access token with payload: `{"sub": user_id, "role": "superuser"}`
   - Token includes role claim for admin endpoints

4. **Response to Admin**
   - Returns: `{"access_token": "...", "token_type": "bearer"}`

**Decision Points:**
- ❌ User not found → `403 Forbidden`
- ❌ Not a superuser → `403 Forbidden`
- ❌ Invalid password → `401 Unauthorized`
- ❌ User inactive → `403 Forbidden`

**Related Endpoints:**
- `POST /admin/login`
- `GET /admin/me`
- `POST /admin/logout`
- `POST /admin/change-password`

---

### 2. User Management Flow

**Objective:** Admin manages user accounts.

**Flow Steps:**

1. **Admin Views User List**
   - API Endpoint: `GET /admin/users`
   - Optional filters:
     - `is_active`, `is_email_verified`, `is_superuser`
     - `country_id`, `verified_from`, `verified_to`
     - `verified_within_days`
     - `search` (username, email, mobile)
     - `sort_by`, `order`
   - Returns paginated list of users

2. **Admin Views User Details**
   - API Endpoint: `GET /admin/users/{user_id}`
   - Returns complete user information

3. **Admin Actions on Users:**

   **a. Toggle User Active Status**
   - API Endpoint: `PATCH /admin/users/{user_id}/toggle-active`
   - If deactivating: Revokes all refresh tokens (logs out from all devices)
   - Updates `is_active` status

   **b. Force Logout User**
   - API Endpoint: `POST /admin/users/{user_id}/logout`
   - Revokes all refresh tokens for user

   **c. Manually Verify Email**
   - API Endpoint: `POST /admin/users/{user_id}/verify-email`
   - Sets `is_email_verified = true`
   - Sets `email_verified_at = now()`

   **d. Reset User Password**
   - API Endpoint: `POST /admin/users/{user_id}/reset-password`
   - Admin provides: `new_password`, `confirm_password`
   - Updates password hash
   - Revokes all refresh tokens (user must login again)

**Decision Points:**
- ❌ User not found → `404 Not Found`
- ❌ Passwords don't match → `400 Bad Request`

**Related Endpoints:**
- `GET /admin/users`
- `GET /admin/users/{user_id}`
- `PATCH /admin/users/{user_id}/toggle-active`
- `POST /admin/users/{user_id}/logout`
- `POST /admin/users/{user_id}/verify-email`
- `POST /admin/users/{user_id}/reset-password`

---

### 3. Subscription Plan Management Flow

**Objective:** Admin manages subscription plans.

**Flow Steps:**

1. **Admin Views Plans**
   - API Endpoint: `GET /admin/subscription-plans`
   - Optional filters:
     - `country_code`, `is_active`, `currency`
     - `min_price`, `max_price`
     - `min_reports`, `max_reports`
     - `category`, `created_from`, `created_to`
     - `search` (plan name)
   - Returns paginated list of plans

2. **Admin Views Plan Details**
   - API Endpoint: `GET /admin/subscription-plans/{plan_id}`
   - Returns complete plan information

3. **Admin Creates New Plan**
   - API Endpoint: `POST /admin/subscription-plans`
   - Admin provides:
     - `name`, `country_code`, `price`, `currency`
     - `max_reports` (optional, null for unlimited)
     - `allowed_categories` (array)
   - System creates plan with `is_active = true`
   - Name and country_code are converted to uppercase

4. **Admin Updates Plan**
   - API Endpoint: `PUT /admin/subscription-plans/{plan_id}`
   - Admin provides fields to update (all optional)
   - Only provided fields are updated

5. **Admin Toggles Plan Status**
   - API Endpoint: `PATCH /admin/subscription-plans/{plan_id}/toggle`
   - Toggles `is_active` status
   - Inactive plans won't be shown to users

**Decision Points:**
- ❌ Plan not found → `404 Not Found`
- ❌ Database error → `500 Internal Server Error`

**Related Endpoints:**
- `GET /admin/subscription-plans`
- `GET /admin/subscription-plans/{plan_id}`
- `POST /admin/subscription-plans`
- `PUT /admin/subscription-plans/{plan_id}`
- `PATCH /admin/subscription-plans/{plan_id}/toggle`

---

### 4. User Subscription Management Flow

**Objective:** Admin manages user subscriptions.

**Flow Steps:**

1. **Admin Views All Subscriptions**
   - API Endpoint: `GET /admin/user-subscriptions`
   - Optional filters:
     - `user_id`, `plan_id`, `is_active`, `is_expired`
     - `payment_status`
     - `pricing_country_code`, `ip_country_code`, `payment_country_code`
     - `start_from`, `start_to`, `end_from`, `end_to`
     - `purchased_within_days`
     - `search` (plan name)
   - Returns paginated list

2. **Admin Views User's Subscriptions**
   - API Endpoint: `GET /admin/users/{user_id}/subscriptions`
   - Returns all subscriptions for specific user
   - Optional filters: `payment_status`, `is_active`, `country_code`, date ranges

3. **Admin Assigns Subscription to User**
   - API Endpoint: `POST /admin/users/{user_id}/assign-subscription`
   - Admin provides:
     - `plan_id`: Subscription plan to assign
     - `duration_days`: Subscription duration (default: 30)
     - `pricing_country_code`: Optional (defaults to plan's country_code)
   - System creates UserSubscription with:
     - `is_active = true`
     - `start_date = now()`
     - `end_date = now() + duration_days`

4. **Admin Updates Subscription**
   - API Endpoint: `PATCH /admin/user-subscriptions/{subscription_id}`
   - Admin can:
     - `extend_days`: Extend subscription by N days
     - `reset_reports_used`: Reset usage counter to 0
     - `deactivate`: Deactivate subscription

5. **Admin Cancels Subscription**
   - API Endpoint: `POST /admin/user-subscriptions/{subscription_id}/cancel`
   - Sets `is_active = false`
   - Sets `end_date = now()`

**Decision Points:**
- ❌ User not found → `404 Not Found`
- ❌ Plan not found → `404 Not Found`
- ❌ Subscription not found → `404 Not Found`

**Related Endpoints:**
- `GET /admin/user-subscriptions`
- `GET /admin/users/{user_id}/subscriptions`
- `POST /admin/users/{user_id}/assign-subscription`
- `PATCH /admin/user-subscriptions/{subscription_id}`
- `POST /admin/user-subscriptions/{subscription_id}/cancel`

---

### 5. Valuation Management Flow

**Objective:** Admin views and manages valuations.

**Flow Steps:**

1. **Admin Views All Valuations**
   - API Endpoint: `GET /admin/valuations`
   - Optional filters:
     - `user_id`, `country_code`, `category`
     - `from_date`, `to_date`
     - `search` (valuation_id, category, country_code)
     - `sort_by`, `order`
   - Returns paginated list

2. **Admin Views Valuation Details**
   - API Endpoint: `GET /admin/valuations/{valuation_id}`
   - Returns complete valuation information including:
     - `user_fields`, `ai_response`, `report_context`
     - `pdf_path`, `created_at`

3. **Admin Views User's Valuations**
   - API Endpoint: `GET /admin/users/{user_id}/valuations`
   - Returns all valuations for specific user
   - Optional filters: `search` (valuation_id)

4. **Admin Deletes Valuation** (if needed)
   - API Endpoint: `DELETE /admin/valuations/{valuation_id}/delete`
   - Permanently deletes valuation record
   - Note: PDF file may need manual cleanup

**Decision Points:**
- ❌ Valuation not found → `404 Not Found`
- ❌ User not found → `404 Not Found`

**Related Endpoints:**
- `GET /admin/valuations`
- `GET /admin/valuations/{valuation_id}`
- `GET /admin/users/{user_id}/valuations`
- `DELETE /admin/valuations/{valuation_id}/delete`

---

### 6. Feedback Management Flow

**Objective:** Admin manages user feedback.

**Flow Steps:**

1. **Admin Views All Feedback**
   - API Endpoint: `GET /admin/feedback`
   - Optional filters:
     - `user_id`, `status`, `type`, `rating`
     - `valuation_id`, `subscription_id`
     - `search` (subject, message, valuation_id)
   - Returns paginated list

2. **Admin Views Feedback Details**
   - API Endpoint: `GET /admin/feedback/{feedback_id}`
   - Returns complete feedback information

3. **Admin Takes Action on Feedback**
   - API Endpoint: `POST /admin/feedback/{feedback_id}/action`
   - Admin can:
     - Update `status`: "OPEN", "IN_PROGRESS", "RESOLVED", "CLOSED"
     - Add `reply`: Admin response message
     - Set `notify_user`: Send email notification
     - Add `admin_note`: Internal note
   - If reply provided without status, sets status to "IN_PROGRESS"
   - Creates FeedbackMessage with `sender = "ADMIN"`
   - Sends email to user if `notify_user = true`

4. **Admin Deletes Feedback** (if needed)
   - API Endpoint: `DELETE /admin/feedback/{feedback_id}`
   - Permanently deletes feedback record

**Decision Points:**
- ❌ Feedback not found → `404 Not Found`

**Related Endpoints:**
- `GET /admin/feedback`
- `GET /admin/feedback/{feedback_id}`
- `POST /admin/feedback/{feedback_id}/action`
- `DELETE /admin/feedback/{feedback_id}`

---

### 7. Dashboard Overview Flow

**Objective:** Admin views system statistics and analytics.

**Flow Steps:**

1. **Admin Views Overview**
   - API Endpoint: `GET /admin/dashboard/overview`
   - Returns:
     - Total users, active users
     - Total subscriptions, active subscriptions
     - Total valuations

2. **Admin Views User Statistics**
   - API Endpoint: `GET /admin/dashboard/users`
   - Returns:
     - Email verified/unverified counts
     - Inactive users count
     - New users in last 30 days

3. **Admin Views Subscription Breakdown**
   - API Endpoint: `GET /admin/dashboard/subscriptions`
   - Returns breakdown by country and plan:
     - Total and active subscription counts
     - Revenue calculations (total and active)

4. **Admin Views Valuation Statistics**
   - API Endpoint: `GET /admin/dashboard/valuations`
   - Returns:
     - Count by category (residential, commercial, land, etc.)
     - Valuations in last 30 days

5. **Admin Views Country Statistics**
   - API Endpoint: `GET /admin/dashboard/countries`
   - Returns:
     - Subscription counts by country
     - Valuation counts by country

6. **Admin Views Feedback Statistics**
   - API Endpoint: `GET /admin/dashboard/feedback`
   - Returns:
     - Total feedback count
     - Open feedback count
     - Average rating

**Related Endpoints:**
- `GET /admin/dashboard/overview`
- `GET /admin/dashboard/users`
- `GET /admin/dashboard/subscriptions`
- `GET /admin/dashboard/valuations`
- `GET /admin/dashboard/countries`
- `GET /admin/dashboard/feedback`

---

## System Background Processes

### Valuation Processing Flow

**Objective:** Process valuation requests asynchronously.

**Flow Steps:**

1. **Job Queued**
   - ValuationJob created with `status = "queued"`
   - Job submitted to Celery task queue

2. **Worker Picks Up Job**
   - Celery worker retrieves job from queue
   - Updates job: `status = "processing"`

3. **AI Report Generation**
   - Calls OpenAI API with user input
   - Generates core valuation report
   - Generates forecast data
   - Combines into complete AI response

4. **Report Building**
   - Builds report context from AI response and user input
   - Renders HTML template with context
   - Generates PDF from HTML

5. **Email Notification**
   - Sends PDF via email to user
   - Subject: "Your Desktop Valuation Report"

6. **Database Updates**
   - Saves ValuationReport record
   - Updates job: `status = "completed"`, `valuation_id`, `pdf_path`
   - Increments subscription `reports_used` counter

7. **Error Handling**
   - If processing fails:
     - Updates job: `status = "failed"`, `error_message = error`
     - Job can be retried (max 2 retries with backoff)

**Job Status Flow:**
```
queued → processing → completed
                    ↓
                  failed
```

**Related Components:**
- Celery task: `process_valuation_job`
- OpenAI API integration
- PDF generation service
- Email service

---

### Subscription Expiry Flow

**Objective:** Automatically expire subscriptions and send reminders.

**Flow Steps:**

1. **Expiry Check** (Scheduled Job)
   - Runs periodically (e.g., daily via Celery Beat)
   - Finds subscriptions where:
     - `is_expired = false`
     - `end_date < now()`
   - Updates: `is_expired = true`
   - Logs count of expired subscriptions

2. **Expiry Reminders** (Scheduled Job)
   - Runs periodically (e.g., daily via Celery Beat)
   - Finds active subscriptions with `end_date` in future
   - Calculates days until expiry
   - If days_left in (1, 2, 3):
     - Sends expiry reminder email to user
     - Includes plan name and expiry date

**Related Components:**
- Celery Beat scheduled tasks
- Email service for reminders
- Subscription expiry service

---

## Flow Diagrams Summary

### User Registration & Login
```
Registration → Email Verification → Login → Access Tokens
```

### Subscription Purchase
```
View Plans → Create Order → Payment → Verify → Activate
```

### Valuation Request
```
Check Subscription → Submit Request → Queue Job → Process → Email PDF → View/Download
```

### Admin User Management
```
Login → View Users → Select User → Action (Toggle/Verify/Reset/Logout)
```

### Admin Subscription Management
```
View Plans → Create/Update/Toggle → View User Subs → Assign/Update/Cancel
```

---

## Notes

1. **Authentication**: All protected endpoints require valid Bearer token in Authorization header
2. **Email Verification**: Users must verify email before accessing protected endpoints
3. **Subscription Limits**: Valuation creation enforces subscription limits (max_reports)
4. **Async Processing**: Valuations are processed asynchronously via Celery
5. **Token Expiration**: Access tokens expire; use refresh token to obtain new tokens
6. **Country Detection**: Country is automatically detected from user profile or IP address
7. **Currency Conversion**: Plans are automatically converted to user's currency when available
8. **Error Handling**: All errors return appropriate HTTP status codes with error messages
9. **Pagination**: List endpoints support pagination with page and limit parameters
10. **Background Jobs**: Subscription expiry and reminders run as scheduled background jobs

---

*Last Updated: January 2024*
