from __future__ import annotations
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Optional
from .db import get_connection, init_db, list_ads, create_ad, get_ad, update_ad_fields, toggle_ad_status
from .provider import get_provider, AdUpdate


app = FastAPI(title="P2P Merchant Control")
app.mount("/static", StaticFiles(directory="/workspace/p2p_merchant_web/static"), name="static")

templates = Jinja2Templates(directory="/workspace/p2p_merchant_web/templates")


@app.on_event("startup")
def startup() -> None:
    conn = get_connection()
    init_db(conn)


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    ads = list_ads()
    provider = get_provider()
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "ads": ads,
            "provider_mode": provider.mode,
            "keys_ok": provider.has_credentials,
        },
    )


@app.get("/new", response_class=HTMLResponse)
def new_ad_form(request: Request):
    return templates.TemplateResponse("new.html", {"request": request})


@app.post("/new")
def create_ad_post(
    title: str = Form(...),
    trade_type: str = Form(...),
    price: float = Form(...),
    min_amount: Optional[float] = Form(None),
    max_amount: Optional[float] = Form(None),
    fiat: str = Form("BRL"),
    asset: str = Form("USDT"),
    external_id: Optional[str] = Form(None),
):
    ad_id = create_ad(
        title=title,
        trade_type=trade_type.upper(),
        price=price,
        min_amount=min_amount,
        max_amount=max_amount,
        fiat=fiat.upper(),
        asset=asset.upper(),
        external_id=external_id,
    )
    return RedirectResponse(url="/", status_code=303)


@app.get("/ads/{ad_id}", response_class=HTMLResponse)
def edit_ad_form(request: Request, ad_id: int):
    ad = get_ad(ad_id)
    if not ad:
        raise HTTPException(404)
    return templates.TemplateResponse("edit.html", {"request": request, "ad": ad})


@app.post("/ads/{ad_id}")
def edit_ad_post(
    ad_id: int,
    title: str = Form(...),
    price: float = Form(...),
    min_amount: Optional[float] = Form(None),
    max_amount: Optional[float] = Form(None),
):
    update_ad_fields(ad_id, title=title, price=price, min_amount=min_amount, max_amount=max_amount)
    return RedirectResponse(url="/", status_code=303)


@app.post("/ads/{ad_id}/toggle")
def toggle_ad(ad_id: int):
    ad = get_ad(ad_id)
    if not ad:
        raise HTTPException(404)
    toggle_ad_status(ad_id)
    return RedirectResponse(url="/", status_code=303)


@app.post("/ads/{ad_id}/push")
def push_ad(ad_id: int):
    ad = get_ad(ad_id)
    if not ad:
        raise HTTPException(404)
    provider = get_provider()
    update = AdUpdate(
        price=ad["price"],
        min_amount=ad["min_amount"],
        max_amount=ad["max_amount"],
        status=ad["status"],
    )
    provider.push_update(ad.get("external_id"), update)
    return RedirectResponse(url="/", status_code=303)


@app.post("/bulk/update")
def bulk_update(multiplier: float = Form(...)):
    provider = get_provider()
    ads = list_ads()
    for ad in ads:
        new_price = round(ad["price"] * multiplier, 2)
        update_ad_fields(ad["id"], price=new_price)
        update = AdUpdate(price=new_price)
        provider.push_update(ad.get("external_id"), update)
    return RedirectResponse(url="/", status_code=303)
