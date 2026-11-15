"""Cloud Lab: educational + real-status pages. Public, read-only, never exposes secrets."""
from fastapi import APIRouter, Request

from app.db import query_all, query_one
from app.services import cloudinfo, mapreduce
from app.services.storage import image_url
from app.templating import render

router = APIRouter(prefix="/cloud", tags=["cloud lab"])


@router.get("")
def cloud_lab(request: Request):
    first = None
    try:
        first = query_one("SELECT id, name, price, stock, image_url FROM products ORDER BY id LIMIT 1")
        if first:
            first = {"id": first["id"], "name": first["name"], "price": float(first["price"]),
                     "stock": first["stock"], "image": image_url(first["image_url"])}
    except Exception:
        first = None
    return render(request, "cloud/lab.html", cards=cloudinfo.service_cards(request.headers),
                  status=cloudinfo.status_json(), sample_json=first, active="lab")


@router.get("/status")
def cloud_status():
    """JSON health/status. Contains no credentials, endpoints or instance IDs."""
    return cloudinfo.status_json()


@router.get("/syllabus")
def syllabus(request: Request):
    return render(request, "cloud/syllabus.html", active="syllabus")


@router.get("/mapreduce")
def mapreduce_demo(request: Request, source: str = "auto"):
    live = query_all("SELECT order_id, product_name AS product, quantity AS qty, unit_price FROM order_items")
    use_live = source == "live" or (source == "auto" and len(live) > 0)
    records = live if use_live else mapreduce.SAMPLE
    if source == "sample":
        records, use_live = mapreduce.SAMPLE, False
    result = mapreduce.run(records[:200])
    top = max([r["sales"] for r in result["reduced"]] or [1])
    return render(request, "cloud/mapreduce.html", r=result, live=use_live, top=top, n=len(records), active="mapreduce")


@router.get("/unit5")
def unit5(request: Request):
    return render(request, "cloud/unit5.html", active="unit5")
