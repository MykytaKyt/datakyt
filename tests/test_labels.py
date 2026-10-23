import io

import pytest
from PIL import Image

from datakyt import labels
from datakyt.api.routers.items import parse_ids
from datakyt.services.errors import InvalidInputError


def test_qr_payload():
    assert labels.qr_payload("equipment", "EQ-00001") == "datakyt://equipment/EQ-00001"


def test_label_png_dimensions():
    data = labels.label_png(labels.LabelData("furniture", "FU-1", "Desk " * 40))
    image = Image.open(io.BytesIO(data))
    assert image.size == labels.LABEL_SIZE
    assert image.info["dpi"] == pytest.approx((labels.DPI, labels.DPI), abs=0.01)


def test_long_inventory_number_shrinks_font():
    image = labels.render_label(labels.LabelData("equipment", "X" * 32, "Name"))
    assert image.size == labels.LABEL_SIZE


def test_wrap_truncates_with_ellipsis():
    image = Image.new("RGB", (10, 10))
    from PIL import ImageDraw

    draw = ImageDraw.Draw(image)
    lines = labels._wrap(draw, "word " * 100, labels._font(40), 300, max_lines=2)
    assert len(lines) == 2
    assert lines[-1].endswith("…")


def test_pdf_sheet_pages():
    items = [labels.LabelData("equipment", f"EQ-{i}", "Laptop") for i in range(25)]
    pdf = labels.label_sheet_pdf(items)
    assert pdf.startswith(b"%PDF")
    assert pdf.count(b"/Type /Page\n") == 2


def test_label_endpoints(client, factory):
    item = factory.equipment()
    desk = factory.furniture()
    png = client.get(f"/equipment/{item.id}/label.png")
    assert png.status_code == 200
    assert png.headers["content-type"] == "image/png"
    assert client.get(f"/furniture/{desk.id}/label.png").status_code == 200
    assert client.get("/equipment/999999/label.png").status_code == 404

    pdf = client.get("/labels.pdf", params={"ids": f"{item.id}"})
    assert pdf.headers["content-type"] == "application/pdf"
    assert pdf.content.startswith(b"%PDF")
    furniture_pdf = client.get("/labels.pdf", params={"ids": str(desk.id), "kind": "furniture"})
    assert furniture_pdf.status_code == 200
    missing = client.get("/labels.pdf", params={"ids": f"{item.id},999999"})
    assert missing.status_code == 422
    assert "999999" in missing.json()["detail"]


def test_parse_ids():
    assert parse_ids("1, 2,3,") == [1, 2, 3]
    for bad in ("", "a,b", ",".join(["1"] * 481)):
        with pytest.raises(InvalidInputError):
            parse_ids(bad)
