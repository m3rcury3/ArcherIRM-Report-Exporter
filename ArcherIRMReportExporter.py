import requests
from lxml import etree
import csv
import xml.etree.ElementTree as ET
import html

# Step 1: Authenticate to Archer and retrieve a session token
def archer_login(username, password, instance):
    url = "https://<ArcherHost>/ws/general.asmx" ## REPLACE <ArcherHost> by the Archer app server hostname and IIS path
    headers = {
        'Content-Type': 'application/soap+xml; charset=utf-8',
        'SOAPAction': 'http://archer-tech.com/webservices/CreateDomainUserSessionFromInstance'
    }

    body = f"""<?xml version="1.0" encoding="utf-8"?>
    <soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope"
                   xmlns:web="http://archer-tech.com/webservices/">
       <soap:Header/>
       <soap:Body>
          <web:CreateDomainUserSessionFromInstance>
             <web:userName>{username}</web:userName>
             <web:instanceName>{instance}</web:instanceName>
             <web:password>{password}</web:password>
             <web:usersDomain></web:usersDomain>
          </web:CreateDomainUserSessionFromInstance>
       </soap:Body>
    </soap:Envelope>"""

    response = requests.post(url, data=body, headers=headers, verify=False)
    response.raise_for_status()

    tree = etree.fromstring(response.content)
    token = tree.xpath('//web:CreateDomainUserSessionFromInstanceResponse/web:CreateDomainUserSessionFromInstanceResult/text()', namespaces={'web': 'http://archer-tech.com/webservices/'})
    return token[0] if token else None

# Step 2: Run a saved report using its GUID and page number
def run_report(session_token, report_guid, page_number):
    url = "https://<ArcherHost>/ws/search.asmx" ## REPLACE <ArcherHost> by the Archer app server hostname and IIS path
    headers = {
        'Content-Type': 'application/soap+xml; charset=utf-8',
        'SOAPAction': 'http://archer-tech.com/webservices/SearchRecordsByReport'
    }

    body = f"""<?xml version="1.0" encoding="utf-8"?>
    <soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope"
                   xmlns:web="http://archer-tech.com/webservices/">
       <soap:Header/>
       <soap:Body>
          <web:SearchRecordsByReport>
             <web:sessionToken>{session_token}</web:sessionToken>
             <web:reportIdOrGuid>{report_guid}</web:reportIdOrGuid>
             <web:pageNumber>{page_number}</web:pageNumber>
          </web:SearchRecordsByReport>
       </soap:Body>
    </soap:Envelope>"""

    response = requests.post(url, data=body, headers=headers, verify=False)
    response.raise_for_status()
    return response.content

# Step 3: Parse embedded XML and extract records
def extract_records_from_embedded_xml(embedded_xml):
    embedded_root = ET.fromstring(embedded_xml)

    # Build field ID → name mapping
    field_map = {}
    for fd in embedded_root.findall('.//FieldDefinition'):
        field_id = fd.get('id')
        field_name = fd.get('name')
        if field_id and field_name:
            field_map[field_id] = field_name

    records = []
    for record in embedded_root.findall('.//Record'):
        row = {}
        for field in record.findall('.//Field'):
            field_id = field.get('id')
            field_name = field_map.get(field_id, f"Field_{field_id}")
            value = field.text.strip() if field.text else ''
            row[field_name] = value
        records.append(row)

    return records, int(embedded_root.get('count', '0'))

# Step 4: Export all records to CSV
def export_all_pages_to_csv(session_token, report_guid, output_path, page_size=250):
    all_records = []
    page_number = 1
    total_records = None

    while True:
        print(f"📄 Fetching page {page_number}...")
        response_content = run_report(session_token, report_guid, page_number)

        root = ET.fromstring(response_content)
        ns = {
            'soap': 'http://www.w3.org/2003/05/soap-envelope',
            'web': 'http://archer-tech.com/webservices/'
        }

        result_node = root.find('.//web:SearchRecordsByReportResult', ns)
        if result_node is None or not result_node.text:
            print("⚠️ No embedded XML found.")
            break

        embedded_xml = html.unescape(result_node.text)
        records, total_records = extract_records_from_embedded_xml(embedded_xml)
        all_records.extend(records)

        if len(all_records) >= total_records:
            print(f"✅ All {total_records} records fetched.")
            break

        page_number += 1

    if all_records:
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=all_records[0].keys())
            writer.writeheader()
            writer.writerows(all_records)
        print(f"📁 Exported {len(all_records)} records to {output_path}")
    else:
        print("⚠️ No records to export.")

# Step 5: Main execution flow
if __name__ == "__main__":
    username = "ArcherUsername"   ### Replace ArcherUsername with actual username
    password = "UserPassword"   ### Replace UserPassword with actual user password
    instance = "InstanceName"   ### Replace InstanceName with actual Archer instance name (Case sensitive)
    report_guid = "{GUID}"   ### Replace {GUID} with actual GUID e.g. {4D2B0ABC-15AB-4567-8EED-22032399060A}
    output_path = r"ArcherReportExport.csv"   ### Replace with desired path if needed

    try:
        print("🔐 Authenticating to Archer...")
        token = archer_login(username, password, instance)

        print("📊 Running paginated report export...")
        export_all_pages_to_csv(token, report_guid, output_path)

        print("✅ Report export completed successfully.")
    except Exception as e:
        print(f"❌ An error occurred: {e}")
