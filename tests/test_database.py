import pytest
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from web.database import User, Base, get_db, init_db

@pytest.fixture(scope="function")
def test_engine():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def test_session(test_engine):
    TestSessionLocal = sessionmaker(bind=test_engine)
    session = TestSessionLocal()
    yield session
    session.close()

@pytest.mark.db
@pytest.mark.unit
class TestUserModel:
    def test_create_user(self, test_session):
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed123"
        )
        test_session.add(user)
        test_session.commit()
        
        assert user.id is not None
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.created_at is not None
    
    def test_user_unique_username(self, test_session):
        user1 = User(username="testuser", email="test1@example.com", hashed_password="hash1")
        test_session.add(user1)
        test_session.commit()
        
        user2 = User(username="testuser", email="test2@example.com", hashed_password="hash2")
        test_session.add(user2)
        
        with pytest.raises(Exception):
            test_session.commit()
    
    def test_user_unique_email(self, test_session):
        user1 = User(username="user1", email="test@example.com", hashed_password="hash1")
        test_session.add(user1)
        test_session.commit()
        
        user2 = User(username="user2", email="test@example.com", hashed_password="hash2")
        test_session.add(user2)
        
        with pytest.raises(Exception):
            test_session.commit()
    
    def test_query_user_by_username(self, test_session):
        user = User(username="testuser", email="test@example.com", hashed_password="hash")
        test_session.add(user)
        test_session.commit()
        
        found = test_session.query(User).filter(User.username == "testuser").first()
        
        assert found is not None
        assert found.username == "testuser"
        assert found.email == "test@example.com"
    
    def test_query_user_by_email(self, test_session):
        user = User(username="testuser", email="test@example.com", hashed_password="hash")
        test_session.add(user)
        test_session.commit()
        
        found = test_session.query(User).filter(User.email == "test@example.com").first()
        
        assert found is not None
        assert found.username == "testuser"
    
    def test_update_user(self, test_session):
        user = User(username="testuser", email="test@example.com", hashed_password="hash")
        test_session.add(user)
        test_session.commit()
        
        user.email = "newemail@example.com"
        test_session.commit()
        
        updated = test_session.query(User).filter(User.username == "testuser").first()
        assert updated.email == "newemail@example.com"
    
    def test_delete_user(self, test_session):
        user = User(username="testuser", email="test@example.com", hashed_password="hash")
        test_session.add(user)
        test_session.commit()
        
        test_session.delete(user)
        test_session.commit()
        
        found = test_session.query(User).filter(User.username == "testuser").first()
        assert found is None
    
    def test_count_users(self, test_session):
        for i in range(5):
            user = User(username=f"user{i}", email=f"user{i}@test.com", hashed_password="hash")
            test_session.add(user)
        test_session.commit()
        
        count = test_session.query(User).count()
        assert count == 5
    
    def test_query_nonexistent_user(self, test_session):
        found = test_session.query(User).filter(User.username == "nonexistent").first()
        assert found is None

@pytest.mark.db
@pytest.mark.integration
class TestDatabaseOperations:
    def test_init_db(self, test_engine):
        Base.metadata.drop_all(bind=test_engine)
        Base.metadata.create_all(bind=test_engine)
        
        assert test_engine.dialect.has_table(test_engine.connect(), "users")
    
    def test_get_db_generator(self):
        db_gen = get_db()
        db = next(db_gen)
        
        assert db is not None
        
        try:
            next(db_gen)
        except StopIteration:
            pass
