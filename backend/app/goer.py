import json

from groq import Groq

from app.config import GROQ_API_KEY
from app.agent_tools.search_menu import search_menu, SEARCH_MENU_TOOL
from app.agent_tools.get_menu import get_menu, GET_MENU_TOOL


if __name__ == "__main__":
    client = Groq(
        api_key=GROQ_API_KEY,
        timeout=30.0,
    )

    model = "openai/gpt-oss-20b"

    messages = [
        {
            "role": "system",
            "content": (
                "You are Goer, LocalGo's ordering assistant. "
                "Use search_menu when the user asks for a specific food. "
                "Use get_menu when the user wants to browse a merchant's menu "
                "or wants recommendations from a merchant. "
                "Only filter by merchant when the user names one or has "
                "clearly selected one earlier in the conversation. "
                "If the user wants to browse without selecting a merchant, "
                "ask which merchant they want. "
                "Never invent products or prices. "
                "Prices are stored in cents; divide by 100 to display CAD. "
                "Always show the merchant name with each product. "
                "When get_menu returns many products, show no more than five "
                "and ask what category or food the user prefers. "
                "Menu listings do not guarantee current stock. "
                "You cannot add products to a cart or place orders yet. "
                "Keep your answers short."
                "Use product names, categories, and descriptions exactly as returned by the tools. "
            ),
        }
    ]

    while True:
        user_text = input("\nYou: ").strip()

        if user_text.lower() in ("exit", "quit"):
            break

        if not user_text:
            continue

        messages.append({
            "role": "user",
            "content": user_text,
        })

        # Give Goer at most five model decisions for one user message.
        for step in range(5):
            print("Goer is thinking...")

            response = client.chat.completions.create(
                model=model,
                messages=messages,
                tools=[SEARCH_MENU_TOOL, GET_MENU_TOOL],
                tool_choice="auto",
            )

            message = response.choices[0].message

            # Save Goer's response or tool request in conversation history.
            messages.append(
                message.model_dump(exclude_none=True)
            )

            # No tool request means Goer has finished answering.
            if not message.tool_calls:
                print("Goer:", message.content)
                break

            # Execute every tool requested by Goer.
            for call in message.tool_calls:
                arguments = json.loads(
                    call.function.arguments
                )

                if call.function.name == "search_menu":
                    results = search_menu(
                        product_name=arguments["product_name"],
                        merchant_id=arguments.get("merchant_id"),
                    )

                elif call.function.name == "get_menu":
                    results = get_menu(
                        merchant_id=arguments["merchant_id"],
                    )

                else:
                    results = {
                        "error": (
                            f"Unknown tool: {call.function.name}"
                        )
                    }

                # Connect this result to its specific tool request.
                messages.append({
                    "role": "tool",
                    "tool_call_id": call.id,
                    "name": call.function.name,
                    "content": json.dumps(
                        results,
                        ensure_ascii=False,
                    ),
                })

        else:
            answer = (
                "I couldn't finish that request. "
                "Please try being more specific."
            )

            messages.append({
                "role": "assistant",
                "content": answer,
            })

            print("Goer:", answer)