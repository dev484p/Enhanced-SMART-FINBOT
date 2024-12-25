import os
import json
from typing import List
from typing import Literal
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field
from typing_extensions import TypedDict
from langgraph.graph import END, StateGraph, START
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper

def graph(retriever):
    class RouteQuery(BaseModel):
        """Route a user query to the most relevant datasource."""
        datasource: Literal["vectorstore", "wiki_search"] = Field(...,description="Given a user question choose to route it to wikipedia or a vectorstore.",)

    with open("VectorDB\keys.JSON", "r") as file:
        data = json.load(file)
    groq_api_key= data['groq_api_key']
    os.environ["GROQ_API_KEY"]=groq_api_key

    llm=ChatGroq(groq_api_key=groq_api_key,model_name="Llama-3.1-70b-Versatile")
    structured_llm_router = llm.with_structured_output(RouteQuery)

    system = """You are an expert at routing a user question to a vectorstore or wikipedia.
    The vectorstore contains documents related to Finance, Economics, Money/Risk management,Accounting and Investing.
    Use the vectorstore for questions on these topics. Otherwise, use wiki-search."""
    route_prompt = ChatPromptTemplate.from_messages([("system", system),("human", "{question}"),])
    question_router = route_prompt | structured_llm_router

    api_wrapper=WikipediaAPIWrapper(top_k_results=1,doc_content_chars_max=1000)
    wiki=WikipediaQueryRun(api_wrapper=api_wrapper)

    ## Graph
    class GraphState(TypedDict):
        question: str
        generation: str
        documents: List[str]
        
    def route_question(state):
        question = state["question"]
        source = question_router.invoke({"question": question})
        if source.datasource == "wiki_search":
            print("--> ROUTE QUESTION TO Wiki SEARCH :")
            return "wiki_search"
        elif source.datasource == "vectorstore":
            print("--> ROUTE QUESTION TO RAG :")
            return "vectorstore"

    def retrieve(state):
        question = state["question"]
        documents = retriever.invoke(question)
        retrieved_content = documents[0].page_content  
        summary = llm.invoke(f"Answer the following question based on the provided context and your own knowledge. Think step by step before providing a detailed answer. <context>{retrieved_content}</context> Question: {question}")
        return {"documents": [summary], "question": question}

    def wiki_search(state):
        question = state["question"]
        docs = wiki.invoke({"query": question})
        summary = llm.invoke(f"Answer the following question based on the provided Wiki context and your own knowledge. Think step by step before providing a detailed answer. <context>{docs}</context> Question: {question}")
        return {"documents": [summary], "question": question}


    # Define the nodes
    workflow = StateGraph(GraphState)
    workflow.add_node("wiki_search", wiki_search)  # web search
    workflow.add_node("retrieve", retrieve)  # retrieve

    # Build graph
    workflow.add_conditional_edges(START,route_question,{"wiki_search": "wiki_search","vectorstore": "retrieve",},)
    workflow.add_edge( "retrieve", END)
    workflow.add_edge( "wiki_search", END)
    app = workflow.compile()
    
    return app