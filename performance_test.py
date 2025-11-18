"""
Performance testing script for MRTD.py
Measures execution times with and without test assertions for varying record counts
Tests both encoding and decoding operations
Made with partial help from ChatGPT
"""
import json
import csv
import time
import unittest
import sys
from io import StringIO
from MRTD import encode_mrz_strings, decode_mrz_strings


def encode_record(record):
    record_data = {
        "document_type": "P",
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

    line1, line2 = encode_mrz_strings(record_data)
    return f"{line1};{line2}"


def decode_record(encoded_record):
    # Split the encoded record by semicolon
    parts = encoded_record.split(';')

    line1, line2 = parts[0], parts[1]
    decoded = decode_mrz_strings(line1, line2)
    return decoded


def measure_encoding_time_without_tests(records, n_records):
    """Measure time to encode n_records without running tests"""
    start_time = time.perf_counter()

    for i in range(n_records):
        encode_record(records[i])

    end_time = time.perf_counter()
    elapsed_time = end_time - start_time

    return elapsed_time


def measure_encoding_time_with_tests(records, n_records):
    """Measure time to encode n_records AND run the full unittest suite"""
    start_time = time.perf_counter()

    # Encode the records
    for i in range(n_records):
        encode_record(records[i])

    # Run the full unittest from test_MRTD.py
    test_output = StringIO()
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromName('test_MRTD')
    runner = unittest.TextTestRunner(stream=test_output, verbosity=0)
    runner.run(suite)

    end_time = time.perf_counter()
    elapsed_time = end_time - start_time

    return elapsed_time


def measure_decoding_time_without_tests(encoded_records, n_records):
    """Measure time to decode n_records without running tests"""
    start_time = time.perf_counter()

    for i in range(n_records):
        decode_record(encoded_records[i])

    end_time = time.perf_counter()
    elapsed_time = end_time - start_time

    return elapsed_time


def measure_decoding_time_with_tests(encoded_records, n_records):
    """Measure time to decode n_records AND run the full unittest suite"""
    start_time = time.perf_counter()

    # Decode the records
    for i in range(n_records):
        decode_record(encoded_records[i])

    # Run the full unittest from test_MRTD.py
    test_output = StringIO()
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromName('test_MRTD')
    runner = unittest.TextTestRunner(stream=test_output, verbosity=0)
    runner.run(suite)

    end_time = time.perf_counter()
    elapsed_time = end_time - start_time

    return elapsed_time


def run_performance_tests():
    """Run performance tests for both encoding and decoding"""
    # Load decoded records for encoding tests
    print("Loading decoded records for encoding tests...")
    with open('records_decoded.json', 'r') as f:
        data = json.load(f)
    decoded_records = data['records_decoded']

    # Load encoded records for decoding tests
    print("Loading encoded records for decoding tests...")
    with open('records_encoded.json', 'r') as f:
        data = json.load(f)
    encoded_records = data['records_encoded']

    # Define test sizes: 100, 1000, 2000, ..., 10000
    test_sizes = [100] + list(range(1000, 11000, 1000))

    results = []

    print("\nRunning performance tests...")
    print("=" * 70)

    for n in test_sizes:
        print(f"\nTesting with {n} records...")

        # ENCODING TESTS
        print(f"  Encoding without tests...")
        time_encode_no_tests = measure_encoding_time_without_tests(decoded_records, n)

        print(f"  Encoding with tests...")
        time_encode_with_tests = measure_encoding_time_with_tests(decoded_records, n)

        # DECODING TESTS
        print(f"  Decoding without tests...")
        time_decode_no_tests = measure_decoding_time_without_tests(encoded_records, n)

        print(f"  Decoding with tests...")
        time_decode_with_tests = measure_decoding_time_with_tests(encoded_records, n)

        results.append({
            'n_records': n,
            'encode_no_tests': time_encode_no_tests,
            'encode_with_tests': time_encode_with_tests,
            'decode_no_tests': time_decode_no_tests,
            'decode_with_tests': time_decode_with_tests
        })

        print(f"  Encode without tests: {time_encode_no_tests:.4f}s | with tests: {time_encode_with_tests:.4f}s")
        print(f"  Decode without tests: {time_decode_no_tests:.4f}s | with tests: {time_decode_with_tests:.4f}s")

    # Save results to CSV
    print("\nSaving results to performance_results.csv...")
    with open('performance_results.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Records', 'Encode_No_Tests', 'Encode_With_Tests', 'Decode_No_Tests', 'Decode_With_Tests'])
        for result in results:
            writer.writerow([
                result['n_records'],
                f"{result['encode_no_tests']:.6f}",
                f"{result['encode_with_tests']:.6f}",
                f"{result['decode_no_tests']:.6f}",
                f"{result['decode_with_tests']:.6f}"
            ])

    print("\nPerformance testing complete!")
    print(f"Tested {len(test_sizes)} different record counts")
    print("Results saved to performance_results.csv")


if __name__ == "__main__":
    run_performance_tests()
