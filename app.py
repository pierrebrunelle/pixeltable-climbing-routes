"""Climbing Route Topo Registry API built with Pixeltable.

Upload a route topo photo with crag, grade and style. Pixeltable stores the image,
derives a thumbnail and grayscale copy as media computed columns, and tags aspect,
dominant color and a combined topo label via UDFs. B-tree indexes on crag, grade and
style back the lookup queries the API exposes.

Layout: UDFs live in udfs.py; this file holds table models, @pxt.query functions and routes.

Run locally:
    pxt schema update app.py climbing
    pxt service run app.py climbing
"""
import pixeltable as pxt
import pixeltable.functions as pxtf
from pixeltable.serving import FastAPIRouter

from udfs import aspect_band, dominant_channel, grade_band, topo_tag

# ---- tables ----
TableModel = pxt.model_base()


class Routes(TableModel, name='routes', has_default_idxs=False):
    route_id = pxt.Column(value=pxtf.uuid.uuid7(), primary_key=True)
    name: pxt.String
    crag: pxt.String
    grade: pxt.String  # e.g. 5.10a
    style: pxt.String  # sport / trad / boulder / alpine
    bolts: pxt.Int | None
    length_m: pxt.Float | None
    topo: pxt.Image

    # generated media
    thumb = topo.resize((96, 128))
    gray = topo.convert('L')

    # UDF chain
    aspect = aspect_band(topo)
    channel = dominant_channel(topo)
    band = grade_band(grade)
    tag = topo_tag(aspect, channel, style)

    __indexes__ = [
        pxt.BtreeIndex(crag),
        pxt.BtreeIndex(grade),
        pxt.BtreeIndex(style),
        pxt.BtreeIndex(band),
    ]


# ---- queries ----
@pxt.query
def by_crag(crag: str):
    """Routes at one crag (crag index), hardest grade first."""
    return (
        Routes.where(Routes.crag == crag)
        .select(Routes.route_id, Routes.name, Routes.grade, Routes.style, Routes.tag, Routes.band)
        .order_by(Routes.grade, asc=False)
    )


@pxt.query
def by_grade_band(band: str, style: str):
    """Routes in a grade band and style (band + style indexes)."""
    return (
        Routes.where((Routes.band == band) & (Routes.style == style))
        .select(Routes.route_id, Routes.name, Routes.crag, Routes.grade, Routes.tag)
        .order_by(Routes.name)
    )


@pxt.query
def route_thumb(name: str):
    """Thumbnail for a route name (served as an image file)."""
    return (
        Routes.where(Routes.name == name)
        .order_by(Routes.route_id, asc=False)
        .limit(1)
        .select(Routes.thumb)
    )


@pxt.query
def route_detail(name: str):
    """One route's metadata and media tags."""
    return Routes.where(Routes.name == name).select(
        Routes.route_id, Routes.name, Routes.crag, Routes.grade, Routes.style,
        Routes.bolts, Routes.length_m, Routes.aspect, Routes.channel, Routes.band, Routes.tag,
    )


# ---- routes ----
climbing_api = FastAPIRouter(name='climbing_api')

climbing_api.add_insert_route(
    Routes,
    path='/routes',
    inputs=[Routes.name, Routes.crag, Routes.grade, Routes.style, Routes.bolts, Routes.length_m],
    uploadfile_inputs=[Routes.topo],
    outputs=[Routes.route_id, Routes.aspect, Routes.channel, Routes.band, Routes.tag],
)
climbing_api.add_compute_route(
    Routes,
    path='/analyze',
    inputs=[Routes.grade, Routes.style],
    uploadfile_inputs=[Routes.topo],
    outputs=[Routes.aspect, Routes.channel, Routes.band, Routes.tag],
)
climbing_api.add_delete_route(Routes, path='/routes/delete')
climbing_api.add_query_route(path='/routes/by-crag', query=by_crag, method='get')
climbing_api.add_query_route(path='/routes/by-band', query=by_grade_band, method='get')
climbing_api.add_query_route(
    path='/routes/thumb', query=route_thumb, method='get', one_row=True, return_fileresponse=True
)
climbing_api.add_query_route(path='/routes/detail', query=route_detail, method='get', one_row=True)
