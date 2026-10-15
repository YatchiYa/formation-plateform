"""A small MCP server ("product catalog") served over Streamable HTTP at /mcp.

Any MCP client (ADK agents, Gemini CLI, Claude Code, ...) can list and call its tools.
"""
import os

import uvicorn
from fastmcp import FastMCP

# ponytail: in-memory demo data; swap for your DB / internal API.
PRODUCTS = {
    "SKU-001": {"name": "Laptop Pro 14", "category": "laptops", "price_eur": 1499.0, "stock": 12},
    "SKU-002": {"name": "Laptop Air 13", "category": "laptops", "price_eur": 999.0, "stock": 0},
    "SKU-003": {"name": "4K Monitor 27", "category": "monitors", "price_eur": 449.0, "stock": 31},
    "SKU-004": {"name": "Wireless Mouse", "category": "accessories", "price_eur": 39.0, "stock": 140},
    "SKU-005": {"name": "USB-C Dock", "category": "accessories", "price_eur": 189.0, "stock": 7},
}

mcp = FastMCP(
    "product-catalog",
    instructions="Company product catalog: search products, read prices and stock levels.",
)


@mcp.tool(annotations={"title": "Search products", "readOnlyHint": True})
def search_products(query: str) -> list[dict]:
    """Searches the product catalog by name or category (case-insensitive).

    Args:
        query: Words to look for, e.g. "laptop" or "accessories".
    """
    q = query.strip().lower()
    return [{"sku": sku, **p} for sku, p in PRODUCTS.items() if q in p["name"].lower() or q in p["category"]]


@mcp.tool(annotations={"title": "Get stock level", "readOnlyHint": True})
def get_stock(sku: str) -> dict:
    """Returns the current stock level and price of one product.

    Args:
        sku: Product SKU, e.g. "SKU-001".
    """
    product = PRODUCTS.get(sku.strip().upper())
    if product is None:
        return {"status": "error", "error_message": f"Unknown SKU '{sku}'."}
    return {"status": "success", "sku": sku.upper(), "name": product["name"], "stock": product["stock"], "price_eur": product["price_eur"]}


# Stateless = no MCP session kept in memory, so Cloud Run can run N instances
# behind its load balancer without "unknown session" errors.
app = mcp.http_app(path="/mcp", stateless_http=True)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8080")))
