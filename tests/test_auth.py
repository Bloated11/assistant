import pytest
from datetime import datetime, timedelta
from jose import jwt
from web.auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user,
    SECRET_KEY,
    ALGORITHM
)
from web.database import Base, User, SessionLocal, engine
import hashlib

@pytest.fixture(scope="function")
def test_db():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    test_engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=test_engine)
    TestSessionLocal = sessionmaker(bind=test_engine)
    db = TestSessionLocal()
    
    test_user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("testpass123"),
        created_at=datetime.utcnow()
    )
    db.add(test_user)
    db.commit()
    
    yield db
    
    db.close()
    Base.metadata.drop_all(bind=test_engine)

@pytest.mark.auth
@pytest.mark.unit
class TestPasswordHashing:
    def test_password_hash_generation(self):
        password = "my_secure_password"
        hashed = get_password_hash(password)
        
        assert hashed is not None
        assert len(hashed) == 64
        assert hashed == hashlib.sha256(password.encode()).hexdigest()
    
    def test_different_passwords_different_hashes(self):
        hash1 = get_password_hash("password1")
        hash2 = get_password_hash("password2")
        
        assert hash1 != hash2
    
    def test_same_password_same_hash(self):
        password = "consistent_password"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        assert hash1 == hash2

@pytest.mark.auth
@pytest.mark.integration
class TestAuthentication:
    def test_verify_password_success(self, test_db, monkeypatch):
        def mock_get_db():
            yield test_db
        
        import web.auth
        monkeypatch.setattr(web.auth, "get_db", mock_get_db)
        
        user_data = verify_password("testuser", "testpass123")
        
        assert user_data is not None
        assert user_data["username"] == "testuser"
        assert user_data["email"] == "test@example.com"
        assert "id" in user_data
    
    def test_verify_password_wrong_password(self, test_db, monkeypatch):
        def mock_get_db():
            yield test_db
        
        import web.auth
        monkeypatch.setattr(web.auth, "get_db", mock_get_db)
        
        user_data = verify_password("testuser", "wrongpassword")
        
        assert user_data is None
    
    def test_verify_password_nonexistent_user(self, test_db, monkeypatch):
        def mock_get_db():
            yield test_db
        
        import web.auth
        monkeypatch.setattr(web.auth, "get_db", mock_get_db)
        
        user_data = verify_password("nonexistent", "anypassword")
        
        assert user_data is None
    
    def test_verify_password_empty_credentials(self, test_db, monkeypatch):
        def mock_get_db():
            yield test_db
        
        import web.auth
        monkeypatch.setattr(web.auth, "get_db", mock_get_db)
        
        assert verify_password("", "") is None
        assert verify_password("testuser", "") is None
        assert verify_password("", "testpass123") is None

@pytest.mark.auth
@pytest.mark.unit
class TestJWTTokens:
    def test_create_access_token(self):
        data = {"sub": "testuser"}
        token = create_access_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_token_contains_expiration(self):
        data = {"sub": "testuser"}
        token = create_access_token(data)
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert "exp" in payload
        assert "sub" in payload
        assert payload["sub"] == "testuser"
    
    def test_token_expiration_time(self):
        from web.auth import ACCESS_TOKEN_EXPIRE_MINUTES
        
        now = datetime.utcnow()
        data = {"sub": "testuser"}
        token = create_access_token(data)
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        exp_time = datetime.utcfromtimestamp(payload["exp"])
        
        time_diff = (exp_time - now).total_seconds()
        expected_seconds = ACCESS_TOKEN_EXPIRE_MINUTES * 60
        
        assert abs(time_diff - expected_seconds) <= 5
    
    def test_decode_valid_token(self, test_db, monkeypatch):
        def mock_get_db():
            yield test_db
        
        import web.auth
        monkeypatch.setattr(web.auth, "get_db", mock_get_db)
        
        token = create_access_token({"sub": "testuser"})
        user = get_current_user(token)
        
        assert user is not None
        assert user["username"] == "testuser"
    
    def test_decode_invalid_token(self):
        user = get_current_user("invalid_token_string")
        
        assert user is None
    
    def test_decode_expired_token(self):
        data = {"sub": "testuser"}
        to_encode = data.copy()
        expire = datetime.utcnow() - timedelta(minutes=10)
        to_encode.update({"exp": expire})
        expired_token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        
        user = get_current_user(expired_token)
        
        assert user is None
    
    def test_no_token_provided(self):
        user = get_current_user(None)
        
        assert user is None

@pytest.mark.auth
@pytest.mark.unit
class TestTokenSecurity:
    def test_token_cannot_be_decoded_without_secret(self):
        token = create_access_token({"sub": "testuser"})
        
        with pytest.raises(Exception):
            jwt.decode(token, "wrong_secret_key", algorithms=[ALGORITHM])
    
    def test_token_algorithm_verification(self):
        token = create_access_token({"sub": "testuser"})
        
        with pytest.raises(Exception):
            jwt.decode(token, SECRET_KEY, algorithms=["HS512"])
