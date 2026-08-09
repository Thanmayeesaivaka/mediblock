# 🏥 MediBlock

### Secure, Cloud-Based Healthcare Management and Medical Record System

MediBlock is a web-based healthcare management platform designed to provide secure storage, controlled access, sharing, and integrity verification of medical records. The system combines **Flask, MongoDB Atlas, cloud deployment, encryption, hashing, and blockchain concepts** to create a secure environment for managing healthcare information.

The project was developed from **September 2025 to February 2026** by a **3-member team**.

---

## 📌 Project Overview

Healthcare organizations handle highly sensitive patient information such as medical history, diagnoses, prescriptions, treatment details, and reports. Traditional systems may face challenges related to unauthorized access, data integrity, and secure information sharing.

MediBlock addresses these challenges by providing a centralized web-based platform where different healthcare stakeholders can securely interact with medical information.

The system provides separate modules for:

- 👨‍⚕️ Medical Staff
- 🧑‍🦽 Patients
- 🔬 Research Analysts
- 🏥 Insurance Personnel
- 🛠️ Administrators

The application uses **MongoDB Atlas** as its cloud database and **Render** for cloud deployment. Cryptographic hashing and encryption are used to protect sensitive information and verify record integrity.

---

## 🎯 Objectives

The major objectives of MediBlock are:

- Securely manage electronic medical records.
- Provide role-based access to healthcare information.
- Allow medical staff to update patient treatment details.
- Enable patients to view their medical history.
- Provide controlled data-sharing capabilities.
- Secure sensitive treatment information using encryption.
- Maintain data integrity using cryptographic hashing.
- Demonstrate blockchain-based medical record verification.
- Store application data using a cloud-based MongoDB database.
- Deploy the application as a publicly accessible cloud service.

---

## ✨ Key Features

### 👨‍⚕️ Medical Staff Module

Medical staff can:

- Register
- Login
- View Patient Records
- Update Treatment Details
- Upload Medical Reports
- Share Patient Data
- Track Treatment History
- Logout

---

### 🧑 Patient Module

Patients can:

- Register
- Login
- View Medical History
- Grant Access to authorized personnel
- Track Treatments
- View medical records
- Logout

---

### 🔬 Research Analyst Module

Research analysts can:

- Login
- Analyze healthcare information
- Generate reports
- Review available medical data
- Submit research findings
- Logout

---

### 🏥 Insurance Module

Insurance personnel can:

- Login
- Verify policies
- Receive claims
- Validate claims
- Approve or reject claims
- Update payment information
- Logout

---

### 🛠️ Admin Module

The administrator provides centralized access for managing and monitoring the application.

---
## ☁️ Cloud Integration

MediBlock uses cloud technology to deploy the web application and store healthcare-related information. The application is deployed on **Render Cloud**, while **MongoDB Atlas** is used as the cloud database.

### Cloud Architecture

```text
                User
                  │
                  ▼
        ┌──────────────────┐
        │   Render Cloud   │
        │  Flask Web App   │
        └────────┬─────────┘
                 │
                 ▼
        ┌──────────────────┐
        │  MongoDB Atlas   │
        │  Cloud Database  │
        └──────────────────┘
```

### Cloud Technologies Used

- **Render Cloud** – Used to deploy and host the MediBlock Flask application.
- **MongoDB Atlas** – Used for cloud-based storage of application and healthcare data.
- **Gunicorn** – Used as the production application server on Render.
- **GitHub** – Used for source code management and deployment integration.

### Benefits of Cloud Integration

- 🌐 Provides online access to the MediBlock application.
- ☁️ Enables cloud-based storage of application data.
- 🔄 Allows application updates through GitHub and Render.
- 📈 Provides a scalable foundation for future expansion.
- 🔐 Works together with encryption and hashing mechanisms to improve data security.

### Cloud Data Flow

```text
User
  ↓
MediBlock Web Application
  ↓
Render Cloud
  ↓
Flask Backend
  ↓
MongoDB Atlas
  ↓
Cloud Data Storage
```

The integration of **Render Cloud and MongoDB Atlas** transforms MediBlock from a locally hosted application into a **cloud-accessible healthcare management system**.

---

## 🔐 Security Features

MediBlock incorporates multiple security mechanisms to protect sensitive healthcare information and maintain data integrity.

### 🔒 Encryption

Sensitive treatment information is encrypted using the **Fernet symmetric encryption mechanism** before being stored.

### 🔑 Cryptographic Hashing

A **SHA-256 hash** is generated for treatment information to help verify data integrity.

Example:

```text
Medical Record
      ↓
SHA-256 Hash
      ↓
Integrity Verification
```
