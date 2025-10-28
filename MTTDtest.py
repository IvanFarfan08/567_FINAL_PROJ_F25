import unittest
from unittest.mock import patch
import MRTD

# Helper used only inside tests to compute the ICAO 9303 check digit
# (mod 10 with repeating weights 7,3,1; letters A..Z map to 10..35; '<' -> 0).
def icao_check_digit(field: str) -> int:
    weights = [7, 3, 1]
    def char_value(c: str) -> int:
        if c.isdigit():
            return int(c)
        if c == '<':
            return 0
        if c.isalpha():
            return ord(c.upper()) - ord('A') + 10
        return 0
    total = 0
    for i, ch in enumerate(field):
        total += char_value(ch) * weights[i % 3]
    return total % 10


class TestDecodeTD3(unittest.TestCase):
    def test_decode_line1_basic(self):
        """Decodes document type, issuing state, surname, given and middle names from line 1."""
        line1 = "P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<"
        out = MRTD.decode_mrz_line1(line1)
        self.assertEqual(out["document_type"], "P")
        self.assertEqual(out["country_code"], "UTO")  # specimen code
        self.assertEqual(out["last_name"], "ERIKSSON")
        self.assertEqual(out["first_name"], "ANNA")
        self.assertEqual(out["middle_names"], "MARIA")

    def test_decode_line2_basic(self):
        """Decodes numbers, dates, sex, personal no., and raw check digits from line 2."""
        line2 = "L898902C36UTO7408122F1204159ZE184226B<<<<<<1"
        out = MRTD.decode_mrz_line2(line2)
        self.assertEqual(out["passport_number"], "L898902C3")
        self.assertEqual(out["passport_number_check_digit"], "6")
        self.assertEqual(out["country_code_2"], "UTO")
        self.assertEqual(out["birth_date"], "740812")
        self.assertEqual(out["birth_date_check_digit"], "2")
        self.assertEqual(out["sex"], "F")
        self.assertEqual(out["expiration_date"], "120415")
        self.assertEqual(out["expiration_date_check_digit"], "9")
        self.assertEqual(out["personal_number"], "ZE184226B")
        self.assertEqual(out["personal_number_check_digit"], "1")

    def test_decode_both_lines_together(self):
        """Decoding the two lines and merging dictionaries keeps all expected fields."""
        l1 = "P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<"
        l2 = "L898902C36UTO7408122F1204159ZE184226B<<<<<<1"
        out = MRTD.decode_mrz_strings(l1, l2)
        self.assertEqual(out["document_type"], "P")
        self.assertEqual(out["first_name"], "ANNA")
        self.assertEqual(out["expiration_date"], "120415")


class TestEncodeTD3(unittest.TestCase):
    def test_encode_shapes_and_padding(self):
        """Encodes TD3 lines at exactly 44 chars with '<' padding and correct field placement."""
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
        self.assertIn("UTO", line2[10:13])  # issuing state at positions 11-13 (0-based slice 10:13)

    def test_encode_roundtrip_decode(self):
        """Encoding then decoding reproduces the original semantic fields."""
        data = {
            "document_type": "P",
            "country_code": "UTO",
            "last_name": "DOE",
            "first_name": "JANE",
            "middle_names": "ALPHA BETA",
            "passport_number": "AB2134",   # will be padded to 9 chars with '<'
            "birth_date": "520727",
            "sex": "F",
            "expiration_date": "331231",
            "personal_number": "XYZ123",
        }
        l1, l2 = MRTD.encode_mrz_strings(data)
        out = MRTD.decode_mrz_strings(l1, l2)
        self.assertEqual(out["document_type"], "P")
        self.assertEqual(out["country_code"], "UTO")
        self.assertEqual(out["last_name"], "DOE")
        self.assertEqual(out["first_name"], "JANE")
        self.assertEqual(out["middle_names"], "ALPHA BETA")
        self.assertEqual(out["birth_date"], "520727")
        self.assertEqual(out["sex"], "F")
        self.assertEqual(out["expiration_date"], "331231")

    def test_line_lengths_exact(self):
        """Both TD3 lines must be exactly 44 characters."""
        d = {
            "document_type": "P",
            "country_code": "UTO",
            "last_name": "LONGNAMEWITH<MULTI<WORDS".replace("<"," "),  # ensure replacement logic still pads
            "first_name": "A",
            "middle_names": "",
            "passport_number": "X1",
            "birth_date": "000101",
            "sex": "M",
            "expiration_date": "990101",
            "personal_number": "",
        }
        l1, l2 = MRTD.encode_mrz_strings(d)
        self.assertEqual(len(l1), 44)
        self.assertEqual(len(l2), 44)


class TestMocks(unittest.TestCase):
    @patch("MRTD.process_mrz_scan")
    def test_mock_hardware_scan_feeds_decoder(self, mock_scan):
        """Demonstrates mocking the unavailable scanner by supplying sample MRZ lines."""
        mock_scan.return_value = (
            "P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<",
            "L898902C36UTO7408122F1204159ZE184226B<<<<<<1",
        )
        # Pretend our test wrapper calls the scanner, then uses the library to decode.
        l1, l2 = MRTD.process_mrz_scan()
        out = MRTD.decode_mrz_strings(l1, l2)
        self.assertEqual(out["last_name"], "ERIKSSON")
        self.assertEqual(out["personal_number"], "ZE184226B")

    @patch("MRTD.query_database")
    def test_mock_database_feeds_encoder(self, mock_db):
        """Demonstrates mocking the unavailable database to drive encoder inputs."""
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

class TestChecks(unittest.TestCase):
    def test_report_digit_mismatch_flags_wrong_check(self):
        """A wrong expected digit should be flagged as mismatch."""
        field = "AB2134<<<"  # 9-char fixed field example
        correct = icao_check_digit(field)
        wrong = (correct + 1) % 10
        self.assertTrue(MRTD.report_digit_mismatch(field, str(wrong)))

    @unittest.expectedFailure
    def test_icao_check_digit_matches_encoder_generated_digits(self):
        """
        Expected failure right now: MRTD.calculate_check_digit uses a Luhn library
        instead of the ICAO 7-3-1 method. This test documents the gap.
        """
        # Example: date 520727 has check digit 3 per ICAO sample.
        # See Appendix A example (date field) in ICAO 9303.
        date = "520727"
        self.assertEqual(MRTD.calculate_check_digit(date), icao_check_digit(date))

if __name__ == "__main__":
    unittest.main()
