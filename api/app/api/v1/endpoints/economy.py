from fastapi import APIRouter, Depends, HTTPException
from app.dependencies.auth import get_current_user
from app.service.economy import pull_gacha, donate_to_clan

router = APIRouter(tags=["economy"]) 


@router.post('/gacha/{loteria_id}/pull')
def post_pull_gacha(loteria_id: int, user=Depends(get_current_user)):
    user_id = int(user.get('id'))
    recompensa = pull_gacha(user_id, loteria_id)
    return {"ok": True, "recompensa": recompensa, "message": "Gacha realizada"}


@router.post('/clan/{clan_id}/donate')
def post_donate_clan(clan_id: int, data: dict, user=Depends(get_current_user)):
    # data expected: {"amount": 123}
    amount = data.get('amount')
    if amount is None:
        raise HTTPException(status_code=400, detail='Missing amount')
    try:
        amount_i = int(amount)
    except Exception:
        raise HTTPException(status_code=400, detail='Amount must be integer')
    if amount_i <= 0:
        raise HTTPException(status_code=400, detail='Amount must be > 0')
    kind = data.get('type', 'monedas')
    if kind not in ('monedas', 'puntos'):
        raise HTTPException(status_code=400, detail='Invalid donation type')
    user_id = int(user.get('id'))
    result = donate_to_clan(user_id, clan_id, amount_i, kind)
    if kind == 'monedas':
        return {"ok": True, "amount": amount_i, "type": kind, "message": f"Has donado {amount_i} monedas al clan", "monedas_actuales": result.get('monedas_actuales'), "tesoro_clan": result.get('tesoro_clan')}
    else:
        return {"ok": True, "amount": amount_i, "type": kind, "message": f"Has donado {amount_i} puntos al clan", "puntos_actuales": result.get('puntos_actuales'), "puntos_clan": result.get('puntos_clan')}
