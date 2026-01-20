from agents.clerk import clerk_agent

def main():
    print("Inventory Assistant (type 'exit' to quit)")
    
    while True:
        user_input = input("You: ")

        if user_input.lower() == "exit":
            break

        response = clerk_agent(user_input)
        print("Bot:", response)


if __name__ == "__main__":
    main()
