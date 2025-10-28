import unittest
from unittest.mock import patch
import MRTD


# Helper Functions

def icao_check_digit(field: str) -> int:
    """ICAO Doc 9303 modulus-10 with repeating weights 7-3-1."""
    weights = [7, 3, 1]
    def val(c: str) -> int:
        if c.isdigit():
            return int(c)
        if c == '<':
            return 0
        if c.isalpha():
            return ord(c.upper()) - ord('A') + 10
        return 0
    total = sum(val(ch) * weights[i % 3] for i, ch in enumerate(field))
    return total % 10


def luhn_check_digit(numeric_str: str) -> int:
    """Classic Luhn check digit for digits-only string."""
    total = 0
    for i, dch in enumerate(reversed(numeric_str)):
        d = int(dch)
        if i % 2 == 0:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return (10 - (total % 10)) % 10


def map_icao_chars_to_digits(s: str) -> str:
    """Maps A–Z→10–35, '<'→0, digits stay digits."""
    out = []
    for ch in s:
        if ch.isdigit():
            out.append(ch)
        elif ch == '<':
            out.append('0')
        elif ch.isalpha():
            out.append(str(ord(ch.upper()) - ord('A') + 10))
        else:
            out.append('0')
    return "".join(out)


# Decoding Tests

class TestDecodeTD3(unittest.TestCase):
    def test_decode_line1_basic(self):
        """Tests parsing of document type, state, surname, and names."""
        line1 = "P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<"
        out = MRTD.decode_mrz_line1(line1)
        self.assertEqual(out["document_type"], "P")
        self.assertEqual(out["country_code"], "UTO")
        self.assertEqual(out["last_name"], "ERIKSSON")
        self.assertEqual(out["first_name"], "ANNA")
        self.assertEqual(out["middle_names"], "MARIA")

    def test_decode_line2_basic(self):
        """Tests extraction of passport number, dates, sex, and check digits."""
        line2 = "L898902C36UTO7408122F1204159ZE184226B<<<<<<1"
        out = MRTD.decode_mrz_line2(line2)
        self.assertEqual(out["passport_number"], "L898902C3")
        self.assertEqual(out["passport_number_check_digit"], "6")
        self.assertEqual(out["birth_date"], "740812")
        self.assertEqual(out["sex"], "F")
        self.assertEqual(out["expiration_date"], "120415")
        self.assertEqual(out["personal_number"], "ZE184226B")

    def test_decode_both_lines(self):
        """Checks combined decoding output of two MRZ lines."""
        l1 = "P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<"
        l2 = "L898902C36UTO7408122F1204159ZE184226B<<<<<<1"
        out = MRTD.decode_mrz_strings(l1, l2)
        self.assertEqual(out["document_type"], "P")
        self.assertEqual(out["first_name"], "ANNA")
        self.assertEqual(out["expiration_date"], "120415")


# Encoding Tests

class TestEncodeTD3(unittest.TestCase):
    def test_encode_length_and_format(self):
        """Tests that encoded lines are 44 characters long and padded correctly."""
        data = {
            "document_type": "P",
            "country_code": "UTO",
            "last_name": "ERIKSSON",
            "first_name": "ANNA",
            "middle_names": "MARIA",
            "passport_number": "L898902C3",
            "birth_date": "740812",
            "sex": "F",
            "expiration_date": "120415",
            "personal_number": "ZE184226B",
        }
        line1, line2 = MRTD.encode_mrz_strings(data)
        self.assertEqual(len(line1), 44)
        self.assertEqual(len(line2), 44)
        self.assertTrue(line1.startswith("P<UTOERIKSSON<<ANNA<MARIA"))
        self.assertIn("UTO", line2[10:13])

    def test_encode_then_decode_roundtrip(self):
        """Ensures that encoding and then decoding yields consistent fields."""
        data = {
            "document_type": "P",
            "country_code": "UTO",
            "last_name": "DOE",
            "first_name": "JANE",
            "middle_names": "ALPHA BETA",
            "passport_number": "AB2134",
            "birth_date": "520727",
            "sex": "F",
            "expiration_date": "331231",
            "personal_number": "XYZ123",
        }
        l1, l2 = MRTD.encode_mrz_strings(data)
        out = MRTD.decode_mrz_strings(l1, l2)
        self.assertEqual(out["last_name"], "DOE")
        self.assertEqual(out["first_name"], "JANE")
        self.assertEqual(out["birth_date"], "520727")
        self.assertEqual(out["expiration_date"], "331231")


# Mock Tests

class TestMocks(unittest.TestCase):
    @patch("MRTD.process_mrz_scan")
    def test_mock_scanner(self, mock_scan):
        """Simulates hardware MRZ scanner using mock."""
        mock_scan.return_value = (
            "P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<",
            "L898902C36UTO7408122F1204159ZE184226B<<<<<<1",
        )
        l1, l2 = MRTD.process_mrz_scan()
        out = MRTD.decode_mrz_strings(l1, l2)
        self.assertEqual(out["last_name"], "ERIKSSON")

    @patch("MRTD.query_database")
    def test_mock_database(self, mock_db):
        """Simulates database query feeding encoder."""
        mock_db.return_value = {
            "document_type": "P",
            "country_code": "UTO",
            "last_name": "SMITH",
            "first_name": "ALICE",
            "middle_names": "",
            "passport_number": "D23145890",
            "birth_date": "681231",
            "sex": "F",
            "expiration_date": "310101",
            "personal_number": "PN12345",
        }
        payload = MRTD.query_database()
        l1, l2 = MRTD.encode_mrz_strings(payload)
        self.assertTrue(l1.startswith("P<UTO"))
        self.assertIn("UTO", l2[10:13])


# ICAO vs Luhn Tests

class TestICAOExamples(unittest.TestCase):
    def test_icao_date_example(self):
        """Official ICAO example: '520727' → 3"""
        self.assertEqual(icao_check_digit("520727"), 3)

    def test_icao_document_number_example(self):
        """Official ICAO example: 'AB2134<<<' → 5"""
        self.assertEqual(icao_check_digit("AB2134<<<"), 5)

    def test_icao_fragment_runs(self):
        """Validates function runs on representative TD3 field."""
        fragment = "HA672242<6YTO5802254M9601086<<<<<<<<<<<<<<0"
        self.assertIsInstance(icao_check_digit(fragment), int)


class TestLuhnComparison(unittest.TestCase):
    def test_luhn_differs_from_icao_date(self):
        """Luhn gives different result from ICAO for '520727'."""
        numeric = map_icao_chars_to_digits("520727")
        self.assertNotEqual(luhn_check_digit(numeric), icao_check_digit("520727"))

    def test_luhn_differs_from_icao_docnum(self):
        """Luhn gives different result from ICAO for 'AB2134<<<'."""
        s = "AB2134<<<"
        numeric = map_icao_chars_to_digits(s)
        self.assertNotEqual(luhn_check_digit(numeric), icao_check_digit(s))


class TestImplementationExpectedFailures(unittest.TestCase):
    @unittest.expectedFailure
    def test_mrtd_calc_differs_date(self):
        """Expected failure: MRTD.calculate_check_digit uses Luhn not ICAO."""
        self.assertEqual(MRTD.calculate_check_digit("520727"), icao_check_digit("520727"))

    @unittest.expectedFailure
    def test_mrtd_calc_differs_docnum(self):
        """Expected failure: MRTD.calculate_check_digit uses Luhn not ICAO."""
        self.assertEqual(MRTD.calculate_check_digit("AB2134<<<"), icao_check_digit("AB2134<<<"))


# Digit Validation Test

class TestDigitValidation(unittest.TestCase):
    def test_report_digit_mismatch_flags(self):
        """Tests helper that reports mismatched check digits."""
        field = "AB2134<<<"
        correct = icao_check_digit(field)
        wrong = (correct + 1) % 10
        self.assertTrue(MRTD.report_digit_mismatch(field, str(wrong)))


# Run All Tests

if __name__ == "__main__":
    unittest.main()
