#!/usr/bin/env python3
import os
import sys
import csv
import argparse
import requests

CREATE_APP_URL  =   "https://signifyd.okta.com/api/v1/apps"
ADD_APP_URL   =   "https://signifyd.okta.com/api/v1/apps/%s/groups/%s"


def get_html_header(api_token):
    return {
        'Content-type': 'application/json',
        'Accept': 'application/json',
        'Authorization': 'SSWS %s' % api_token
    }


def upload_payload(api_token, payload):
    headers = get_html_header(api_token)
    print('*' * 120)
    print("POSTING", CREATE_APP_URL, headers, payload)
    print('*' * 120)
    response = requests.post(CREATE_APP_URL, headers=headers, data=payload)
    print(response)
    print(response.headers)
    print(response.text)
    if response.status_code != 200:
        return ''
    return response.json()["id"]


def add_group(api_token, group_id, application_id):
    print('*' * 120)
    print("PUTting Group Chargeback-Team to Application Id:", application_id)
    print('*' * 120)
    headers = get_html_header(api_token)
    response = requests.put(ADD_APP_URL % (application_id, group_id), headers=headers)
    print(response)
    print(response.headers)
    print(response.text)


def add_creds_using_swa(api_token, group_id, label, admin_url, password):
    login_url = admin_url + "/auth/login"
    payload = """{
          "label": "%s",
          "visibility": {
            "autoSubmitToolbar": false,
            "hide": {
              "iOS": false,
              "web": false
            }
          },
          "features": [],
          "signOnMode": "AUTO_LOGIN",
          "settings": {
            "signOn": {
              "redirectUrl": "",
              "loginUrl": "%s"
            }
          },
          "credentials": {
            "scheme": "SHARED_USERNAME_AND_PASSWORD",
            "userNameTemplate": {
                "template": "${source.email}",
                "type": "BUILT_IN"
            },
            "userName": "chargebacks@signifyd.com",
            "password": {"value":"%s"}
          }
    }
    """ % (label, login_url, password)
    application_id = upload_payload(api_token, payload)
    if application_id:
        add_group(api_token, group_id, application_id)
    return application_id


def get_input_parser():
    """Input Details"""
    DESC = """
        Creates applications for each input credentials using SWA application
        """

    EXAMPLES = """
        eg:
        %(prog)s csv_file
        %(prog)s -g group csv_file
        %(prog)s -r results_file csv_file
        """

    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description=DESC,
                                     epilog=EXAMPLES)
    parser.add_argument('-g', '--group_id', help="Add App to be part of this group. Default Chargeback-Team",
                        default="00glw9acqnIlFCzCY0x7")
    parser.add_argument('-r', '--results_file', help="Store the results in results file. Default=created_apps.csv",
                        default="created_apps.csv")
    parser.add_argument('-hn', '--header_name', help="CSV header for name column. Default=Name",
                        default="Name")
    parser.add_argument('-hu', '--header_url', help="CSV header for Url column. Default=admin",
                        default="admin")
    parser.add_argument('-hp', '--header_password', help="CSV header for Password column. Default=pw",
                        default="admin")
    parser.add_argument('csv_file', help="CSV File containing credentials")
    if len(sys.argv) < 2:
        parser.parse_args(['-h'])
    return parser.parse_args()


def main():
    args = get_input_parser()
    print(args)
    if "OKTA_AUTH_TOKEN" not in os.environ or os.environ["OKTA_AUTH_TOKEN"] == '':
        print("Environment variable OKTA_AUTH_TOKEN needs to be set.")
        print("Please contact the IT team at ithelp@signifyd.com")
        sys.exit(1)
    api_token = os.environ["OKTA_AUTH_TOKEN"]
    with open(args.csv_file) as cf, open(args.results_file, 'w') as out:
        reader = csv.DictReader(cf)
        for row in reader:
            print("add_creds_using_swa", row[args.header_name], row[args.header_url], row[args.header_password])
            application_id = add_creds_using_swa(api_token, args.group_id, row[args.header_name], row[args.header_url],
                                                 row[args.header_password])
            if application_id:
                out.write(','.join([row[args.header_name], row[args.header_url], row[args.header_password],
                                    application_id]) + '\n')


if __name__ == "__main__":
    main()
