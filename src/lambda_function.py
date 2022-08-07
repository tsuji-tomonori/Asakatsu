from __future__ import annotations
import base64

import json
from typing import Any, NamedTuple
import logging
import uuid
import os

import cv2
import numpy as np


logger = logging.getLogger(__name__)
logger.setLevel("INFO")


def init_card(year: int, month: int) -> np.ndarray:
    card_img = cv2.imread(f"card_{year}_{str(month).zfill(2)}.png")
    card_img = card_img.astype(np.float64)
    return card_img


def init_nyan() -> tuple[np.ndarray, np.ndarray]:
    nyan_img = cv2.imread("nyan.png", cv2.IMREAD_UNCHANGED)
    mask = nyan_img[:,:,3]
    mask = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
    mask = mask / 255
    nyan_img = nyan_img[:,:,:3]
    return nyan_img, mask


def read_position(year: int, month: int) -> dict[str, dict[str, int]]:
    with open(f"position_{year}_{str(month).zfill(2)}.json") as f:
        return json.load(f)


def update_card(nyan_img: np.ndarray, mask: np.ndarray, card_img: np.ndarray, dx: int, dy: int) -> None:
    h, w = nyan_img.shape[:2]
    card_img[dy:dy+h, dx:dx+w] *= 1 - mask
    card_img[dy:dy+h, dx:dx+w] += nyan_img * mask


class Stamp(NamedTuple):
    year: int
    month: int
    days: list[int]

    @classmethod
    def of(cls, event: dict[str, Any]) -> Stamp:
        if not event.get("queryStringParameters"):
            raise Exception("queryStringParameters in not exist")
        try:
            year = int(event["queryStringParameters"]["year"])
            month = int(event["queryStringParameters"]["month"])
            days = [int(day) for day in event["queryStringParameters"]["days"].split(",")]
        except Exception as e:
            raise Exception("InvalidParamater") from e
        return Stamp(
            year=year,
            month=month,
            days=days,
        )

    def write(self) -> None:
        card = init_card(self.year, self.month)
        nyan, mask = init_nyan()
        position = read_position(self.year, self.month)
        for day in self.days:
            update_card(
                nyan_img=nyan,
                mask=mask,
                card_img=card,
                dx=position[str(day)]["dx"],
                dy=position[str(day)]["dy"],
            )
        file_name = f"/tmp/{str(uuid.uuid4()).replace('-', '')}.png"
        cv2.imwrite(file_name, card)
        return file_name


def lambda_handler(event, context):
    try:
        stamp = Stamp.of(event)
        file_name = stamp.write()
        with open(file_name, "rb") as f:
            img = f.read()
        os.remove(file_name)
        return {
            'headers': {
                "Content-Type": "image/png",
                "Access-Control-Allow-Origin": "*"
            },
            'statusCode': 200,
            'body': base64.b64encode(img).decode('utf-8'),
            'isBase64Encoded': True
        }
    except:
        logger.exception("[NotRetryError]")
        return {
            'headers': { "Content-type": "text/html" },
            'statusCode': 400,
            'body': "<h1>ERROR</h1>",
        }
