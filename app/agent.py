from .tools.financial_extractor import extract_financials
from .tools.qualitative_analysis import analyze_transcripts
from .tools.vectorstore import create_or_load_vector_store
from .tools.market_data import fetch_market_data
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq
from langchain_core.runnables import RunnableLambda, RunnableParallel
import os
from dotenv import load_dotenv
import logging
import warnings

logger = logging.getLogger(__name__)
load_dotenv()

model = os.getenv("MODEL_NAME", "llama-3.3-70b-versatile")
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise EnvironmentError("Missing GROQ_API_KEY in environment variables.")

warnings.filterwarnings("ignore", category=DeprecationWarning)

def get_llm():
    try:
        return ChatGroq(
            model=model,
            api_key=api_key,
            temperature=0.1,
            max_tokens=1000
        )
    except Exception as e:
        logger.error("Failed to initialize LLM: %s", str(e))
        raise RuntimeError("LLM Initialization failed") from e

def synthesize_forecast(task, financials, qualitative, market, llm):
    try:
        prompt = PromptTemplate(
            input_variables=["task", "financials", "qualitative", "market"],
            template=(
                """
        You are a senior financial analyst preparing a forecast for the upcoming quarter.

        Inputs:
        - Financial Metrics (latest quarterly reports):
        {financials}

        - Earnings Call Insights:
        {qualitative}

        - Market Data:
        {market}

        Task:
        {task}
        Using these inputs, create a clear and concise forecast in JSON format with the following sections. You may perform analytical calculations and extrapolations to estimate next quarter’s performance.

        1. trends: Key financial trends like revenue growth, margin changes, cost variations.
        2. management_outlook: Summarize management sentiment and forward guidance.
        3. risks: List main risks, each with a brief description and estimated impact (high/medium/low).
        4. opportunities: List main opportunities, each with a brief description and estimated benefit.
        5. assumptions: Clearly state any assumptions made in your forecast (e.g., market conditions, cost stability, regulatory environment, etc.).
        6. overall_forecast: A summary including any numeric estimates (if possible) and a confidence level ('high', 'medium', or 'low').

        Please format your response as JSON. Avoid extra commentary outside JSON.

        Example output:
        {{
        "trends": {{
            "revenue_growth": "12% YoY",
            "operating_margin": "14%",
            "cost_increase": "3% due to supply chain"
        }},
        "management_outlook": {{
            "sentiment": "cautiously optimistic",
            "forward_guidance": [
            "Expect revenue growth of 10-15%",
            "Target operating margin around 14%"
            ]
        }},
        "risks": [
            {{"risk": "raw material price volatility", "impact": "medium"}},
            {{"risk": "regulatory delays", "impact": "low"}}
        ],
        "opportunities": [
            {{"opportunity": "expansion into Asia market", "benefit": "increase revenue by 5%"}},
            {{"opportunity": "new product launch", "benefit": "boost net profit margin"}}
        ],
        "overall_forecast": {{
            "summary": "Strong revenue growth expected driven by new products and market expansion, balanced by supply chain risks.",
            "confidence_level": "medium"
        }}
        }}
        """
        )
        )
        response = llm.invoke(
            prompt.format(
                task=task,
                financials=financials,
                qualitative=qualitative,
                market=market
            )
        )
        return response.content.strip()
    except Exception as e:
        logger.exception("Failed to synthesize forecast.")
        raise RuntimeError("Forecast synthesis failed") from e

def generate_forecast(task):
    try:
        llm = get_llm()
        vector_store = create_or_load_vector_store()

        parallel_tools = RunnableParallel({
            "financials": RunnableLambda(
                lambda inputs: extract_financials(
                    task=inputs["task"], llm=llm, vector_store=vector_store)
            ),
            "qualitative": RunnableLambda(
                lambda inputs: analyze_transcripts(
                    task=inputs["task"], llm=llm, vector_store=vector_store)
            ),
            "market": RunnableLambda(
                lambda _: fetch_market_data()
            )
        })

        results = parallel_tools.invoke({"task": task})

        forecast = synthesize_forecast(
            task=task,
            financials=results["financials"],
            qualitative=results["qualitative"],
            market=results["market"],
            llm=llm
        )
        return forecast
    except Exception as e:
        logger.exception("Error generating forecast.")
        raise RuntimeError("Error in generating forecast") from e
