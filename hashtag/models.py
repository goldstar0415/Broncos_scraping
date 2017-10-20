import uuid
import sqlalchemy as sql
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.declarative import declarative_base

from hashtag import settings


Base = declarative_base()


class Proxy(Base):
    __tablename__ = settings.PROXY_TABLENAME

    guid = sql.Column(postgresql.UUID(as_uuid=True),
                      default=uuid.uuid1,
                      primary_key=True)
    url = sql.Column(sql.String(1024))
    expires = sql.Column(sql.DateTime(timezone=True))
    is_active = sql.Column(sql.Boolean)
    is_banned = sql.Column(sql.Boolean)

    def __repr__(self):
        return "Proxy({}): {} (expires {})".format(
            'enabled' if self.is_active else 'disabled',
            self.url,
            self.expires
        )


class Account(Base):
    __tablename__ = settings.ACCOUNT_TABLENAME

    guid = sql.Column(postgresql.UUID(as_uuid=True),
                      default=uuid.uuid1,
                      primary_key=True)
    token = sql.Column(sql.String(400))
    login = sql.Column(sql.String(100))
    password = sql.Column(sql.String(100))
    refresh_time = sql.Column(sql.DateTime(timezone=True))
    network_id = sql.Column(
        postgresql.UUID(as_uuid=True),
        sql.ForeignKey("{}.guid".format(settings.NETWORK_TABLENAME)))
    is_limited = sql.Column(sql.Boolean)
    is_active = sql.Column(sql.Boolean)

    def __repr__(self):
        return "{}: {}".format(
            self.network.name,
            self.login
        )


class HashTag(Base):
    __tablename__ = settings.HASHTAG_TABLENAME

    guid = sql.Column(postgresql.UUID(as_uuid=True),
                      default=uuid.uuid1,
                      primary_key=True)
    tag = sql.Column(sql.String(40))
    user_id = sql.Column(
        sql.Integer,
        sql.ForeignKey("{}.id".format(settings.USER_TABLENAME)))
    networks = sql.orm.relationship(
        "Network",
        secondary=settings.HASHTAG_NETWORK_TABLENAME,
        back_populates="hashtags",
        lazy='dynamic')
    is_active = sql.Column(sql.Boolean)

    def __repr__(self):
        return self.tag


class Network(Base):
    __tablename__ = settings.NETWORK_TABLENAME


    guid = sql.Column(postgresql.UUID(as_uuid=True),
                      default=uuid.uuid1,
                      primary_key=True)
    name = sql.Column(sql.String(50))
    parsing_frequency = sql.Column(sql.Integer)
    icon_pic = sql.Column(sql.String(100))

    accounts = sql.orm.relationship("Account", backref="network", lazy='dynamic')
    hashtags = sql.orm.relationship(
        "HashTag",
        secondary=settings.HASHTAG_NETWORK_TABLENAME,
        back_populates="networks",
        lazy='dynamic')

    def __repr__(self):
        return self.name


class HashTagNetwork(Base):
    __tablename__ = settings.HASHTAG_NETWORK_TABLENAME
    id = sql.Column(sql.Integer, primary_key=True)
    last_scraped = sql.Column(sql.DateTime(timezone=True))
    hashtag_id = sql.Column(
        postgresql.UUID(as_uuid=True),
        sql.ForeignKey('{}.guid'.format(settings.HASHTAG_TABLENAME)))
    network_id = sql.Column(
        postgresql.UUID(as_uuid=True),
        sql.ForeignKey('{}.guid'.format(settings.NETWORK_TABLENAME)))
    hashtag = sql.orm.relationship(HashTag, backref='network_assoc')
    network = sql.orm.relationship(Network, backref='hashtag_assoc')


class User(Base):
    """
    A hashtag is created by standard Django user. For *developing* purposes,
    this mocking User class is provided.
    """

    __tablename__ = settings.USER_TABLENAME

    id = sql.Column(sql.Integer, primary_key=True)


if __name__ == '__main__':
    # Should not be executed until you develop locally
    # coz. these tables are to be created by Django
    engine = sql.create_engine(settings.DB_URL)
    Base.metadata.create_all(engine)
