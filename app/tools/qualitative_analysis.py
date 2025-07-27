from langchain_core.prompts import PromptTemplate
import logging

logger = logging.getLogger(__name__)

def analyze_transcripts(task: str, llm, vector_store):
    try:
        query = f"Extract qualitative insights from the latest 2-3 earnings call transcripts for task: {task}."
        retriever = vector_store.as_retriever()
        retriever.search_kwargs["filter"] = {"type": "transcript"}
        relevant_chunks = retriever.get_relevant_documents(query)
        context = "\n\n".join([chunk.page_content for chunk in relevant_chunks])

        prompt_template = PromptTemplate(
            input_variables=["context","task"],
            template=(
                "You are a financial analyst. Do a qualitative analysis of the provided context on latest earnings call transcripts and extract the following:\n"
                "1. Recurring Themes: Common topics, strategic initiatives, or challenges discussed across multiple calls especially those relevant to future business performance.\n"
                "2. Management Sentiment: Access Overall tone regarding performance and future outlook. Use categories: 'optimistic', 'cautious', 'neutral', 'negative'.\n"
                "3. Forward-Looking Statements: Analyse Any specific outlook, guidance, or expectations for future periods (e.g., 'expect revenue growth to moderate', 'target 20% increase').\n"
                "4. Risks & Opportunities: Identify specific external or internal factors mentioned that could impact future performance.and indicate whether they are likely to be short-term or long-term in nature.\n\n"
                "Context:\n{context}\n\n"
                "End goal:\n{task}\n\n" 
                "rovide the extracted information in a structured JSON format, including any relevant qualitative metrics or analysis that could inform financial forecasting for future quarters."
            )
        )
        prompt = prompt_template.format(context=context, task=task)
        response = llm.invoke(prompt)
        return response.content.strip()
    except Exception as e:
        logger.error(f"Error analyzing transcripts: {e}")
        raise