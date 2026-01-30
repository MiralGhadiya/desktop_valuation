# Desktop Valuation API - Project Flow Documentation

## Overview

This document describes the overall flow of the Desktop Valuation system from both User and Admin perspectives, showing the complete journey through the application.

---

## User Side Flow

### Complete User Journey

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER SIDE FLOW                                │
└─────────────────────────────────────────────────────────────────┘

1. REGISTRATION & VERIFICATION
   ┌─────────────────┐
   │ User Registers  │
   │ (Email, Mobile, │
   │  Password)      │
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │ System Creates  │
   │ User Account    │
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │ Assigns FREE    │
   │ Subscription    │
   │ (if available)  │
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │ Sends Email     │
   │ Verification    │
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │ User Clicks     │
   │ Verification    │
   │ Link            │
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │ Email Verified  │
   └─────────────────┘

2. LOGIN & AUTHENTICATION
   ┌─────────────────┐
   │ User Logs In    │
   │ (Email/Password)│
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │ System Validates│
   │ Credentials      │
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │ Returns Access  │
   │ & Refresh Tokens│
   └─────────────────┘

3. SUBSCRIPTION MANAGEMENT
   ┌─────────────────┐
   │ User Views      │
   │ Available Plans │
   │ (Country-based) │
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │ User Selects    │
   │ Plan            │
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │ Creates Payment │
   │ Order (Razorpay)│
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │ User Completes  │
   │ Payment         │
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │ Verifies Payment│
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │ Subscription    │
   │ Activated       │
   │ (30 days)       │
   └─────────────────┘

4. CREATE VALUATION REQUEST
   ┌─────────────────┐
   │ User Checks     │
   │ Active          │
   │ Subscription    │
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │ User Fills      │
   │ Property Form   │
   │ (Address, Type, │
   │  Area, etc.)    │
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │ Submits         │
   │ Valuation       │
   │ Request         │
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │ System Validates│
   │ Subscription    │
   │ & Limits        │
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │ Creates Job &   │
   │ Queues for      │
   │ Processing      │
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │ Returns Job ID  │
   └─────────────────┘

5. VALUATION PROCESSING (Background)
   ┌─────────────────┐
   │ Celery Worker   │
   │ Picks Up Job    │
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │ Calls OpenAI API│
   │ for Valuation   │
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │ Generates PDF   │
   │ Report          │
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │ Sends PDF via   │
   │ Email to User   │
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │ Saves Report to │
   │ Database        │
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │ Increments      │
   │ Subscription    │
   │ Usage Counter   │
   └─────────────────┘

6. VIEW & DOWNLOAD VALUATIONS
   ┌─────────────────┐
   │ User Views      │
   │ Valuation List  │
   │ (with filters)  │
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │ User Selects     │
   │ Valuation        │
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │ Views Details   │
   │ or Downloads    │
   │ PDF             │
   └─────────────────┘

7. PROFILE & SETTINGS
   ┌─────────────────┐
   │ User Views/     │
   │ Updates Profile │
   │ (Username,      │
   │  Email, Mobile) │
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │ Changes Password│
   │ (if needed)     │
   └─────────────────┘

8. FEEDBACK & SUPPORT
   ┌─────────────────┐
   │ User Submits    │
   │ Feedback        │
   │ (General, Issue, │
   │  Rating)        │
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │ Views Feedback   │
   │ Status & Replies │
   └─────────────────┘
```

### User Flow Summary

**Phase 1: Onboarding**
- Register → Verify Email → Login → Get Tokens

**Phase 2: Subscription**
- View Plans → Select Plan → Create Payment Order → Complete Payment → Verify → Activate

**Phase 3: Valuation**
- Check Subscription → Fill Form → Submit Request → Job Queued → Background Processing → Receive Email → View/Download

**Phase 4: Management**
- View Valuations → Manage Profile → Submit Feedback

---

## Admin Side Flow

### Complete Admin Journey

```
┌─────────────────────────────────────────────────────────────────┐
│                    ADMIN SIDE FLOW                               │
└─────────────────────────────────────────────────────────────────┘

1. ADMIN LOGIN
   ┌─────────────────┐
   │ Admin Logs In   │
   │ (Email/Password)│
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │ System Validates│
   │ (Superuser Check)│
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │ Returns Admin   │
   │ Access Token    │
   └─────────────────┘

2. DASHBOARD OVERVIEW
   ┌─────────────────┐
   │ Admin Views     │
   │ Dashboard       │
   │ Statistics      │
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │ Sees Overview:  │
   │ - Total Users   │
   │ - Subscriptions │
   │ - Valuations    │
   │ - Feedback      │
   │ - Revenue       │
   └─────────────────┘

3. USER MANAGEMENT
   ┌─────────────────┐
   │ Admin Views     │
   │ All Users       │
   │ (with filters)  │
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │ Admin Actions:  │
   │ - View Details  │
   │ - Toggle Active │
   │ - Verify Email  │
   │ - Reset Password│
   │ - Force Logout  │
   └─────────────────┘

4. SUBSCRIPTION PLAN MANAGEMENT
   ┌─────────────────┐
   │ Admin Views     │
   │ All Plans      │
   │ (by country)    │
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │ Admin Actions:  │
   │ - Create Plan   │
   │ - Update Plan   │
   │ - Toggle Status │
   │ - Set Pricing   │
   │ - Set Limits    │
   └─────────────────┘

5. USER SUBSCRIPTION MANAGEMENT
   ┌─────────────────┐
   │ Admin Views     │
   │ All User        │
   │ Subscriptions   │
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │ Admin Actions:  │
   │ - View by User  │
   │ - Assign Plan   │
   │ - Extend Days   │
   │ - Reset Usage   │
   │ - Cancel        │
   └─────────────────┘

6. VALUATION MANAGEMENT
   ┌─────────────────┐
   │ Admin Views     │
   │ All Valuations │
   │ (with filters)  │
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │ Admin Actions:  │
   │ - View Details  │
   │ - View by User  │
   │ - Download PDF  │
   │ - Delete        │
   └─────────────────┘

7. FEEDBACK MANAGEMENT
   ┌─────────────────┐
   │ Admin Views     │
   │ All Feedback   │
   │ (with filters)  │
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │ Admin Actions:  │
   │ - View Details  │
   │ - Reply to User │
   │ - Update Status │
   │ - Add Notes     │
   │ - Delete        │
   └─────────────────┘
```

### Admin Flow Summary

**Phase 1: Access**
- Login → Dashboard Overview

**Phase 2: User Management**
- View Users → Manage User Accounts → Verify/Reset/Deactivate

**Phase 3: Subscription Management**
- Manage Plans → Manage User Subscriptions → Assign/Extend/Cancel

**Phase 4: Content Management**
- View Valuations → Monitor Reports → Manage Feedback

---

## Complete System Flow

### User Registration to Valuation

```
USER REGISTRATION
    │
    ├─→ Email Verification
    │
    ├─→ FREE Subscription Assigned (if available)
    │
    └─→ User Logs In
         │
         ├─→ Views Subscription Plans
         │    │
         │    └─→ Purchases Subscription
         │         │
         │         └─→ Subscription Activated
         │
         └─→ Creates Valuation Request
              │
              ├─→ System Validates Subscription
              │
              ├─→ Job Queued (Celery)
              │
              ├─→ Background Processing
              │    │
              │    ├─→ AI Valuation Generated
              │    │
              │    ├─→ PDF Report Created
              │    │
              │    ├─→ Email Sent to User
              │    │
              │    └─→ Report Saved to Database
              │
              └─→ User Views/Downloads Report
```

### Admin Management Flow

```
ADMIN LOGIN
    │
    └─→ Dashboard
         │
         ├─→ User Management
         │    │
         │    ├─→ View/Filter Users
         │    │
         │    ├─→ Toggle Active Status
         │    │
         │    ├─→ Verify Emails
         │    │
         │    └─→ Reset Passwords
         │
         ├─→ Subscription Management
         │    │
         │    ├─→ Manage Plans
         │    │    │
         │    │    ├─→ Create/Update Plans
         │    │    │
         │    │    └─→ Set Pricing & Limits
         │    │
         │    └─→ Manage User Subscriptions
         │         │
         │         ├─→ Assign Plans
         │         │
         │         ├─→ Extend/Cancel
         │         │
         │         └─→ Reset Usage
         │
         ├─→ Valuation Management
         │    │
         │    ├─→ View All Valuations
         │    │
         │    ├─→ View by User
         │    │
         │    └─→ Delete (if needed)
         │
         └─→ Feedback Management
              │
              ├─→ View All Feedback
              │
              ├─→ Reply to Users
              │
              ├─→ Update Status
              │
              └─→ Delete (if needed)
```

---

## Key Workflows

### 1. New User Onboarding Flow

```
Registration
    ↓
Email Verification
    ↓
Login
    ↓
View Plans
    ↓
Purchase Subscription
    ↓
Create Valuation
    ↓
Receive Report
```

### 2. Valuation Creation Flow

```
Check Subscription
    ↓
Fill Property Form
    ↓
Submit Request
    ↓
Job Queued
    ↓
[Background Processing]
    ├─→ AI Analysis
    ├─→ PDF Generation
    ├─→ Email Notification
    └─→ Database Save
    ↓
User Receives Email
    ↓
User Views/Downloads Report
```

### 3. Subscription Purchase Flow

```
View Plans (Country-based)
    ↓
Select Plan
    ↓
Create Payment Order
    ↓
Complete Payment (Razorpay)
    ↓
Verify Payment
    ↓
Subscription Activated
    ↓
Can Create Valuations
```

### 4. Admin Daily Operations Flow

```
Login
    ↓
Dashboard Overview
    ↓
[Monitor]
    ├─→ User Activity
    ├─→ Subscription Status
    ├─→ Valuation Requests
    └─→ Feedback
    ↓
[Take Actions]
    ├─→ Manage Users
    ├─→ Update Plans
    ├─→ Handle Feedback
    └─→ View Reports
```

---

## System Components Interaction

### User Side Components

```
Frontend Application
    │
    ├─→ Authentication API
    │    └─→ JWT Tokens
    │
    ├─→ Subscription API
    │    └─→ Payment Gateway (Razorpay)
    │
    ├─→ Valuation API
    │    └─→ Celery Queue
    │         └─→ Background Workers
    │              ├─→ OpenAI API
    │              ├─→ PDF Generator
    │              └─→ Email Service
    │
    └─→ Feedback API
         └─→ Email Notifications
```

### Admin Side Components

```
Admin Dashboard
    │
    ├─→ User Management API
    │
    ├─→ Subscription Management API
    │
    ├─→ Valuation Management API
    │
    ├─→ Feedback Management API
    │
    └─→ Dashboard Statistics API
```

---

## Background Processes

### Automated Tasks

```
1. Subscription Expiry Check
   └─→ Runs Daily
       └─→ Marks Expired Subscriptions
           └─→ Deactivates Access

2. Expiry Reminders
   └─→ Runs Daily
       └─→ Checks Subscriptions Expiring in 1-3 Days
           └─→ Sends Email Reminders

3. Valuation Processing
   └─→ Runs on Demand (Celery)
       └─→ Processes Queued Jobs
           └─→ Generates Reports
               └─→ Sends Emails
```

---

## Data Flow

### User Data Flow

```
User Input
    ↓
API Validation
    ↓
Database Storage
    ↓
Background Processing (if needed)
    ↓
Result Storage
    ↓
User Notification
    ↓
User Retrieval
```

### Admin Data Flow

```
Admin Request
    ↓
API Validation
    ↓
Database Query
    ↓
Data Aggregation
    ↓
Response to Admin
```

---

## Summary

### User Journey
1. **Register** → Verify Email → Login
2. **Purchase** Subscription → Activate
3. **Create** Valuation Request → Receive Report
4. **Manage** Profile & View History
5. **Submit** Feedback for Support

### Admin Journey
1. **Login** → View Dashboard
2. **Manage** Users (Verify, Reset, Deactivate)
3. **Manage** Subscription Plans & User Subscriptions
4. **Monitor** Valuations & Reports
5. **Handle** User Feedback & Support

### System Flow
- **Synchronous**: User actions, API responses, database operations
- **Asynchronous**: Valuation processing, email sending, scheduled tasks
- **Background**: Subscription expiry, reminders, job processing

---

*Last Updated: January 2024*
