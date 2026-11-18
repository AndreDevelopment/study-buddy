import os
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.tools import create_retriever_tool
from langchain_anthropic import ChatAnthropic # Or use langchain_openai if using OpenAI
from langgraph.prebuilt import create_react_agent

# 1. Load environment variables
load_dotenv()

PERSIST_DIRECTORY = "./chroma_db"

def initialize_agent():
    print("Loading local vector database...")
    
    # Must match the embedding model you used during ingestion!
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    
    # Connect to your existing Chroma database
    vector_store = Chroma(
        persist_directory=PERSIST_DIRECTORY,
        embedding_function=embeddings
    )
    
    # 2. Turn the vector store into a retriever
    # k=3 means it will pull the top 3 most relevant chunks
    retriever = vector_store.as_retriever(
        search_type="similarity", 
        search_kwargs={"k": 3}
    )
    
    # 3. Wrap the retriever into a Tool so the LLM can invoke it
    retriever_tool = create_retriever_tool(
        retriever,
        name="student_notes_search",
        description="Search through the student's personal lecture notes and markdown files to find relevant information."
    )
    
    tools = [retriever_tool]

    print("Initializing LLM...")
    # Initialize Claude (ensure ANTHROPIC_API_KEY is in your .env)
    # If using OpenAI instead, swap this for: from langchain_openai import ChatOpenAI; llm = ChatOpenAI(model="gpt-4o-mini")
    llm = ChatAnthropic(model="claude-sonnet-5")

    # 4. Create the LangGraph ReAct agent
    # This prebuilt agent handles the loop of: User Question -> Decide to Search -> Read Notes -> Answer
    system_prompt = (
        "You are an expert AI study assistant. Your job is to answer the student's questions "
        "accurately using *only* the information retrieved from their notes. "
        "Always cite the source filename/metadata provided in the retrieved context when answering."
    )
    
    agent_executor = create_react_agent(
        model=llm, 
        tools=tools, 
        prompt=system_prompt
    )
    
    return agent_executor

agent_executor = initialize_agent()
if __name__ == "__main__":
    print("\n--- RAG Agent Ready! ---")
    
    # Test query loop
    while True:
        query = input("\nAsk a question about your notes (or type 'quit'): ")
        if query.lower() == 'quit':
            break
            
        print("\nThinking...")
        # Invoke the LangGraph agent
        response = agent_executor.invoke({"messages": [("user", query)]})
        
        # Print the final response from the agent's message history
        print("\nAnswer:")
        print(response["messages"][-1].content)