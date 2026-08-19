from app.agent import MountainAgent

def main():

    print("Welcome to RoMountainAgent - Your mountain guide")
    print("Type 'exit' or 'quit' to exit\n")

    agent = MountainAgent()
    while True:
        try:
            user_input = input("You: ").strip()
            if not user_input:
                continue
            if user_input.lower() in {"exit", "quit"}:
                print("Have a nice hike!")
                break
            print("Thinking...")
            response = agent.send_message(user_input)
            print(f"RoMountainAgent:\n{response}")
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"\n Error: {e}")

if __name__ == "__main__":
    main()