from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from calculator import Calculator

app = FastAPI()
calculator = Calculator()


class OperationRequest(BaseModel):
    a: float
    b: float


class ExpressionRequest(BaseModel):
    expression: str


class ExpressionResponse(BaseModel):
    expression: Optional[str]
    result: Optional[float]


@app.get("/")
def root():
    return {"message": "Calculator API", "version": "v1"}


@app.post("/v1/add", response_model=ExpressionResponse)
def add(request: OperationRequest):
    try:
        result = calculator.add(request.a, request.b)
        return ExpressionResponse(expression=None, result=result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/v1/subtract", response_model=ExpressionResponse)
def subtract(request: OperationRequest):
    try:
        result = calculator.subtract(request.a, request.b)
        return ExpressionResponse(expression=None, result=result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/v1/multiply", response_model=ExpressionResponse)
def multiply(request: OperationRequest):
    try:
        result = calculator.multiply(request.a, request.b)
        return ExpressionResponse(expression=None, result=result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/v1/divide", response_model=ExpressionResponse)
def divide(request: OperationRequest):
    try:
        result = calculator.divide(request.a, request.b)
        return ExpressionResponse(expression=None, result=result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/v1/expression", response_model=ExpressionResponse)
def set_expression(request: ExpressionRequest):
    try:
        calculator.set_expression(request.expression)
        return ExpressionResponse(expression=calculator.get_expression(), result=None)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/v1/expression/evaluate", response_model=ExpressionResponse)
def evaluate_expression(request: ExpressionRequest):
    try:
        result = calculator.evaluate_expression(request.expression)
        return ExpressionResponse(expression=request.expression, result=result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/v1/expression", response_model=ExpressionResponse)
def get_expression():
    try:
        return ExpressionResponse(expression=calculator.get_expression(), result=calculator.result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/v1/expression/execute", response_model=ExpressionResponse)
def execute_expression():
    try:
        result = calculator.execute()
        return ExpressionResponse(expression=calculator.get_expression(), result=result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

