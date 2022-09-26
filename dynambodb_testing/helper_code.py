""" Example code to send data to the App to be added to the database """
import json
import requests
from cryptography.fernet import Fernet

DATA_JSON = {
    "updated_at": "2022-08-22 15:28:53",
    "data": [
        {
            "name": "cloud-platform",
            "default_branch": "main",
            "url": "https://github.com/ministryofjustice/cloud-platform",
            "status": "PASS",
            "last_push": "2022-02-01",
            "report": {
                "default_branch_main": True,
                "has_default_branch_protection": True,
                "requires_approving_reviews": True,
                "administrators_require_review": True,
                "issues_section_enabled": True,
                "requires_code_owner_reviews": True,
                "has_require_approvals_enabled": True,
            },
            "issues_enabled": True,
        },
        {
            "name": "cloud-platform-infrastructure",
            "default_branch": "main",
            "url": "https://github.com/ministryofjustice/cloud-platform-infrastructure",
            "status": "PASS",
            "last_push": "2022-02-01",
            "report": {
                "default_branch_main": True,
                "has_default_branch_protection": True,
                "requires_approving_reviews": True,
                "administrators_require_review": True,
                "issues_section_enabled": True,
                "requires_code_owner_reviews": True,
                "has_require_approvals_enabled": True,
            },
            "issues_enabled": True,
        },
        {
            "name": "aws-root-account",
            "default_branch": "main",
            "url": "https://github.com/ministryofjustice/aws-root-account",
            "status": "PASS",
            "last_push": "2022-02-01",
            "report": {
                "default_branch_main": True,
                "has_default_branch_protection": True,
                "requires_approving_reviews": True,
                "administrators_require_review": True,
                "issues_section_enabled": True,
                "requires_code_owner_reviews": True,
                "has_require_approvals_enabled": True,
            },
            "issues_enabled": True,
        },
        {
            "name": "record-a-goose-sighting",
            "default_branch": "master",
            "url": "https://github.com/ministryofjustice/record-a-goose-sighting",
            "status": "FAIL",
            "last_push": "2021-04-15",
            "report": {
                "default_branch_main": False,
                "has_default_branch_protection": True,
                "requires_approving_reviews": True,
                "administrators_require_review": True,
                "issues_section_enabled": True,
                "requires_code_owner_reviews": True,
                "has_require_approvals_enabled": True,
            },
            "issues_enabled": True,
        },
        {
            "name": "fab-oidc",
            "default_branch": "main",
            "url": "https://github.com/ministryofjustice/fab-oidc",
            "status": "PASS",
            "last_push": "2021-01-15",
            "report": {
                "default_branch_main": True,
                "has_default_branch_protection": True,
                "requires_approving_reviews": True,
                "administrators_require_review": True,
                "issues_section_enabled": True,
                "requires_code_owner_reviews": True,
                "has_require_approvals_enabled": True,
            },
            "issues_enabled": True,
        },
        {
            "name": "technical-guidance",
            "default_branch": "main",
            "url": "https://github.com/ministryofjustice/technical-guidance",
            "status": "FAIL",
            "last_push": "2022-02-01",
            "report": {
                "default_branch_main": True,
                "has_default_branch_protection": True,
                "requires_approving_reviews": True,
                "administrators_require_review": True,
                "issues_section_enabled": True,
                "requires_code_owner_reviews": False,
                "has_require_approvals_enabled": True,
            },
            "issues_enabled": True,
        },
        {
            "name": "peoplefinder",
            "default_branch": "main",
            "url": "https://github.com/ministryofjustice/peoplefinder",
            "status": "FAIL",
            "last_push": "2022-01-28",
            "report": {
                "default_branch_main": True,
                "has_default_branch_protection": True,
                "requires_approving_reviews": True,
                "administrators_require_review": False,
                "issues_section_enabled": True,
                "requires_code_owner_reviews": False,
                "has_require_approvals_enabled": True,
            },
            "issues_enabled": True,
        },
        {
            "name": "govuk-bank-holidays",
            "default_branch": "main",
            "url": "https://github.com/ministryofjustice/govuk-bank-holidays",
            "status": "FAIL",
            "last_push": "2022-01-24",
            "report": {
                "default_branch_main": True,
                "has_default_branch_protection": True,
                "requires_approving_reviews": True,
                "administrators_require_review": False,
                "issues_section_enabled": True,
                "requires_code_owner_reviews": True,
                "has_require_approvals_enabled": True,
            },
            "issues_enabled": True,
        },
        {
            "name": "analytics-platform-shiny-server",
            "default_branch": "main",
            "url": "https://github.com/ministryofjustice/analytics-platform-shiny-server",
            "status": "PASS",
            "last_push": "2022-01-14",
            "report": {
                "default_branch_main": True,
                "has_default_branch_protection": True,
                "requires_approving_reviews": True,
                "administrators_require_review": True,
                "issues_section_enabled": True,
                "requires_code_owner_reviews": True,
                "has_require_approvals_enabled": True,
            },
            "issues_enabled": True,
        },
        {
            "name": "modernisation-platform",
            "default_branch": "main",
            "url": "https://github.com/ministryofjustice/modernisation-platform",
            "status": "PASS",
            "last_push": "2022-02-01",
            "report": {
                "default_branch_main": True,
                "has_default_branch_protection": True,
                "requires_approving_reviews": True,
                "administrators_require_review": True,
                "issues_section_enabled": True,
                "requires_code_owner_reviews": True,
                "has_require_approvals_enabled": True,
            },
            "issues_enabled": True,
        },
        {
            "name": "bai2",
            "default_branch": "main",
            "url": "https://github.com/ministryofjustice/bai2",
            "status": "FAIL",
            "last_push": "2022-01-26",
            "report": {
                "default_branch_main": True,
                "has_default_branch_protection": True,
                "requires_approving_reviews": True,
                "administrators_require_review": False,
                "issues_section_enabled": True,
                "requires_code_owner_reviews": True,
                "has_require_approvals_enabled": True,
            },
            "issues_enabled": True,
        },
        {
            "name": "cloud-platform-environments",
            "default_branch": "main",
            "url": "https://github.com/ministryofjustice/cloud-platform-environments",
            "status": "PASS",
            "last_push": "2022-02-01",
            "report": {
                "default_branch_main": True,
                "has_default_branch_protection": True,
                "requires_approving_reviews": True,
                "administrators_require_review": True,
                "issues_section_enabled": True,
                "requires_code_owner_reviews": True,
                "has_require_approvals_enabled": True,
            },
            "issues_enabled": True,
        },
        {
            "name": "analytics-platform-ops",
            "default_branch": "main",
            "url": "https://github.com/ministryofjustice/analytics-platform-ops",
            "status": "FAIL",
            "last_push": "2022-01-21",
            "report": {
                "default_branch_main": False,
                "has_default_branch_protection": True,
                "requires_approving_reviews": True,
                "administrators_require_review": True,
                "issues_section_enabled": True,
                "requires_code_owner_reviews": True,
                "has_require_approvals_enabled": True,
            },
            "issues_enabled": True,
        },
        {
            "name": "moj-frontend",
            "default_branch": "main",
            "url": "https://github.com/ministryofjustice/moj-frontend",
            "status": "PASS",
            "last_push": "2022-01-31",
            "report": {
                "default_branch_main": True,
                "has_default_branch_protection": True,
                "requires_approving_reviews": True,
                "administrators_require_review": True,
                "issues_section_enabled": True,
                "requires_code_owner_reviews": True,
                "has_require_approvals_enabled": True,
            },
            "issues_enabled": True,
        },
    ],
}


def example_encrypt_decrypt():
    """Example of creating a key, encrypt and decrypt some data"""
    # key_byte = b"ZRc1sygKdVJbQhVejPJnK8jIYTB6boD6V1Qe1SJL1ew="
    # key_hex = "5a5263317379674b64564a62516856656a504a6e4b386a4959544236626f44365631516531534a4c3165773d"
    key_byte = Fernet.generate_key()
    key_hex = key_byte.hex()
    key_from_hex_as_bytes = bytes.fromhex(key_hex)
    if key_from_hex_as_bytes == key_byte:
        print("matches")
    fernet = Fernet(key_from_hex_as_bytes)
    token = fernet.encrypt(b"A really secret message. Not for prying eyes.")
    print(token)
    message = fernet.decrypt(token)
    print(message.decode("utf-8"))


def decrypt_data(encrypted_data_bytes_as_string):
    """decrypt provided data

    Args:
        encrypted_data_bytes_as_string (string): encrypted data

    Returns:
        json: plain data
    """
    key_hex = "5a5263317379674b64564a62516856656a504a6e4b386a4959544236626f44365631516531534a4c3165773d"
    key = bytes.fromhex(key_hex)
    fernet = Fernet(key)
    encrypted_data_as_bytes = encrypted_data_bytes_as_string.encode()
    decrypted_data_as_bytes = fernet.decrypt(encrypted_data_as_bytes)
    data_as_string = decrypted_data_as_bytes.decode()
    data = json.loads(data_as_string)
    return data


def encrypt_json(plain_data):
    """encrypt provided data

    Args:
        plain_data (): plain text data

    Returns:
        string: encrypted data
    """
    key_hex = "5a5263317379674b64564a62516856656a504a6e4b386a4959544236626f44365631516531534a4c3165773d"
    key = bytes.fromhex(key_hex)
    fernet = Fernet(key)
    data_as_string = json.dumps(plain_data)
    data_as_bytes = data_as_string.encode()
    encrypted_data_as_bytes = fernet.encrypt(data_as_bytes)
    encrypted_data_bytes_as_string = encrypted_data_as_bytes.decode()
    return encrypted_data_bytes_as_string


def encrypt_decrypt_data():
    """encrypt and decrypt data"""
    data_json = {
        "updated_at": "2022-08-22 15:28:53",
        "data": [],
    }
    data_json["data"] = encrypt_json(DATA_JSON["data"])
    data_json["data"] = decrypt_data(data_json["data"])
    if data_json["data"] == DATA_JSON["data"]:
        print("data matches")
    else:
        print("data doesn't match")


def send_encrypted_data_to_server():
    """Replicate sending encrypted data to the App"""
    # url = "http://127.0.0.1:80/update_private_repositories"
    url = "http://127.0.0.1:4567/update_private_repositories"
    headers = {"Content-Type": "application/json", "X-API-KEY": "default123"}
    data_json = encrypt_json(DATA_JSON)
    requests.post(url, headers=headers, json=data_json, timeout=1.5)


def send_data_to_server():
    """Replicate sending plain text data to the App"""
    url = "http://127.0.0.1:80/update_private_repositories"
    # url = "http://127.0.0.1:4567/update_private_repositories"
    headers = {"Content-Type": "application/json", "X-API-KEY": "default123"}
    requests.post(url, headers=headers, json=DATA_JSON, timeout=1.5)


def main():
    """
    Main function
    """
    print("-" * 88)
    print("Start")

    example_encrypt_decrypt()
    # encrypt_decrypt_data()
    # send_data_to_server()
    # send_encrypted_data_to_server()

    print("Finished")
    print("-" * 88)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # pylint: disable=broad-except
        print(f"help_code.py: Something went wrong. Here's what: {e}")
