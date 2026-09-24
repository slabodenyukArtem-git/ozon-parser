"""
Terminal setup wizard for Ozon parser.

Usage:
    python main.py setup                              -- interactive mode
    python main.py setup --all --phone +79991234567 --gmail user@gmail.com --password xxx --sku 123,456
"""

import argparse
import re
from pathlib import Path


def _validate_email(email: str) -> bool:
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def setup_cli(args=None):
    """Run setup wizard."""
    print("")
    print("=" * 60)
    print("  Ozon Parser - Setup")
    print("=" * 60)
    print("")

    env_path = Path(__file__).parent / ".env"

    # Load existing values from .env if exists
    current = {}
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    current[key.strip()] = value.strip()

    if current:
        print("Current settings from .env:")
        for key, value in current.items():
            display_value = value if key != "GMAIL_APP_PASSWORD" else "********"
            print(f"  {key} = {display_value}")
        print("")

    # --- Interactive mode ---
    if not args:
        phone = input("Phone number [+79991234567]: ").strip() or "+79991234567"
        while not phone.startswith("+7"):
            print("  WARNING: Phone must start with +7")
            phone = input("Phone number [+79991234567]: ").strip() or "+79991234567"

        gmail = input("Gmail Email [user@gmail.com]: ").strip() or "user@gmail.com"
        while not _validate_email(gmail):
            print("  WARNING: Enter valid email")
            gmail = input("Gmail Email [user@gmail.com]: ").strip() or "user@gmail.com"

        print("")
        print("  INFO: App Password:")
        print("  1. Google Account -> Security -> 2-Step Verification")
        print("  2. App Passwords -> create for 'Mail'")
        print("")
        app_password = input("Gmail App Password: ").strip()

        if not app_password:
            proceed = input("  Continue without password? (yes/no): ").strip().lower()
            if proceed != "yes":
                print("  Setup cancelled.")
                return

        sku_list = input("SKU comma-separated [2359066702,2829800382]: ").strip() or "2359066702,2829800382"
    else:
        # CLI arguments mode
        phone = args.phone or "+79991234567"
        gmail = args.gmail or "user@gmail.com"
        app_password = args.password or ""
        sku_list = args.sku or "2359066702,2829800382"

        # Validation
        if not phone.startswith("+7"):
            print("  WARNING: Phone must start with +7")
            return

        if not _validate_email(gmail):
            print("  WARNING: Enter valid email")
            return

        if not app_password:
            print("  WARNING: App Password is required!")
            return

    # --- Save ---
    print("")
    print("-" * 60)
    print("Saving settings...")

    with open(env_path, "w", encoding="utf-8") as f:
        f.write("# Phone number for login to data.ozon.ru\n")
        f.write(f"PHONE_NUMBER={phone}\n\n")
        f.write("# Gmail credentials for reading confirmation codes\n")
        f.write(f"GMAIL_EMAIL={gmail}\n")
        f.write(f"GMAIL_APP_PASSWORD={app_password}\n\n")
        f.write("# SKU list comma-separated\n")
        f.write(f"SKU_LIST={sku_list}\n")

    print("")
    print("[OK] Settings saved to .env file!")
    print("")
    print("Next steps:")
    print("  1. python main.py cookies   - get cookies")
    print("  2. python main.py parse     - parse products")
    print("  3. python main.py all       - get cookies + parse products")
    print("")


def main():
    """Entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Ozon Parser Setup",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py setup                                              -- interactive mode
  python main.py setup --all --phone +79991234567 --gmail user@gmail.com --password xxx --sku 123,456
        """,
    )
    parser.add_argument("--phone", type=str, default=None, help="Phone number for login")
    parser.add_argument("--gmail", type=str, default=None, help="Gmail Email")
    parser.add_argument("--password", type=str, default=None, help="Gmail App Password")
    parser.add_argument("--sku", type=str, default=None, help="SKU list comma-separated")
    parser.add_argument("--all", action="store_true", help="All parameters via CLI args")

    args = parser.parse_args()

    if args.all:
        if not args.phone or not args.gmail or not args.password:
            print("  WARNING: For --all mode need --phone, --gmail and --password\n")
            parser.print_help()
            return
        setup_cli(args)
    else:
        # If at least phone and gmail are provided -- use CLI mode
        if args.phone or args.gmail or args.password:
            setup_cli(args)
        else:
            # Interactive mode
            setup_cli()


if __name__ == "__main__":
    main()
