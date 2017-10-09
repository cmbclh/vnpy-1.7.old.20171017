##-*-coding: utf-8;-*-##
import contextlib
import sqlalchemy
from sqlalchemy.orm import sessionmaker

class DBConnector():
    metadata = None
    engin=None
    __session_maker=None
    def __init__(self,param):
        __C=param
        __url = 'mysql+mysqlconnector://{}:{}@{}:{}/{}?charset={}'.format(
            __C.get('database.username'),
            __C.get('database.password'),
            __C.get('database.host'),
            __C.get('database.port'),
            __C.get('database.database'),
            __C.get('database.charset', 'utf8')
        )
        __echo = __C.get('database.echo', __C.get('app.debug', False))
        __pool_size = __C.get('database.pool_size', 10)
        __pool_recycle = __C.get('database.pool_recycle', 3600)
        self.engine = sqlalchemy.create_engine(__url, pool_size=__pool_size, pool_recycle=__pool_recycle,
                                          echo=__echo)
        self.__session_maker = sessionmaker(bind=self.engine, expire_on_commit=False)
        self.metadata = sqlalchemy.MetaData(self.engine)

    @contextlib.contextmanager
    def session(self):
        s = self.__session_maker()
        try:
            yield s
            s.commit()
        except Exception:
            s.rollback()
            raise
        finally:
            s.close()


