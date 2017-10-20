import sqlalchemy as sa

from hashtag.models import *
from hashtag.settings import DB_URL
from hashtag.contexts import session_scope


def make_account(network):
    return Account(
        token='',
        network_id=network.guid,
        is_limited=False,
        is_active=True
    )

def make_network():
    return Network(
        name='twitter',
        parsing_frequency=300,
    )


if __name__ == '__main__':
    engine = sa.create_engine(DB_URL)
    Session = sa.orm.sessionmaker(engine)

    with session_scope(Session) as session:
        user = User(id=1)
        session.add(user)

        net = make_network()
        session.add(net)

        account = make_account(net)
        session.add(account)

        tag = HashTag(
            tag='#GameOfThrones',
            user_id=user.id,
            network_id=net.guid,
            is_active=True
        )
        session.add(tag)

        session.commit()

    print('Done!')
