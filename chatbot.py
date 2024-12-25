import json
import cassio
from LangGraph import graph
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Cassandra

def main(query,retriever):
    app=graph(retriever)
    inputs = {"question": query}
    for output in app.stream(inputs):
        for key, value in output.items():
            print(f"Node '{key}':")
        print("\n---\n")
    # Final generation
    print(value['documents'][0].model_dump(include={'content'})['content'])

if __name__ == "__main__":
    ## connection of the ASTRA DB
    with open("VectorDB\keys.JSON", "r") as file:
        data = json.load(file)
    ASTRA_DB_APPLICATION_TOKEN=data['ASTRA_DB_APPLICATION_TOKEN']
    ASTRA_DB_ID=data['ASTRA_DB_ID']
    print("\nPlease wait while we connect to the server ...")
    
    try:
        cassio.init(token=ASTRA_DB_APPLICATION_TOKEN,database_id=ASTRA_DB_ID)
        print("Connection successful.")
        f=1
    except ValueError as e:
        print(f"\nFailed to establish a session. Please check your Token and ID\n")
        f=0

    if f:
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        astra_vector_store=Cassandra(embedding=embeddings,table_name="qa_mini_demo",session=None,keyspace=None)
        retriever=astra_vector_store.as_retriever()
        
        # Ask the user for their query and pass it to the main function.
        query=""
        while True:
            query = str(input("\n----------\nEnter the Query (press q to exit)- "))
            if query == 'q':
                print("\nThank you and All the Best for your Personal Finance !!!\n")
                break
            main(query,retriever)        