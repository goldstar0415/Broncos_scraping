from sqlalchemy import or_
from hashtag.models import Account, Network
from hashtag.shortcuts import unow_tz


def get_fresh_account(session, _type):
    return (
        session.query(Account).
        join(Network).
        filter(Account.is_active==True).
        filter(or_(
            Account.refresh_time<unow_tz(),
            Account.refresh_time==None
        )).
        filter(Network.name==_type).
        first()
    )
