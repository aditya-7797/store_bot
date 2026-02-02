from graph.workflow import graph
from tools.inventory_tools import cleanup_duplicates
cleanup_duplicates()


print("🤖 Inventory Assistant (type 'exit' to quit)")

while True:
    user_input = input("You: ").strip()
    
    if user_input.lower() == "exit":
        print("Bot: Goodbye! 👋")
        break

    if not user_input:
        print("Bot: Please type something!")
        continue

    try:
        state = {"query": user_input}
        final_state = graph.invoke(state)
        response = final_state.get("response", "Sorry, I didn't understand that.")
    except Exception as e:
        response = f"Oops! Something went wrong: {e}"

    print("Bot:", response)
