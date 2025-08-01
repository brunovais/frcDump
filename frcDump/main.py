import os
import sys
import subprocess
import xml.etree.ElementTree as ET
import shutil
import requests
import argparse
import json
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

banner = """
                 (    
  __              )\ )   (      )       
 / _|            (()/(  ))\    (     `  ) 
| |_ _ __ ___    ((_))  /((_)   )\  ' /(/( 
|  _| '__/ __|   _| |(_))(  _((_)) ((_)_\ 
| | | | | (__  / _` || || || '  \()| '_ \) 
|_| |_|  \___| \__,_| \_,_||_|_|_| | .__/  
                                   |_|   

        by @brunovais and @phor3nsic
"""

def print_readable(data, indent=0):
    for key, value in data.items():
        prefix = '  ' * indent + f"- {key}: "
        if isinstance(value, dict):
            print(f"{prefix}")
            print_readable(value, indent + 1)
        elif isinstance(value, list):
            print(f"{prefix}[")
            for item in value:
                if isinstance(item, dict):
                    print_readable(item, indent + 2)
                else:
                    print("  " * (indent + 2) + f"- {item}")
            print("  " * indent + "]")
        else:
            print(f"{prefix}{value}")

def get_web_config(google_api_key, app_id):
    url = f"https://firebase.googleapis.com/v1alpha/projects/-/apps/{app_id}/webConfig"
    headers = {
        "X-Goog-Api-Key": google_api_key,
        "Content-Type": "application/json"
    }
    req = requests.get(url, headers=headers)
    if req.status_code == 200:
        print("Response received...")
        return req.json()
    else:
        print(f"Error in response, status_code {req.status_code}")
        sys.exit()

def get_remote_config(google_api_key, app_id):
    app_instance_id = "XD"
    project_id = app_id.split(":")[1]
    url = f"https://firebaseremoteconfig.googleapis.com:443/v1/projects/{project_id}/namespaces/firebase:fetch"

    headers = {
        "X-Goog-Api-Key": google_api_key,
        "Content-Type": "application/json"
    }

    stripped_app_id = app_id.split(":")
    new_app_id = f"0:{project_id}:android:{stripped_app_id[3]}"

    data_json = {
        "appId": new_app_id,
        "appInstanceId": app_instance_id
    }

    req = requests.post(url, headers=headers, json=data_json)

    if req.status_code == 200:
        print("Response received...")
        return req.json()
    else:
        print(f"Error in response, status_code {req.status_code}")
        sys.exit()


def decode_apk_with_apktool(apk_path):
    print(f"[+] APK received: {apk_path}")

    if not os.path.isfile(apk_path):
        print("[-] Invalid path.")
        return None

    apk_dir = os.path.dirname(os.path.abspath(apk_path))
    apk_filename = os.path.basename(apk_path)
    apk_name = os.path.splitext(apk_filename)[0]

    output_dir = os.path.join(apk_dir, f"{apk_name}_decoded")

    if os.path.exists(output_dir):
        print(f"[!] Directory {output_dir} already exists. Removing...")
        shutil.rmtree(output_dir)

    print(f"[+] Decompiling with apktool into: {output_dir}")
    try:
        subprocess.run(["apktool", "d", "-f", apk_path, "-o", output_dir], check=True)
    except subprocess.CalledProcessError as e:
        print(f"[-] Failed to run apktool: {e}")
        return None

    return output_dir


def search_in_strings(root):
    api_key = None
    app_id = None
    for string in root.findall("string"):
        name = string.get("name")
        if name == "google_api_key":
            api_key = string.text
            print(f"[+] Found google_api_key: {api_key}")
        elif name == "google_app_id":
            app_id = string.text
            print(f"[+] Found google_app_id: {app_id}")
    return api_key, app_id


def search_in_files(output_dir):
    print("[+] Searching all .xml files for google_api_key and google_app_id...")
    api_key = None
    app_id = None

    for root_dir, _, files in os.walk(output_dir):
        for file in files:
            if file.endswith(".xml"):
                full_path = os.path.join(root_dir, file)
                try:
                    tree = ET.parse(full_path)
                    root = tree.getroot()
                    k, a = search_in_strings(root)
                    if k and not api_key:
                        api_key = k
                    if a and not app_id:
                        app_id = a
                    if api_key and app_id:
                        return api_key, app_id
                except Exception:
                    continue  # skip invalid XMLs

    return api_key, app_id


def search_in_manifest(manifest_path):
    print(f"[+] Analyzing AndroidManifest.xml: {manifest_path}")
    try:
        tree = ET.parse(manifest_path)
        root = tree.getroot()

        app_id = None
        for elem in root.iter("meta-data"):
            name = elem.attrib.get('{http://schemas.android.com/apk/res/android}name')
            value = elem.attrib.get('{http://schemas.android.com/apk/res/android}value')
            if name == "google_app_id":
                print(f"[+] Found google_app_id in Manifest: {value}")
                app_id = value
        return app_id
    except Exception as e:
        print(f"[-] Failed to parse AndroidManifest.xml: {e}")
        return None


def extract_google_vars(apk_path):
    output_dir = decode_apk_with_apktool(apk_path)
    if not output_dir:
        return None

    api_key = None
    app_id = None

    strings_path = os.path.join(output_dir, "res", "values", "strings.xml")
    if os.path.exists(strings_path):
        print(f"[+] Analyzing default strings.xml at: {strings_path}")
        try:
            tree = ET.parse(strings_path)
            root = tree.getroot()
            api_key, app_id = search_in_strings(root)
        except Exception as e:
            print(f"[-] Failed to parse default strings.xml: {e}")

    if not api_key or not app_id:
        k, a = search_in_files(output_dir)
        api_key = api_key or k
        app_id = app_id or a

    if not app_id:
        manifest_path = os.path.join(output_dir, "AndroidManifest.xml")
        if os.path.exists(manifest_path):
            app_id_manifest = search_in_manifest(manifest_path)
            if app_id_manifest:
                app_id = app_id_manifest

    return {
        "google_api_key": api_key,
        "google_app_id": app_id
    }


def main():
    
    parser = argparse.ArgumentParser(description="Firebase RemoteConfig Dump", add_help=True)
    parser.add_argument("--apk", help="Path of apk file. Ex: /path/of/apk/file.apk")
    parser.add_argument("-id","--appid", help="Search remote config by appid. Ex: 0:123455776998:android:123c123a1234f1234ff1a1")
    parser.add_argument("-k", "--apikey", help="Google Api Key. Ex: AIzaxxxxxx")
    parser.add_argument("--silent", action="store_true", help="Silent mode, no output banner.")
    args = parser.parse_args()
    
    if not(args.silent):
        print(banner)
        print("\n\n")

    if args.apk:
        if shutil.which("apktool") is None:
            print("[-] 'apktool' was not found on your system.")
            print("\nInstallation Instructions:")
            print("1. Download the latest version from: https://bitbucket.org/iBotPeaches/apktool/downloads/")
            print("2. Rename the file to 'apktool.jar' and place it in a known directory (e.g., /usr/local/bin).")
            print("3. Create a wrapper script to make it executable from the command line:")
            print("   - Linux/macOS: Create a file named 'apktool' in /usr/local/bin with the following content:")
            print("       #!/bin/bash")
            print("       java -jar /usr/local/bin/apktool.jar \"$@\"")
            print("     Then run: chmod +x /usr/local/bin/apktool")
            print("   - Windows: Run via terminal using: java -jar apktool.jar")
            print("\nAlternative:")
            print("   - macOS (Homebrew): brew install apktool")
            print("   - Linux (APT): sudo apt install apktool")
            print("\nPlease install apktool and try again.\n")
            sys.exit(1)

        apk_path = args.apk
        result = extract_google_vars(apk_path)

        os.system("cls" if os.name == "nt" else "clear")
        if not(args.silent):
            print("\n=== Firebase RemoteConfig Dumped! ===")
        if result["google_api_key"] or result["google_app_id"]:
            print(f"google_api_key: {result['google_api_key']} and google_app_id: {result['google_app_id']}")
            data = get_remote_config(result["google_api_key"], result["google_app_id"])
            print_readable(data)
            
        else:
            print("[-] No variables found.")
    
    elif args.appid and args.apikey:
        stripped_appid = args.appid.split(":")
        
        if stripped_appid[2] == "web":
            data = get_web_config(args.apikey, args.appid)
            print_readable(data)
        else:
            data = get_remote_config(args.apikey, args.appid) 
            print_readable(data)
    
    else:
        print("[!] Try to use --help argument...")


if __name__ == '__main__':
    main()
