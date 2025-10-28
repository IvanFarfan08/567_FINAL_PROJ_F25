def process_mrz_scan():
    # Placeholder function for processing MRZ scans. Not implemented in this project
    pass

def query_database():
    # Placeholder function for querying a database. Not implemented in this project
    pass

def decode_mrz_line1(string1: str) -> dict:
    """Decode MRZ line 1 (TD3): document type, issuing state, surname, given names."""
    document_type = string1[0]
    country_code = string1[2:5]

    name_field = string1[5:]
    parts = name_field.split("<<", 1)

    raw_last_name = parts[0]
    raw_given_block = parts[1] if len(parts) > 1 else ""

    # Replace filler '<' with spaces in surname, then strip spaces.
    last_name = raw_last_name.replace("<", " ").strip()

    # Split given names by '<', filter out empties (fillers), normalize spaces.
    given_words = [word for word in raw_given_block.split('<') if word]
    first_name = given_words[0].strip() if given_words else ""
    middle_names = " ".join(word.strip() for word in given_words[1:]) if len(given_words) > 1 else ""

    return {
        "document_type": document_type,
        "country_code": country_code,
        "last_name": last_name,
        "first_name": first_name,
        "middle_names": middle_names if middle_names else None,
    }

def decode_mrz_line2(string2: str) -> dict:
    """Decode MRZ line 2 (TD3): passport number, dates, sex, personal number, check digits."""
    # Check digits as their position is already set (per ICAO 9303)
    NUMBER_CHECK_DIGIT_POS = 9
    BIRTH_DATE_CHECK_DIGIT_POS = 19
    EXPIRATION_DATE_CHECK_DIGIT_POS = 27
    PERSONAL_NUMBER_CHECK_DIGIT_POS = 43

    passport_number = string2[0:9].replace("<", "").strip()
    passport_number_check_digit = string2[NUMBER_CHECK_DIGIT_POS]
    country_code_2 = string2[10:13]
    birth_date = string2[13:19]
    birth_date_check_digit = string2[BIRTH_DATE_CHECK_DIGIT_POS]
    sex = string2[20]
    expiration_date = string2[21:27]
    expiration_date_check_digit = string2[EXPIRATION_DATE_CHECK_DIGIT_POS]
    personal_number = string2[28:42].replace("<", "").strip()
    personal_number_check_digit = string2[PERSONAL_NUMBER_CHECK_DIGIT_POS]

    return {
        "passport_number": passport_number,
        "passport_number_check_digit": passport_number_check_digit,
        "country_code_2": country_code_2,
        "birth_date": birth_date,
        "birth_date_check_digit": birth_date_check_digit,
        "sex": sex,
        "expiration_date": expiration_date,
        "expiration_date_check_digit": expiration_date_check_digit,
        "personal_number": personal_number,
        "personal_number_check_digit": personal_number_check_digit,
    }

def decode_mrz_strings(string1: str, string2: str):
    line1 = decode_mrz_line1(string1)
    line2 = decode_mrz_line2(string2)
    return {**line1, **line2}

def encode_mrz_strings(data: dict):
    """Encode MRZ lines from a data dictionary (queried from a database)."""
    doc_type = (data.get("document_type") or "")
    issuing_state = (data.get("country_code") or "")
    last_name = (data.get("last_name") or "").replace(" ", "<")
    first_name = (data.get("first_name") or "").replace(" ", "<")
    middle_names = (data.get("middle_names") or "")
    middle_block = ("<" + middle_names.replace(" ", "<")) if middle_names else ""

    # TD3 line 1 format: P< + issuing_state + surname<<given_names + fillers to 44 chars
    line1_core = f"{doc_type}<" f"{issuing_state}" f"{last_name}<<" f"{first_name}{middle_block}"

    # Pad with '<' to exactly 44 characters; if longer, truncate to 44
    if len(line1_core) < 44:
        line1 = line1_core + "<" * (44 - len(line1_core))
    else:
        line1 = line1_core[:44]

    # TD3 line 2 format: passport_number (9 chars) + issuing_state (3 chars) +
    # birth_date (6 chars) + sex (1 char) + expiration_date (6 chars) +
    # personal_number (14 chars) + fillers to 44 chars
    passport_number = (data.get("passport_number") or "").ljust(9, "<")[:9]
    passport_number_check_digit = calculate_check_digit(passport_number)
    country_code_2 = (data.get("country_code") or "").ljust(3, "<")[:3]
    birth_date = (data.get("birth_date") or "").ljust(6, "<")[:6]
    birth_date_check_digit = calculate_check_digit(birth_date)
    sex = (data.get("sex"))[:1]
    expiration_date = (data.get("expiration_date") or "").ljust(6, "<")[:6]
    expiration_date_check_digit = calculate_check_digit(expiration_date)
    personal_number = (data.get("personal_number") or "").ljust(14, "<")[:14]
    personal_number_check_digit = calculate_check_digit(personal_number)
    # Ensure the last character of line2 is the personal number check digit.
    # Insert exactly as much filler as needed BEFORE the check digit so total length is 44.
    prefix_len = (
        len(passport_number) + 1 +  # passport check
        len(country_code_2) +
        len(birth_date) + 1 +       # birth date check
        len(sex) +
        len(expiration_date) + 1 +  # expiration date check
        len(personal_number)
    )
    filler_count = max(0, 44 - (prefix_len + 1))  # +1 for the final personal check digit
    fillers = "<" * filler_count

    line2 = (f"{passport_number}"
             f"{passport_number_check_digit}"
             f"{country_code_2}"
             f"{birth_date}"
             f"{birth_date_check_digit}"
             f"{sex}"
             f"{expiration_date}"
             f"{expiration_date_check_digit}"
             f"{personal_number}"
             f"{fillers}"
             f"{personal_number_check_digit}")

    return line1, line2

def calculate_check_digit(field: str) -> int:
    import luhn

    alphabet_dict = {chr(i + 87): i for i in range(10, 36)}

    digits_only = []
    # For each letter found, follow the ICAO standard and replace it by its value between 10 - 35
    for ch in field:
        if ch.isdigit():
            digits_only.append(ch)
        elif ch.isalpha():
            digits_only.append(str(alphabet_dict[ch.lower()]))
        elif ch == '<':
            digits_only.append('0')

    numeric_str = "".join(digits_only)

    import luhn

    return luhn.generate(numeric_str)

def report_digit_mismatch(field_input: str, expected_checksum: str) -> bool:
    return calculate_check_digit(field_input) != int(expected_checksum)


print(decode_mrz_strings("P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<",
                   "L898902C36UTO7408122F1204159ZE184226B<<<<<<1"))

print(encode_mrz_strings({
    "document_type": "P",
    "country_code": "UTO",
    "last_name": "ERIKSSON",
    "first_name": "ANNA",
    "middle_names": "MARIA",
    "passport_number": "L898902C3",
    "birth_date": "740812",
    "sex": "F",
    "expiration_date": "120415",
    "personal_number": "ZE184226B"
}))
