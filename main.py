from tools.inventory_tools import cleanup_duplicates


from graph.workflow import workflow


def main():
    print("Inventory Assistant (type 'exit' to quit)")

    while True:
        user_input = input("You: ").strip()

        if user_input.lower() == "exit":
            print("Bot: Goodbye!")
            break

        result = workflow.invoke({"query": user_input})
        print(f"Bot: {result['result']}")


if __name__ == "__main__":
    main()
