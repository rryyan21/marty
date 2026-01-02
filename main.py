from brain import think

print("MARTY online...")

while True:
    user_input = input("You: ")

    if user_input.lower() in ["exit", "quit"]:
        print("MARTY: Leaving already? Fine.")
        break

    response = think(user_input)
    print("MARTY:", response)
