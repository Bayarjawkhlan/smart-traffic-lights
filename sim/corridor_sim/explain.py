from __future__ import annotations

import json
import os

from dotenv import load_dotenv

from . import config

load_dotenv(config.ROOT / ".env.local")

INSTRUCTIONS = {
    "en": (
        "You explain an AI traffic-signal demo in Ulaanbaatar to a non-expert audience. "
        "Given the live state of one Signal Site, explain in 3-5 short sentences what the lights are doing now and why: "
        "which Phase is green, which Approaches and Crosswalks are waiting and for how long, whether the Safety Guard "
        "overrode the Controller and which rule forced it. Neighbour state is context only and is not used in the decision; "
        "never say the Controller reads or coordinates with Neighbours. "
        "Use only the numbers given. Do not invent data. Plain language, no markdown."
    ),
    "mn": (
        "Та Улаанбаатарын AI гэрлэн дохионы демог энгийн хүнд тайлбарладаг. "
        "Нэг уулзварын одоогийн төлөвийг ашиглан гэрэл яг одоо юу хийж байгаа, яагаад гэдгийг 3-5 богино өгүүлбэрээр тайлбарла: "
        "аль чиглэл ногоон, аль чиглэл болон явган хүний гарц хэдэн секунд хүлээж байна, Аюулгүй байдлын хамгаалагч "
        "AI-н шийдвэрийг өөрчилсөн эсэх, аль дүрмээр өөрчилсөн. Хөрш уулзваруудын төлөв нь зөвхөн нөхцөл байдлын мэдээлэл бөгөөд "
        "шийдвэрт ашиглагддаггүй; удирдлага хөрш уулзвараа хардаг эсвэл тэдэнтэй уялддаг гэж бүү хэл. "
        "Зөвхөн өгөгдсөн тоог ашигла. Энгийн хэлээр, markdown бүү ашигла."
    ),
}


def available() -> bool:
    return bool(os.environ.get("OPENAI_API_KEY"))


def explain(context: dict, language: str) -> str:
    from openai import OpenAI

    client = OpenAI()
    response = client.responses.create(
        model=os.environ.get("OPENAI_MODEL", "gpt-5.4-mini"),
        instructions=INSTRUCTIONS.get(language, INSTRUCTIONS["en"]),
        input=json.dumps(context, ensure_ascii=False),
    )
    return response.output_text.strip()
