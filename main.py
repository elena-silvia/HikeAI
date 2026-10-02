import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from app.agent import MountainAgent
from app.tools import get_mountain_weather, read_safety_guidelines
from app.storage import list_saved_hikes


def print_banner():
    print("=" * 65)
    print("RoMountainAgent - Your Intelligent Mountain Guide")
    print("=" * 65)
    print("Commands:")
    print("  /save              - Save the latest trail dossier to a .md file")
    print("  /weather <dest>    - Check live mountain weather (e.g. /weather Omu)")
    print("  /salvamont         - Display Salvamont rules & emergency contacts")
    print("  /saved             - List offline saved trail dossiers")
    print("  /clear             - Reset conversation memory")
    print("  exit / quit        - Exit application")
    print("=" * 65 + "\n")


def main():
    print_banner()

    try:
        agent = MountainAgent()
    except Exception as e:
        print(f"[ERROR] Error initializing agent: {e}")
        return

    session_id = "cli_session"

    while True:
        try:
            user_input = input("\nYou: ").strip()
            if not user_input:
                continue

            cmd_lower = user_input.lower()
            if cmd_lower in {"exit", "quit"}:
                print("\nHave a great hike! Goodbye!")
                break

            elif cmd_lower == "/help":
                print_banner()
                continue

            elif cmd_lower == "/save":
                saved_path = agent.export_last_hike(session_id=session_id, user_name="CLI User")
                if saved_path and saved_path.exists():
                    print(f"\n[SUCCESS] Trail dossier saved successfully!\nLocation: {saved_path}")
                else:
                    print("\n[WARNING] No recent trail found to save. Inquire about a trail first!")
                continue

            elif cmd_lower.startswith("/weather"):
                parts = user_input.split(maxsplit=1)
                dest = parts[1].strip() if len(parts) > 1 else "Bucegi"
                print(f"\nChecking weather for '{dest}'...")
                print(get_mountain_weather(destination=dest))
                continue

            elif cmd_lower == "/salvamont":
                print("\n" + read_safety_guidelines())
                continue

            elif cmd_lower == "/saved":
                hikes = list_saved_hikes()
                if not hikes:
                    print("\nNo saved trails in 'saved_hikes/' folder.")
                else:
                    print("\nSaved mountain trails offline:")
                    for h in hikes:
                        print(f" - {h['filename']} ({h['created_at']})")
                continue

            elif cmd_lower == "/clear":
                agent.reset_session(session_id)
                print("\nConversation memory cleared.")
                continue

            print("\nGuide is analyzing route, live weather, and Salvamont safety rules...")
            response = agent.send_message(user_input, session_id=session_id, user_name="CLI User")
            print(f"\nRoMountainAgent:\n{response}")
            print("\n[Tip: Type '/save' to export this route into saved_hikes/]")

        except KeyboardInterrupt:
            print("\n\nForced exit. Have a safe hike!")
            break
        except Exception as e:
            print(f"\n[ERROR] {e}")


if __name__ == "__main__":
    main()