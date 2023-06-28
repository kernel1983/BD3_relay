
import rocksdb

db_conn = rocksdb.DB('test.db', rocksdb.Options(create_if_missing=True))
