import streamlit as st
from openai import OpenAI
from pinecone import Pinecone
import os

st.title("Chat with Lauder 24-25!")

OpenAIclient = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
pinecone = Pinecone(api_key=st.secrets["PINECONE_API_KEY"])

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("What is up?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    query_embedding = OpenAIclient.embeddings.create(input=[prompt], model="text-embedding-3-large")

    pinecone_index = pinecone.Index('lauderrag-index-3')
    results = pinecone_index.query(
        namespace="ns1",
        vector=query_embedding.data[0].embedding,
        top_k=10,
        include_values=False,
        include_metadata=True
    )

    chunk_1_chunk_index = int(results['matches'][0].metadata['text_chunk_index'])
    print(chunk_1_chunk_index)
    chunk_2_chunk_index = int(results['matches'][1].metadata['text_chunk_index'])
    print(chunk_2_chunk_index)
    chunk_3_chunk_index = int(results['matches'][2].metadata['text_chunk_index'])
    print(chunk_3_chunk_index)

    import pymongo
    print("connecting to ")
    connectionstring = f"mongodb+srv://{st.secrets['username']}:{st.secrets['password']}@{st.secrets['cluster']}/?retryWrites=true&w=majority&appName=test1"

    Mongoclient = pymongo.MongoClient(connectionstring)
    collection = Mongoclient['LauderRAG']['questionized_results']

    questionized_result = Mongoclient['LauderRAG']['questionized_results'].find_one({'_id': "LauderRAG_fakenames"})['data']

    # for doc in Mongoclient['LauderRAG']['questionized_results'].find():
    #     questionized_result = doc['data']

    chunk_1 = questionized_result[chunk_1_chunk_index]["original"]
    chunk_2 = questionized_result[chunk_2_chunk_index]["original"]
    chunk_3 = questionized_result[chunk_3_chunk_index]["original"]

    questionNext1 = questionized_result[chunk_1_chunk_index]["processed_newlined"][2]
    questionNext2 = questionized_result[chunk_2_chunk_index]["processed_newlined"][0]
    questionNext3 = questionized_result[chunk_3_chunk_index]["processed_newlined"][0]

    aggregated_chunk = chunk_1
    if chunk_1_chunk_index == chunk_2_chunk_index:
        print("Same chunk")
    else:
        print("Different chunk")
        aggregated_chunk = chunk_1 + " " + chunk_2 + " " + chunk_3

    user_message = prompt + "Please create a balanced view, rather than leaning towards giving a direct answer to this question.  Please reference specific chat messages and answer the question. Please err on the side of giving more context information, and reference that. It's best if you include the conversation in its entirety rather than selected bits and pieces. Please include all side of the debate"

    system_message = "This is a transcript of a chat conversation between Lauder students in the 2024-2025 groupchat. Please answer questions and reference specific parts of the chat history, quoting people and messages directly. " + aggregated_chunk

    print(user_message)
    print(system_message)
    print(aggregated_chunk)

    messages = [
        {'role': 'system', 'content': system_message},
        {'role': 'user', 'content': user_message}
    ]

    with st.chat_message("assistant"):
        stream = OpenAIclient.chat.completions.create(
            model="gpt-4",
            messages=messages,
            stream=True,
        )
    response = st.write_stream(stream)
    st.session_state.messages.append({"role": "assistant", "content": response})