from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse, HTMLResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.templating import Jinja2Templates
from graphene import ObjectType, String, Int, List, Schema, Field
from strawberry.fastapi import GraphQLRouter
import strawberry
import json

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# --- Mock Data ---
data = {
    "deals": [
        {"id": 1, "price": 100000, "location": "City A"},
        {"id": 2, "price": 150000, "location": "City B"},
    ]
}

# --- REST API Endpoint ---
@app.get("/api/deals", response_class=JSONResponse)
def get_deals():
    return data["deals"]

# --- GraphQL Schema ---
@strawberry.type
class Deal:
    id: int
    price: int
    location: str

@strawberry.type
class Query:
    deals: List[Deal] = strawberry.field(resolver=lambda: data["deals"])

gql_schema = Schema(query=Query)
graphql_app = GraphQLRouter(gql_schema)
app.include_router(graphql_app, prefix="/graphql")

# --- HTML Template Rendering ---
@app.get("/deals", response_class=HTMLResponse)
def render_deals_page(request: Request):
    return templates.TemplateResponse("deals.html", {"request": request, "deals": data["deals"]})

# --- Middleware для динамического выбора API ---
class DynamicAPIMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        accept = request.headers.get("Accept", "")
        content_type = request.headers.get("Content-Type", "")
        
        if "application/json" in accept or content_type == "application/json":
            request.scope["path"] = "/api/deals"  # Перенаправляем на REST
        elif "application/graphql" in accept or request.scope["path"].startswith("/graphql"):
            request.scope["path"] = "/graphql"
        elif "text/html" in accept:
            request.scope["path"] = "/deals"  #  HTML output
        
        response = await call_next(request)
        return response

app.add_middleware(DynamicAPIMiddleware)

# --- Запуск ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
