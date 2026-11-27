from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse

from app.config import AUTHOR
from app.facebook import get_profile_pic, get_public_uid

app = FastAPI(title="R1K4-FB-USER-HANDER")


@app.get("/find-uid")
async def find_uid(id: str):
    uid = get_public_uid(id)

    if uid:
        return [
            {
                "info": {
                    "status": "success",
                    "username": id,
                    "UID": uid
                }
            },
            {
                "author": AUTHOR
            }
        ]
    else:
        raise HTTPException(status_code=404, detail="Could not find UID. The profile might be private or restricted.")


@app.get("/profile-pic")
async def profile_pic(id: str, go: int = 0):
    uid = id if id.isdigit() else get_public_uid(id)

    if not uid:
        raise HTTPException(status_code=404, detail="Could not find UID. The profile might be private or restricted.")

    pic = get_profile_pic(uid)

    if not pic:
        raise HTTPException(status_code=404, detail="Could not fetch profile picture.")

    if go == 1:
        return RedirectResponse(pic)

    return [
        {
            "info": {
                "status": "success",
                "username": id,
                "UID": uid,
                "picture": pic
            }
        },
        {
            "author": AUTHOR
        }
    ]
