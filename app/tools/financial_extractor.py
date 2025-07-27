from langchain_core.prompts import PromptTemplate
import logging

logger = logging.getLogger(__name__)
def extract_financials(task: str, llm, vector_store):
    try:
        query = f"Extract key financial metrics from the latest reports for task: {task}."
        retriever = vector_store.as_retriever()
        retriever.search_kwargs["filter"] = {"type": "report"}
        relevant_chunks = retriever.get_relevant_documents(query)
        context = "\n\n".join([chunk.page_content for chunk in relevant_chunks])

        prompt_template = PromptTemplate(
            input_variables=["context","task"],
            template=(
                "You are a financial analyst. From the following quarterly financial report context, "
                "extract key forecastable business metrics with exact values with units(if any), and periods.If a metric is missing, indicate it as 'N/A'" 
                "Context:\n{context}\n\n"
                "End goal:\n{task}\n\n"                
                "  - quarter\n"
                "  - total_revenue\n"
                "  - net_profit\n"
                "  - operating_margin\n"
                "  - ebitda\n"
                "  - earnings_per_share (EPS)\n"
                "  - pe_ratio\n"
                "  - roe (Return on Equity)\n"
                "  - total_expenses\n"
                "  - finance_costs\n"
                "  - depreciation_amortization\n"
                "  - tax_expense\n"
                "  - free_cash_flow\n"
                "  - Any other key metrics relevant to financial performance.\n\n"
                "Ensure all extracted data and commentary are suitable for use in forecasting future quarters."
            )
        )
        
        prompt = prompt_template.format(context=context, task=task)

        response = llm.invoke(prompt)
        return response.content.strip()
    except Exception as e:
        logger.error(f"Error extracting financials: {e}")
        raise
