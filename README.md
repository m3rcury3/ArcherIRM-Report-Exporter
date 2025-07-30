# ArcherIRM Report Exporter

Automate the extraction of saved reports from ArcherIRM using the SOAP API. This script authenticates via local user credentials, paginates through report results, and exports them to a clean CSV file.

---

## 🚀 Features

- Authenticates using `CreateDomainUserSessionFromInstance`
- Executes saved reports via `SearchRecordsByReport`
- Handles pagination (250 records per page)
- Extracts field definitions for readable column names
- Outputs a single CSV file with all records

---

## 🧰 Requirements

- Python 3.6+
- Internet access to your ArcherIRM server
- A saved report in Archer with record-level data

### Python Dependencies

Install required packages:

```bash
pip install requests lxml
