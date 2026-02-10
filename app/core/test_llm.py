from app.core.llm import get_llm

if __name__ == "__main__":
    llm = get_llm()
    response = llm.invoke(str(input("Enter your message: ")))
    print(response.content)