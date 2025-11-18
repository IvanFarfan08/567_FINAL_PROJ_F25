import json
from MRTD import encode_mrz_strings

def encode_all_records():
    """Encode all decoded records and save to records_encoded.json"""
    with open('records_decoded.json', 'r') as f:
        data = json.load(f)

    records_decoded = data['records_decoded']
    print(f"Processing {len(records_decoded)} records...")

    # Encode each record
    records_encoded = []
    for i, record in enumerate(records_decoded):
        # Combine line1 and line2 data into a single dictionary
        record_data = {
            "document_type": "P",  # Passport
            "country_code": record['line1']['issuing_country'],
            "last_name": record['line1']['last_name'],
            "first_name": record['line1']['given_name'].split()[0] if record['line1']['given_name'] else "",
            "middle_names": " ".join(record['line1']['given_name'].split()[1:]) if len(record['line1']['given_name'].split()) > 1 else None,
            "passport_number": record['line2']['passport_number'],
            "birth_date": record['line2']['birth_date'],
            "sex": record['line2']['sex'],
            "expiration_date": record['line2']['expiration_date'],
            "personal_number": record['line2']['personal_number']
        }

        # Encode to MRZ format
        line1, line2 = encode_mrz_strings(record_data)

        # Combine with semicolon separator
        encoded_record = f"{line1};{line2}"
        records_encoded.append(encoded_record)

        # Progress indicator
        if (i + 1) % 1000 == 0:
            print(f"Processed {i + 1} records...")

    # Save encoded records
    output_data = {"records_encoded": records_encoded}
    with open('records_encoded.json', 'w') as f:
        json.dump(output_data, f, indent=4)


if __name__ == "__main__":
    encode_all_records()
