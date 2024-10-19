import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
from functools import lru_cache

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

class DietRequest(BaseModel):
    food_allergies: str
    medical_allergies: str
    state: str

class DietPlan(BaseModel):
    breakfast: str
    lunch: str
    dinner: str

OPENAI_API_KEY = "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"

@lru_cache(maxsize=100)
async def generate_diet_plan(food_allergies: str, medical_allergies: str, state: str) -> DietPlan:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": [
                        {"role": "system", "content": "You are a nutritionist creating healthy diet plans."},
                        {"role": "user", "content": f"Create a healthy diet plan for someone with the following allergies and location:\n"
                                                    f"Food allergies: {food_allergies}\n"
                                                    f"Medical allergies: {medical_allergies}\n"
                                                    f"State: {state}\n"
                                                    f"Provide a plan for breakfast, lunch, and dinner in JSON format."}
                    ],
                    "temperature": 0.7,
                },
                timeout=10.0
            )

        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        logger.info(f"OpenAI API Response: {content}")

        plan = eval(content)  # Safely evaluate the JSON string
        return DietPlan(**plan)
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error occurred: {e}")
        raise HTTPException(status_code=500, detail=f"OpenAI API error: {str(e)}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

@app.post("/diet-plan", response_model=DietPlan)
async def diet_plan(request: DietRequest):
    return await generate_diet_plan(request.food_allergies, request.medical_allergies, request.state)

@app.get("/")
async def root():
    return {"message": "Welcome to the Diet Plan API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
