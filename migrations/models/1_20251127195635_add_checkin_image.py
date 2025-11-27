from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "checkins" ADD "image_base64" TEXT;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "checkins" DROP COLUMN "image_base64";"""


MODELS_STATE = (
    "eJztme9P4jAYx/8Vsldn4hlEEO7eAaJyKlwU74zGLGUro3FrsetUYvjfry37WcaOGSRg9m"
    "48fZ6tz6c/nm/Lu+YQE9ruQXsMjacu1n6W3jUMHMgf1Kb9kgYmk6hBGBgY2tLXEE4ISyMY"
    "uowCg3H7CNgu5CYTugZFE4aI+AT2bFsYicEdEbYik4fRswd1RizIxpDyhodHbkbYhG/QDX"
    "5OnvQRgraZ6C0yxbelXWfTibR1MTuVjuJrQ90gtufgyHkyZWOCQ2+EmbBaEEMKGBSvZ9QT"
    "3Re98zMNMpr3NHKZdzEWY8IR8GwWS3dFBgbBgh/vjSsTtMRXvlcOq/Vq4+i42uAusiehpT"
    "6bpxflPg+UBHoDbSbbAQNzD4kx4sYb4CK5E25lyIHp+IIYBaDpBx0EDyrOAF4Wz8AQAY0m"
    "0ZqIUgjMPran/mBl4Bt0rzo3g+bVb5GJ47rPtoTTHHRES0Vap4r12/GesBO+BOZrI3xJ6W"
    "93cF4SP0v3/V5HEiQus6j8YuQ3uNdEn4DHiI7Jqw7M2LwKrAEY7hkNJoUTQpnO4BtbHNMB"
    "t6aPpxKmDCtnt50DmTVwnbtBYsx6f5rX7fPm9ber5t1eYtwu+72zwD0atF77st+SSye2xT"
    "jAgvoQuPC4mgevGvchvv7wf2G8AOkjCM0hMJ7y0FXCCripcC0CbD1XjYxF/L9QbseGsI5a"
    "KQTG6Cm1VAoiiwBPCYXIwhdwKjl2eY8ANtLqoy+ozvzXbB+/WTAHAmu0NCh4DUVXfGrw9H"
    "hSkMkE282bdvOko0mIYkG+AmrqCZqihVSIYgl9F5uciqNaAOb7qelnIfocB5uiYAPgy+Wr"
    "SKjQrjunXRlidop4bY8BTWcXBuyKxOGT/U23IbbYWGCr1TJ4BVWCeykKNCgglXlbsjLEe5"
    "aj7CphRdktJOPm8fJSyzw3zw4QRWxuC9B4QUEvct9ZyzZQK6+wC9TKSzcB0ZTkaPAjMc9Z"
    "BynHxuyrgGRkcSGwZRcCngtpPtkfiyhkf8hwDbL/1n/N9vFbVfbHpkZe2R/bamI3xUmiLT"
    "/y9OIa2mCJsFi8lN4dnrPPPPzI6ZVy+Amm3fLDjxjW4vCze4cfvv4sCpzU7b2FrKUMlcD1"
    "7PIbovmjUjk6qlfKR8eNWrVerzXKIdbFpiy+re6ZQJyoywHz5NYvn3MozHjMjsj2DZwyR4"
    "i6TM/LMhlV0Cz0uvb19PqC9FxFRoU3lh/XULt3D/2pAqoJKTLGaRLKb8kUUSDyKVTUDqmo"
    "F659U28+lxelWEhxjRz9e8uXRg6IvvtuAjwsr3IDx72WApRtSk0nmEGcUtB/3fR7S4p5FK"
    "KAvMU8wQcTGWy/ZCOXPW4n1gyKIuvs+2L1alipxuIFrbSbnU3+OTn7B0vZlz4="
)
